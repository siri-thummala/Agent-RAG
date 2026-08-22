# DDGS provides free public web search without requiring an API key.
from ddgs import DDGS


# Limit the number of results sent to Gemini.
# This keeps answers focused and avoids unnecessarily large prompts.
DEFAULT_WEB_RESULT_LIMIT = 5


def search_web(
    query: str,
    max_results: int = DEFAULT_WEB_RESULT_LIMIT,
) -> list[dict]:
    """
    Search the live web and return normalized result dictionaries.
    """

    # Remove unnecessary spaces around the question.
    cleaned_query = query.strip()

    if not cleaned_query:
        raise ValueError("Web-search query cannot be empty")

    # Prevent invalid or unnecessarily large searches.
    if max_results < 1 or max_results > 10:
        raise ValueError(
            "Web-search result limit must be between 1 and 10"
        )

    # Perform a live text search.
    #
    # timeout=10 prevents the request from waiting forever
    # if a public search provider is temporarily unavailable.
    raw_results = DDGS(timeout=10).text(
        query=cleaned_query,
        region="wt-wt",
        safesearch="moderate",
        max_results=max_results,
    )

    # Convert provider-specific results into one predictable structure.
    web_results: list[dict] = []

    for result in raw_results:
        # DDGS normally uses `href`, but accepting `url` makes
        # the code safer if a provider returns a different field.
        result_url = result.get("href") or result.get("url") or ""

        result_title = result.get("title") or "Untitled result"

        # `body` contains the short search-result description.
        result_snippet = (
            result.get("body")
            or result.get("snippet")
            or ""
        )

        # Skip unusable results that contain neither a URL nor text.
        if not result_url and not result_snippet:
            continue

        web_results.append(
            {
                "title": result_title,
                "url": result_url,
                "snippet": result_snippet,
            }
        )

    return web_results