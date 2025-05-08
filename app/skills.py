import os
from tavily import TavilyClient
from app.config import TAVILY_API_KEY, TAVILY_ENABLED # Import from your config
from datetime import datetime
# Assuming you still have load_dotenv called in app.config or elsewhere
# from dotenv import load_dotenv

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
    tailored with examples and notes specific to Kerala, India.

    Expected input format (using Kerala examples and currency):
    {
        "trip_title": "Kerala: Backwaters, Hills & Culture",
        "duration_days": 6,
        "destination": "Cochin (Kochi), Munnar, Alleppey (Kerala, India)",
        "overall_budget_estimate": "₹20,000 - ₹35,000 INR (Excluding Flights)", # Adjusted estimate based on typical Kerala costs
        "daily_plans": [
            {
                "day": 1,
                "theme": "Arrival in Cochin & Fort Kochi Charm",
                "activities": [
                    {"time": "Afternoon", "description": "Arrive at Cochin International Airport (COK), transfer to hotel in Fort Kochi.", "est_cost": "₹1000-1500 (Cab/Taxi)"},
                    {"time": "Evening", "description": "Explore Chinese Fishing Nets and walk around Fort Kochi area, enjoy dinner at a cafe.", "est_cost": "₹600-1000 (Food & Entry Fees)"}
                ],
                "daily_cost_estimate": "₹1600-2500"
            },
            {
                "day": 2,
                "theme": "Cochin History & Travel to Munnar",
                 "activities": [
                    {"time": "Morning", "description": "Visit Mattancherry Palace and Paradesi Synagogue.", "est_cost": "₹200 (Entry Fees)"},
                    {"time": "Lunch", "description": "Try local Kerala Sadya (traditional meal).", "est_cost": "₹300"},
                    {"time": "Afternoon", "description": "Scenic drive to Munnar (Tea Gardens).", "est_cost": "₹3000-4000 (Private Cab) or ₹300-500 (Bus)"},
                    {"time": "Evening", "description": "Check into hotel/resort in Munnar.", "est_cost": "₹0"}
                ],
                "daily_cost_estimate": "₹3500-4500"
            },
             {
                "day": 3,
                "theme": "Munnar Tea Gardens & Scenery",
                 "activities": [
                    {"time": "Morning", "description": "Visit a Tea Museum and Tea Plantations.", "est_cost": "₹400 (Entry Fees & Tea Tasting)"},
                    {"time": "Afternoon", "description": "Explore Eravikulam National Park (Rajamalai) or Mattupetty Dam.", "est_cost": "₹300-600 (Entry Fees)"},
                    {"time": "Evening", "description": "Relax at the resort or explore local market.", "est_cost": "₹200-500 (Misc.)"}
                ],
                "daily_cost_estimate": "₹900-1500"
            },
            # Add more days for Alleppey (Houseboat, Backwaters), Thekkady (Periyar), Kovalam/Varkala (Beaches), etc.
            # Example Day for Alleppey:
            # {
            #     "day": 4,
            #     "theme": "Travel to Alleppey & Backwater Bliss",
            #     "activities": [
            #         {"time": "Morning", "description": "Travel from Munnar to Alleppey.", "est_cost": "₹2500-3500 (Private Cab) or ₹400-600 (Bus)"},
            #         {"time": "Afternoon", "description": "Check into houseboat for an overnight stay in the backwaters.", "est_cost": "Varies widely (included in houseboat package)"},
            #         {"time": "Evening", "description": "Enjoy cruising through the backwaters, relax on the houseboat.", "est_cost": "₹0"}
            #     ],
            #     "daily_cost_estimate": "Varies widely (dominated by houseboat cost)"
            # },
        ]
    }
    """
    if not itinerary_details or not isinstance(itinerary_details, dict):
        return "Error: Itinerary details are missing or not in the expected format."

    output = []
    output.append(f"**{itinerary_details.get('trip_title', 'Trip Itinerary')}**") 
    output.append(f"Destination: {itinerary_details.get('destination', 'N/A')}")
    output.append(f"Duration: {itinerary_details.get('duration_days', 'N/A')} days")
    output.append(f"Estimated Budget: {itinerary_details.get('overall_budget_estimate', 'N/A')}\n")

    if "daily_plans" in itinerary_details and itinerary_details["daily_plans"]:
        for day_plan in itinerary_details["daily_plans"]:
            output.append(f"--- Day {day_plan.get('day', 'N/A')}: {day_plan.get('theme', 'Activities')} ---")
            if "activities" in day_plan and day_plan["activities"]:
                for activity in day_plan["activities"]:
                    time_str = f"[{activity.get('time', 'Time not specified')}] " if activity.get('time') else ""
                    cost_str = f" (Est: {activity.get('est_cost', 'Cost not specified')})" if activity.get('est_cost') else ""
                    output.append(f"    - {time_str}{activity.get('description', 'No description')}{cost_str}")
            else:
                output.append("    - No specific activities planned for this day.") 
            output.append(f"    Estimated cost for Day {day_plan.get('day', 'N/A')}: {day_plan.get('daily_cost_estimate', 'N/A')}\n")

    else:
        output.append("No daily plans provided.")

    # Adjusted Disclaimer
    output.append("\n--- Important Notes for Kerala Travel ---")
    output.append("Estimated costs are indicative and can vary significantly based on travel style, season (especially monsoon), and local conditions.") 
    output.append("Explore local transport options: Auto-rickshaws are common in towns, KSRTC buses for inter-city travel, and ferries/boats in backwater areas.")
    output.append("The backwaters experience (houseboats/shikaras in Alleppey/Kumarakom) is a key highlight; book in advance, especially during peak season.") 
    output.append("Kerala is famous for its distinct cuisine, spices, and especially Sadya (traditional meal served on a banana leaf); be sure to try local food.") 
    output.append("Respect local customs and traditions, particularly when visiting temples and other cultural sites. Dress modestly when required.") 
    output.append("Verify timings and book tickets/accommodations in advance, particularly for popular attractions, houseboats, and train/bus tickets.")
    output.append("Consider exploring responsible tourism initiatives prevalent in Kerala.") 
    output.append("--------------------------------------")


    return "\n".join(output)