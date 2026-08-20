# `os` lets us read the Gemini API key and model name from the .env file.
import os

# Google's official Gemini Python SDK.
from google import genai
from google.genai import types

# Loads variables written inside backend/.env.
from dotenv import load_dotenv


# Load environment variables before trying to read the API key.
load_dotenv()


# Read the private API key without writing it directly in the Python code.
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Read the model name from .env.
# The value after `or` is used only if GEMINI_MODEL is missing.
GEMINI_MODEL = os.getenv("GEMINI_MODEL") or "gemini-3.1-flash-lite"


# Stop the application with a clear error if the API key is missing.
if not GEMINI_API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY is missing. Add it to the backend/.env file."
    )


# Create one reusable Gemini client.
# We reuse it instead of creating a new client for every question.
gemini_client = genai.Client(api_key=GEMINI_API_KEY)


def generate_answer(question: str, sources: list[dict]) -> str:
    """
    Generate an answer using only the document chunks retrieved from Qdrant.

    `question` is the user's question.

    `sources` contains the most relevant PDF chunks returned by Qdrant.
    Each source contains information such as filename, page number and text.
    """

    # If Qdrant found no relevant chunks, Gemini should not invent an answer.
    if not sources:
        return (
            "I could not find enough information in the uploaded documents "
            "to answer this question."
        )

    # We will combine the retrieved chunks into one context string.
    context_sections = []

    for source_number, source in enumerate(sources, start=1):
        # Give every retrieved chunk a source number.
        # Gemini can use these numbers when citing its answer.
        source_section = (
            f"[Source {source_number}]\n"
            f"Filename: {source['filename']}\n"
            f"Page: {source['page_number']}\n"
            f"Text:\n{source['text']}"
        )

        context_sections.append(source_section)

    # Separate the source chunks so Gemini can distinguish between them.
    document_context = "\n\n".join(context_sections)

    # Combine the user's question with the retrieved PDF information.
    prompt = (
        f"Question:\n{question}\n\n"
        f"Retrieved document context:\n{document_context}"
    )

    # Send the question and retrieved context to Gemini.
    response = gemini_client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            # Tell Gemini exactly how it should behave.
            system_instruction=(
                "You are a document question-answering assistant. "
                "Answer using only the retrieved document context provided. "
                "Do not use outside knowledge or invent missing information. "
                "Cite supporting sources using labels such as [Source 1]. "
                "If the context does not contain enough information, clearly "
                "say that the answer could not be found in the documents."
            ),

            # A low temperature makes answers more consistent and factual.
            temperature=0.2,

            # Prevent unnecessarily long answers.
            max_output_tokens=500,
        ),
    )

    # Occasionally a model may return no text.
    # Return a safe message instead of crashing the API.
    if not response.text:
        return "Gemini did not return an answer."

    # Remove unnecessary whitespace before returning the final answer.
    return response.text.strip()