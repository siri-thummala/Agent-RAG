# Regular expressions help us extract complete words from a question.
import re

# Shared LangGraph state structure.
from app.graph.state import RAGState

# Converts a question into a 384-number embedding.
from app.services.embedding_service import embed_query

# Searches Qdrant for similar PDF chunks.
from app.services.qdrant_service import search_document_chunks

# Generates document, web and combined answers with Gemini.
from app.services.answer_service import (
    generate_agentic_answer,
    generate_answer,
)

# Performs free live web searches.
from app.services.web_search_service import search_web


# Words indicating that the user probably needs current information.
LIVE_INFORMATION_WORDS = {
    "latest",
    "current",
    "today",
    "recent",
    "recently",
    "news",
    "now",
    "updated",
    "update",
    "2026",
}


# Words indicating that the user wants to compare information.
COMPARISON_WORDS = {
    "compare",
    "comparison",
    "difference",
    "versus",
    "vs",
}


# Minimum similarity score considered a useful document match.
DOCUMENT_RELEVANCE_THRESHOLD = 0.55


def embed_question_node(state: RAGState) -> dict:
    """
    Convert the current question into an embedding vector.
    """

    # Read the current question from LangGraph state.
    question = state["question"]

    # Use the existing FastEmbed service.
    query_vector = embed_query(question)

    # Add the vector to the shared graph state.
    return {
        "query_vector": query_vector,
    }


def retrieve_documents_node(state: RAGState) -> dict:
    """
    Search Qdrant for PDF chunks similar to the question.
    """

    # This vector was created by embed_question_node.
    query_vector = state["query_vector"]

    # None means search across every uploaded PDF.
    document_id = state.get("document_id")

    # Retrieve the five most relevant chunks.
    document_sources = search_document_chunks(
        query_vector=query_vector,
        document_id=document_id,
        limit=5,
    )

    # Add the retrieved chunks to the graph state.
    return {
        "document_sources": document_sources,
    }


def route_question_node(state: RAGState) -> dict:
    """
    Decide whether to use documents, the live web or both.
    """

    question = state["question"].lower()
    document_id = state.get("document_id")
    document_sources = state.get(
        "document_sources",
        [],
    )

    # Extract complete words from the question.
    #
    # This avoids accidentally detecting "now" inside another
    # word such as "knowledge".
    question_words = set(
        re.findall(r"\b[\w-]+\b", question)
    )

    # Determine whether current information is requested.
    needs_live_information = bool(
        question_words.intersection(
            LIVE_INFORMATION_WORDS
        )
    )

    # Determine whether a comparison is requested.
    needs_comparison = bool(
        question_words.intersection(
            COMPARISON_WORDS
        )
    )

    # A comparison involving current information should use
    # both PDF chunks and live web results.
    if (
        needs_live_information
        and needs_comparison
        and document_sources
    ):
        return {
            "route": "both",
        }

    # If the user selected one PDF, respect that selection
    # and answer only from that document.
    if document_id is not None:
        return {
            "route": "document",
        }

    # Current-information questions should use live search.
    if needs_live_information:
        return {
            "route": "web",
        }

    # If Qdrant found nothing, fall back to live search.
    if not document_sources:
        return {
            "route": "web",
        }

    # Qdrant returns the strongest result first.
    highest_score = float(
        document_sources[0].get(
            "score",
            0.0,
        )
    )

    # Use documents when the best match is sufficiently relevant.
    if highest_score >= DOCUMENT_RELEVANCE_THRESHOLD:
        return {
            "route": "document",
        }

    # Weak document matches fall back to live web search.
    return {
        "route": "web",
    }


def web_search_node(state: RAGState) -> dict:
    """
    Search the live web using the current question.
    """

    question = state["question"]

    # Retrieve up to five live search results.
    web_sources = search_web(
        query=question,
        max_results=5,
    )

    # Add the results to the graph state.
    return {
        "web_sources": web_sources,
    }


def generate_document_answer_node(
    state: RAGState,
) -> dict:
    """
    Generate a PDF answer and save it in conversation memory.
    """

    question = state["question"]

    document_sources = state.get(
        "document_sources",
        [],
    )

    # This contains previous messages plus the current user question.
    conversation_history = state.get(
        "conversation_history",
        [],
    )

    # Remove the current question from the history passed to Gemini.
    # The question is already supplied separately.
    previous_history = conversation_history[:-1]

    # Generate the document-grounded answer.
    answer = generate_answer(
        question=question,
        sources=document_sources,
        conversation_history=previous_history,
    )

    # Save the answer and append it as an assistant message.
    return {
        "answer": answer,
        "conversation_history": [
            {
                "role": "assistant",
                "content": answer,
            }
        ],
    }


def generate_routed_answer_node(
    state: RAGState,
) -> dict:
    """
    Generate a web or combined answer and save it in memory.
    """

    question = state["question"]
    route = state["route"]

    document_sources = state.get(
        "document_sources",
        [],
    )

    web_sources = state.get(
        "web_sources",
        [],
    )

    conversation_history = state.get(
        "conversation_history",
        [],
    )

    # Remove the current question because it is passed separately.
    previous_history = conversation_history[:-1]

    # A web-only route must not use PDF chunks, even though
    # document retrieval ran before the routing decision.
    if route == "web":
        document_sources = []

    # For the "both" route, retain PDF and web sources.
    answer = generate_agentic_answer(
        question=question,
        document_sources=document_sources,
        web_sources=web_sources,
        conversation_history=previous_history,
    )

    # Save the answer and append it to conversation memory.
    return {
        "answer": answer,
        "conversation_history": [
            {
                "role": "assistant",
                "content": answer,
            }
        ],
    }