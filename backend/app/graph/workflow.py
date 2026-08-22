# LangGraph tools for building workflows.
from langgraph.graph import END, START, StateGraph

# Shared graph state.
from app.graph.state import RAGState

# Workflow node functions.
from app.graph.nodes import (
    embed_question_node,
    generate_document_answer_node,
    generate_routed_answer_node,
    retrieve_documents_node,
    route_question_node,
    web_search_node,
)
# PostgreSQL memory used to save LangGraph conversation threads.
from app.graph.checkpointer import postgres_checkpointer

def choose_route(state: RAGState) -> str:
    """
    Return the decision created by route_question_node.

    LangGraph uses this returned string to select the next branch.
    """

    return state["route"]


# Create a workflow that shares RAGState between every node.
workflow_builder = StateGraph(RAGState)


# Register all workflow nodes.
workflow_builder.add_node(
    "embed_question",
    embed_question_node,
)

workflow_builder.add_node(
    "retrieve_documents",
    retrieve_documents_node,
)

workflow_builder.add_node(
    "route_question",
    route_question_node,
)

workflow_builder.add_node(
    "web_search",
    web_search_node,
)

workflow_builder.add_node(
    "generate_document_answer",
    generate_document_answer_node,
)

workflow_builder.add_node(
    "generate_routed_answer",
    generate_routed_answer_node,
)


# Begin by embedding the user's question.
workflow_builder.add_edge(
    START,
    "embed_question",
)

# Search Qdrant using the question embedding.
workflow_builder.add_edge(
    "embed_question",
    "retrieve_documents",
)

# Decide whether to use documents, the web or both.
workflow_builder.add_edge(
    "retrieve_documents",
    "route_question",
)


# Follow a different path based on the router's decision.
workflow_builder.add_conditional_edges(
    "route_question",
    choose_route,
    {
        # Document route skips web search.
        "document": "generate_document_answer",

        # Web route performs live search first.
        "web": "web_search",

        # Both also performs web search because document retrieval
        # has already happened earlier in the graph.
        "both": "web_search",
    },
)


# After web search, generate either a web-only or combined answer.
workflow_builder.add_edge(
    "web_search",
    "generate_routed_answer",
)


# Both answer-generation paths finish the workflow.
workflow_builder.add_edge(
    "generate_document_answer",
    END,
)

workflow_builder.add_edge(
    "generate_routed_answer",
    END,
)



# Compile the workflow with persistent PostgreSQL memory.
rag_workflow = workflow_builder.compile(
    checkpointer=postgres_checkpointer,
)