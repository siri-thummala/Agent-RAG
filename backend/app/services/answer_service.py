# `os` reads Gemini configuration from environment variables.
import os

# Google's Gemini Python SDK.
from google import genai
from google.genai import types

# Loads values written inside backend/.env.
from dotenv import load_dotenv


# Load environment variables.
load_dotenv()


# Read Gemini configuration from .env.
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = (
    os.getenv("GEMINI_MODEL")
    or "gemini-3.1-flash-lite"
)


if not GEMINI_API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY is missing. Add it to backend/.env."
    )


# Create one reusable Gemini client.
gemini_client = genai.Client(
    api_key=GEMINI_API_KEY,
)


def format_conversation_history(
    conversation_history: list[dict[str, str]] | None,
) -> str:
    """
    Convert saved conversation messages into readable prompt text.
    """

    if not conversation_history:
        return "No previous conversation."

    formatted_messages: list[str] = []

    # Use only the ten most recent messages.
    # This prevents conversation prompts from growing forever.
    for message in conversation_history[-10:]:
        role = message.get("role", "unknown").upper()
        content = message.get("content", "")

        formatted_messages.append(
            f"{role}: {content}"
        )

    return "\n".join(formatted_messages)


def generate_answer(
    question: str,
    sources: list[dict],
    conversation_history: list[dict[str, str]] | None = None,
) -> str:
    """
    Generate an answer using only Qdrant document chunks.
    """

    if not sources:
        return (
            "I could not find enough information in the uploaded "
            "documents to answer this question."
        )

    context_sections: list[str] = []

    for source_number, source in enumerate(
        sources,
        start=1,
    ):
        context_sections.append(
            f"[Source {source_number}]\n"
            f"Filename: {source['filename']}\n"
            f"Page: {source['page_number']}\n"
            f"Text:\n{source['text']}"
        )

    document_context = "\n\n".join(
        context_sections
    )

    history_context = format_conversation_history(
        conversation_history
    )

    prompt = (
        f"Previous conversation:\n"
        f"{history_context}\n\n"
        f"Current question:\n"
        f"{question}\n\n"
        f"Retrieved document context:\n"
        f"{document_context}"
    )

    response = gemini_client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=(
                "You are a document question-answering assistant. "
                "Use conversation history only to understand follow-up "
                "questions and references. Every factual claim must be "
                "supported by the retrieved document context. "
                "Cite sources using labels such as [Source 1]. "
                "Do not invent missing information."
            ),
            temperature=0.2,
            max_output_tokens=500,
        ),
    )

    if not response.text:
        return "Gemini did not return an answer."

    return response.text.strip()


def generate_agentic_answer(
    question: str,
    document_sources: list[dict] | None = None,
    web_sources: list[dict] | None = None,
    conversation_history: list[dict[str, str]] | None = None,
) -> str:
    """
    Generate an answer from document sources, web sources or both.
    """

    document_sources = document_sources or []
    web_sources = web_sources or []

    if not document_sources and not web_sources:
        return (
            "I could not find enough information in the uploaded "
            "documents or live web results to answer this question."
        )

    context_sections: list[str] = []

    # Format Qdrant document sources.
    for source_number, source in enumerate(
        document_sources,
        start=1,
    ):
        context_sections.append(
            f"[Document Source {source_number}]\n"
            f"Filename: {source['filename']}\n"
            f"Page: {source['page_number']}\n"
            f"Text:\n{source['text']}"
        )

    # Format live web sources.
    for source_number, source in enumerate(
        web_sources,
        start=1,
    ):
        context_sections.append(
            f"[Web Source {source_number}]\n"
            f"Title: {source['title']}\n"
            f"URL: {source['url']}\n"
            f"Snippet:\n{source['snippet']}"
        )

    combined_context = "\n\n".join(
        context_sections
    )

    history_context = format_conversation_history(
        conversation_history
    )

    prompt = (
        f"Previous conversation:\n"
        f"{history_context}\n\n"
        f"Current question:\n"
        f"{question}\n\n"
        f"Available source context:\n"
        f"{combined_context}"
    )

    response = gemini_client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=(
                "You are a grounded research assistant. "
                "Use conversation history only to understand follow-up "
                "questions and references. Every factual claim must be "
                "supported by the provided source context. "
                "Cite document evidence as [Document Source 1] and "
                "web evidence as [Web Source 1]. "
                "Do not invent facts, URLs or citations."
            ),
            temperature=0.2,
            max_output_tokens=700,
        ),
    )

    if not response.text:
        return "Gemini did not return an answer."

    return response.text.strip()