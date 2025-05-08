import os
from tavily import TavilyClient
from app.config import TAVILY_API_KEY, TAVILY_ENABLED # Import from your config
from datetime import datetime

# Initialize Tavily client if enabled
tavily_client = None
if TAVILY_ENABLED:
    try:
        tavily_client = TavilyClient(api_key=TAVILY_API_KEY)
    except Exception as e:
        print(f"Error initializing Tavily client: {e}. Web search will be disabled.")
        TAVILY_ENABLED = False

# Searching the web using Tavily API
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
        # Fallback if Tavily is not available or not configured
        # This message guides the LLM to use its internal knowledge
        return (
            f"Web search skill is not available. Please use your existing knowledge "
            f"to answer the query: '{query}'. If you lack specific real-time information "
            f"(e.g., current events, very specific local details), clearly state that "
            f"your information is based on general knowledge up to your last training cut-off."
        )
    try:
        print(f"\n[Tool Call: search_web] Query: {query}, Max Results: {max_results}")
        # For advanced searches, specify search_depth, topic, etc.
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

def format_day_by_day_itinerary_india(itinerary_details: dict) -> str:
    """
    Formats a dictionary of itinerary details into a readable day-by-day plan,
    tailored slightly for an Indian context.

    Expected input format (using Indian examples and currency):
    {
        "trip_title": "Golden Triangle Cultural Tour",
        "duration_days": 7,
        "destination": "Delhi, Agra, Jaipur (India)",
        "overall_budget_estimate": "₹25,000 - ₹40,000 INR (Excluding Flights)", # Using INR and specifying exclusion
        "daily_plans": [
            {
                "day": 1,
                "theme": "Arrival in Delhi & Old Delhi Flavours",
                "activities": [
                    {"time": "Afternoon", "description": "Arrive at Indira Gandhi International Airport (DEL), transfer to hotel in Delhi.", "est_cost": "₹800-1200 (Cab/Taxi)"}, # Using INR and common local transport term
                    {"time": "Evening", "description": "Explore Chandni Chowk, enjoy dinner at a famous local eatery (e.g., Paranthe Wali Gali).", "est_cost": "₹500-800 (Food & Local Shopping)"} # More specific Indian location/activity
                ],
                "daily_cost_estimate": "₹1500-2000" # Using INR
            },
            {
                "day": 2,
                "theme": "Delhi Heritage & Departure to Agra",
                 "activities": [
                    {"time": "Morning", "description": "Visit India Gate and Rashtrapati Bhavan (from outside).", "est_cost": "₹0"},
                    {"time": "Lunch", "description": "Traditional North Indian lunch.", "est_cost": "₹400"},
                    {"time": "Afternoon", "description": "Travel to Agra by train or road.", "est_cost": "₹700-1500 (Train Ticket/Cab)"}, # Indian transport
                    {"time": "Evening", "description": "Check into hotel in Agra.", "est_cost": "₹0"}
                ],
                "daily_cost_estimate": "₹1100-1900"
            }
            # ... more days
        ]
    }
    """
    if not itinerary_details or not isinstance(itinerary_details, dict):
        return "Error: Itinerary details are missing or not in the expected format."

    output = []
    # Use get with a default value to handle missing keys gracefully
    output.append(f"**{itinerary_details.get('trip_title', 'Your Indian Trip Itinerary')}**")
    output.append(f"Destination: {itinerary_details.get('destination', 'N/A')}")
    output.append(f"Duration: {itinerary_details.get('duration_days', 'N/A')} days")
    output.append(f"Estimated Budget: {itinerary_details.get('overall_budget_estimate', 'N/A')}\n") # Currency comes from input

    if "daily_plans" in itinerary_details and itinerary_details["daily_plans"]:
        for day_plan in itinerary_details["daily_plans"]:
            # Using a consistent header format
            output.append(f"--- Day {day_plan.get('day', 'N/A')}: {day_plan.get('theme', 'Activities')} ---")
            if "activities" in day_plan and day_plan["activities"]:
                for activity in day_plan["activities"]:
                    # Flexibly handle time and cost being optional
                    time_str = f"[{activity.get('time', 'Time not specified')}] " if activity.get('time') else ""
                    cost_str = f" (Est: {activity.get('est_cost', 'Cost not specified')})" if activity.get('est_cost') else ""
                    output.append(f"  - {time_str}{activity.get('description', 'No description')}{cost_str}")
            else:
                output.append("  - No specific activities planned for this day.")

            # Display daily cost estimate
            output.append(f"  Estimated cost for Day {day_plan.get('day', 'N/A')}: {day_plan.get('daily_cost_estimate', 'N/A')}\n")

    else:
        output.append("No daily plans provided.")

    # Adjusted Disclaimer for Indian context
    output.append("\n--- Important Notes ---")
    output.append("Estimated costs are indicative and can vary significantly based on travel style, time of year, and local conditions.")
    output.append("Consider using local transport options like auto-rickshaws, cycle rickshaws, or ride-sharing apps within cities.") # Added transport suggestion
    output.append("Prices for food, shopping, and local transport might be open to bargaining in some areas.") # Added note on bargaining
    output.append("Verify timings and book tickets/accommodations in advance, especially during peak season.")
    output.append("-----------------------")


    return "\n".join(output)
