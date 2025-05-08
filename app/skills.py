import os
from tavily import TavilyClient
from app.config import TAVILY_API_KEY, TAVILY_ENABLED
from datetime import datetime

tavily_client = None
if TAVILY_ENABLED:
    try:
        tavily_client = TavilyClient(api_key=TAVILY_API_KEY)
    except Exception as e:
        print(f"Error initializing Tavily client: {e}. Web search will be disabled.")
        TAVILY_ENABLED = False

def search_web(query: str, max_results: int = 3) -> str:
    """
    Performs a web search using Tavily API for the given query.
    Args:
        query (str): The search query.
        max_results (int): Maximum number of search results to return.
    Returns:
        str: A formatted string of search results, or an error message/LLM knowledge indication.
    """
    if not TAVILY_ENABLED or tavily_client is None:
        return (
            f"Web search skill is not available. Please use your existing knowledge "
            f"to answer the query: '{query}'. If you lack specific real-time information "
            f"(e.g., current events, very specific local details), clearly state that "
            f"your information is based on general knowledge up to your last training cut-off."
        )
    try:
        print(f"\n[Tool Call: search_web] Query: {query}, Max Results: {max_results}")
        response = tavily_client.search(query=query, search_depth="basic", max_results=max_results)
        results = []
        if "results" in response and response["results"]:
            for result in response["results"]:
                results.append(f"Title: {result.get('title', 'N/A')}\nURL: {result.get('url', 'N/A')}\nContent: {result.get('content', 'N/A')}\n---")
            formatted_response = "\n".join(results)
            print(f"[Tool Call: search_web] Results found: {len(response['results'])}")
            return formatted_response
        else:
            print("[Tool Call: search_web] No results found by Tavily.")
            return "No direct search results found. Please try rephrasing the query or use general knowledge."
    except Exception as e:
        print(f"[Tool Call: search_web] Error during Tavily search: {e}")
        return f"Error performing web search: {e}. Please rely on general knowledge or try rephrasing."

def get_current_date() -> str:
    """Returns the current date in YYYY-MM-DD format."""
    return datetime.now().strftime("%Y-%m-%d")

def format_trip_itinerary(itinerary_details: dict) -> str:
    """
    Formats a dictionary of itinerary details into a readable day-by-day plan.
    The dictionary should conform to a structure with 'trip_title', 'destination',
    'duration_days', 'overall_budget_estimate', and 'daily_plans'.
    Each daily_plan should have 'day', 'theme', 'activities' (list of dicts with 'time', 'description', 'est_cost'),
    and 'daily_cost_estimate'.

    Example input format:
    {
        "trip_title": "Kerala: Backwaters, Hills & Culture",
        "duration_days": 3,
        "destination": "Cochin (Kochi), Munnar (Kerala, India)",
        "overall_budget_estimate": "₹20,000 - ₹35,000 INR (Excluding Flights)",
        "daily_plans": [
            {
                "day": 1, "theme": "Arrival in Cochin & Fort Kochi Charm",
                "activities": [
                    {"time": "Afternoon", "description": "Arrive at Cochin International Airport (COK), transfer to hotel in Fort Kochi.", "est_cost": "₹1000-1500 (Cab/Taxi)"},
                    {"time": "Evening", "description": "Explore Chinese Fishing Nets and walk around Fort Kochi area.", "est_cost": "₹600-1000 (Food & Entry Fees)"}
                ],
                "daily_cost_estimate": "₹1600-2500"
            },
            // more days
        ]
    }
    """
    if not itinerary_details or not isinstance(itinerary_details, dict):
        return "Error: Itinerary details are missing or not in the expected dictionary format."

    output = []
    output.append(f"**{itinerary_details.get('trip_title', 'Trip Itinerary')}**")
    output.append(f"Destination: {itinerary_details.get('destination', 'N/A')}")
    output.append(f"Duration: {itinerary_details.get('duration_days', 'N/A')} days")
    output.append(f"Estimated Overall Budget: {itinerary_details.get('overall_budget_estimate', 'N/A')}\n")

    daily_plans = itinerary_details.get("daily_plans")
    if isinstance(daily_plans, list) and daily_plans:
        for day_plan in daily_plans:
            if not isinstance(day_plan, dict):
                output.append("Error: Invalid day_plan structure encountered.")
                continue
            output.append(f"--- Day {day_plan.get('day', 'N/A')}: {day_plan.get('theme', 'Activities')} ---")
            activities = day_plan.get("activities")
            if isinstance(activities, list) and activities:
                for activity in activities:
                    if not isinstance(activity, dict):
                        output.append("  - Error: Invalid activity structure.")
                        continue
                    time_str = f"[{activity.get('time', 'Time N/A')}] " if activity.get('time') else ""
                    cost_str = f" (Est: {activity.get('est_cost', 'Cost N/A')})" if activity.get('est_cost') else ""
                    output.append(f"    - {time_str}{activity.get('description', 'No description')}{cost_str}")
            else:
                output.append("    - No specific activities planned for this day.")
            output.append(f"    Estimated cost for Day {day_plan.get('day', 'N/A')}: {day_plan.get('daily_cost_estimate', 'N/A')}\n")
    else:
        output.append("No daily plans provided or daily_plans is not a list.")

    output.append("\n--- Important Notes ---")
    output.append("All costs are estimates and can vary based on choices, seasonality, and local conditions.")
    output.append("Verify opening hours, booking requirements, and travel advisories before your trip.")
    output.append("This is a suggested itinerary. Feel free to customize it to your preferences.")
    output.append("Consider local transport options, cultural etiquette, and responsible tourism practices for your chosen destination.")
    output.append("If traveling to Kerala, India: Explore backwaters (Alleppey/Kumarakom), tea/spice plantations (Munnar/Thekkady), beaches (Varkala/Kovalam), and cultural performances. Enjoy local cuisine like Sadya.")
    output.append("--------------------------------------")
    output.append("Disclaimer: This is a suggested itinerary. Verify all details before making bookings.") # Gradio app looks for this specifically
    return "\n".join(output)