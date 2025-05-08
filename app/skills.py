import logging
from datetime import datetime
from tavily import TavilyClient
from app.config import TAVILY_ENABLED, TAVILY_API_KEY

# Structured logger for tools
logger = logging.getLogger("trip_planner.tools")

# Initialize Tavily if enabled
if TAVILY_ENABLED:
    tavily = TavilyClient(api_key=TAVILY_API_KEY)
else:
    tavily = None

def search_web(query: str, max_results: int = 3) -> str:
    logger.info(f"[tool] search_web: {query}")
    if not tavily:
        return f"(Web-search disabled) please answer from internal knowledge: {query}"
    try:
        resp = tavily.search(query=query, search_depth="basic", max_results=max_results)
        # format...
        return "\n\n".join(
            f"• {r['title']} – {r['url']}\n  {r.get('content','')}"
            for r in resp.get("results", [])
        ) or "No results found."
    except Exception as e:
        logger.exception("search_web failed")
        return f"Error in search_web: {e}"

def get_current_date() -> str:
    return datetime.now().strftime("%Y-%m-%d")

def format_trip_itinerary(itin: dict) -> str:
    """
    Appends a sentinel tag __END_ITINERARY__ to the formatted string,
    so we can extract it reliably later.
    """
    header = f"**{itin.get('trip_title','Trip Itinerary')}**\n"
    # ... build body ...
    footer = "\n---\nDisclaimer: This is a suggested itinerary."
    return header + "... (body) ..." + footer + "\n\n__END_ITINERARY__"
