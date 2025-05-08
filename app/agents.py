import autogen
from app.config import LLM_CONFIG_GROQ_70B, LLM_CONFIG_GROQ_8B
from app.skills import search_web, get_current_date, format_trip_itinerary

PRIMARY_LLM_CONFIG = LLM_CONFIG_GROQ_70B
SECONDARY_LLM_CONFIG = LLM_CONFIG_GROQ_8B

# --- Agent Factory Functions ---

def create_user_proxy():
    return autogen.UserProxyAgent(
        name="User_Proxy",
        human_input_mode="TERMINATE",
        max_consecutive_auto_reply=15,
        is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
        code_execution_config={
            "work_dir": "coding_trip_planner",
            "use_docker": False,
        },
        system_message="""You are the user's representative.
        Your role is to:
        1.  Provide the initial trip planning request to the agent team.
        2.  Clarify any questions the agents might have if they direct them to you specifically.
        3.  Receive the final compiled and formatted itinerary string from the Itinerary_Compiler_Agent.
        4.  Once you receive the complete formatted itinerary, acknowledge it, and then reply with only the word TERMINATE.
        5.  You can execute tools like 'search_web', 'get_current_date', and 'format_trip_itinerary' if an agent provides the correct tool call.
        Ensure the final output before termination is the formatted itinerary.
        """
    )

def create_requirements_analyst():
    return autogen.AssistantAgent(
        name="Travel_Requirements_Analyst",
        llm_config=PRIMARY_LLM_CONFIG,
        system_message="""You are a Travel Requirements Analyst.
        Your goal is to understand the user's travel needs in detail.
        When you receive an initial request from the User_Proxy:
        1.  Analyze the provided information.
        2.  If details like destination, budget, duration, travel dates, number of travelers, and key interests are missing or vague, ask clarifying questions to the User_Proxy.
        3.  If the destination is specified as Kerala or parts of Kerala, consider asking about specific interests relevant to the region (backwaters, tea plantations, hill stations, beaches, cultural shows, local cuisine).
        4.  Once you have a good understanding, summarize the key requirements in a structured format (e.g., bullet points or a JSON object) and pass this to the Destination_Researcher_Agent.
        Example of structured requirements:
        {
        "destination_preference": "Kerala, India", "duration_days": 8, "budget_category": "Mid-range",
        "travel_style": "Nature and Culture focused", "interests": ["backwaters", "tea gardens", "local food"],
        "num_travelers": 2, "approx_dates": "December"
        }
        Communicate clearly and professionally.
        """
    )

def create_destination_researcher():
    current_date_str = get_current_date() # Get current date once for the prompt
    return autogen.AssistantAgent(
        name="Destination_Researcher",
        llm_config=PRIMARY_LLM_CONFIG,
        system_message=f"""You are a Destination Researcher AI. Current date is: {current_date_str}.
        You will receive structured travel requirements from the Travel_Requirements_Analyst.
        Your tasks:
        1.  If the destination is general, use the 'search_web' tool to research and propose 2-3 specific destinations matching criteria.
        2.  If a specific destination is provided (especially Kerala or cities within):
            - Research best time to visit specific regions considering user's approx dates.
            - Gather climate information for that time.
            - Find details on local currency (e.g., INR for India) and rough exchange rates.
            - Research key cultural norms, etiquette, and regional festivals/events.
            - Get general visa requirements (e.g., for India).
            - Look up general safety advice for travelers.
            - Identify common entry points (e.g., Cochin International Airport - COK, Trivandrum - TRV for Kerala).
        3.  Compile this information clearly and pass it to the Activity_Planner_Agent and Logistics_Coordinator_Agent.
        You have access to the 'search_web' tool. Use it judiciously for up-to-date information. For Kerala, be specific in queries like "best time to visit Kerala backwaters December", "cultural performances in Kerala".
        """
    )

def create_activity_planner():
    return autogen.AssistantAgent(
        name="Activity_Planner",
        llm_config=PRIMARY_LLM_CONFIG,
        system_message="""You are an expert Activity Planner AI.
        You will receive destination information and user interests.
        Your tasks:
        1.  Based on destination and interests, use 'search_web' to find and suggest relevant activities, attractions, tours, and dining experiences.
        2.  If the destination is Kerala:
            - Focus on key Kerala experiences: houseboat stays (Alleppey/Kumarakom), tea/spice plantations (Munnar/Thekkady), Fort Kochi sites (Chinese Nets, Mattancherry Palace), cultural shows (Kathakali, Kalaripayattu), beaches (Varkala), wildlife sanctuaries (Periyar), and local Kerala cuisine.
        3.  For each suggestion, provide: brief description, estimated duration, rough cost estimate (in local currency, e.g., INR for Kerala), why it matches user interests, and booking advice (e.g., "book houseboats well in advance").
        4.  Organize these suggestions (e.g., by category) and pass them to the Itinerary_Compiler_Agent.
        Use 'search_web' for current information. Be creative.
        """
    )

def create_logistics_coordinator():
    return autogen.AssistantAgent(
        name="Logistics_Coordinator",
        llm_config=PRIMARY_LLM_CONFIG,
        system_message="""You are a Logistics Coordinator AI.
        You will receive destination information and travel requirements.
        Your tasks (provide high-level information, not real-time bookings/prices):
        1.  Transportation to Destination: Suggest primary mode (e.g., "Flights to [Destination Airport Code]"). For Kerala, mention COK (Cochin), TRV (Trivandrum). Mention typical flight duration. Use 'search_web' for general airline/route info.
        2.  Accommodation: Based on budget/style, suggest types. For Kerala: resorts (Munnar), houseboats/homestays (Alleppey), hotels (Kochi). Suggest 2-3 well-regarded areas to stay with reasons. Use 'search_web'.
        3.  Local Transportation: Advise on common ways to get around. For Kerala: KSRTC buses, auto-rickshaws/taxis/ride-sharing, ferries/boats in backwaters. Mention common travel routes (e.g., Kochi-Munnar-Thekkady-Alleppey).
        4.  Compile this logistical overview and pass it to the Itinerary_Compiler_Agent.
        Do NOT provide exact prices or make bookings. Focus on general advice.
        """
    )

def create_itinerary_compiler():
    return autogen.AssistantAgent(
        name="Itinerary_Compiler",
        llm_config=LLM_CONFIG_GROQ_70B,
        system_message="""You are the Master Itinerary Compiler AI. This is a critical role.
        Your main goal is to create a structured, day-by-day travel itinerary.
        You will receive inputs from other agents. Your tasks:
        1.  Synthesize all information into a coherent day-by-day plan.
        2.  For each day: assign theme, schedule 2-4 activities (logical flow, travel time, opening hours), include meal suggestions, ensure balance, provide rough daily cost estimate (local currency).
        3.  If planning for Kerala, ensure logical geographical flow and integrate key Kerala experiences.
        4.  The output should be a JSON object containing 'trip_title', 'duration_days', 'destination', 'overall_budget_estimate', and 'daily_plans' (list of day objects).
            Example structure for the JSON:
            {
            "trip_title": "Adventure in [Destination]", "duration_days": ..., "destination": "...",
            "overall_budget_estimate": "...",
            "daily_plans": [
                { "day": 1, "theme": "...", "activities": [ {"time": "Morning", "description": "...", "est_cost": "..."}, ... ], "daily_cost_estimate": "..." },
                // more days
            ]
            }
        5.  Once you have a draft itinerary in this JSON structure, pass it to the Review_And_Refinement_Agent.
        6.  If you receive feedback, incorporate suggestions and create a revised JSON itinerary.
        7.  Once the JSON plan is finalized and approved by the Review_And_Refinement_Agent, you MUST:
            a. Announce that you are now formatting the final plan.
            b. Explicitly call the 'format_trip_itinerary' tool with the finalized JSON payload. The User_Proxy will execute this.
            c. Wait for the tool to return the formatted string.
            d. Present THIS EXACT FORMATTED STRING as your final message to the User_Proxy. Do not add any extra text before or after this formatted string in your final message.
        """
    )

def create_review_agent():
    return autogen.AssistantAgent(
        name="Review_And_Refinement_Agent",
        llm_config=SECONDARY_LLM_CONFIG,
        system_message="""You are a meticulous Review and Refinement AI.
        You will receive a draft day-by-day itinerary (JSON structure) from the Itinerary_Compiler_Agent.
        Your tasks:
        1.  Carefully review the itinerary against original user requirements.
        2.  Check for: completeness, coherence, balance, budget adherence, interest alignment, clarity.
        3.  If the destination is Kerala, check for inclusion of regional highlights and logical geographical flow.
        4.  If issues: provide specific, constructive feedback to Itinerary_Compiler_Agent on what to change in the JSON.
        5.  If the JSON itinerary looks good: approve it by saying "The JSON itinerary is approved. Please proceed with formatting and presentation using the 'format_trip_itinerary' tool."
        Your goal is to ensure the highest quality JSON plan before it's formatted.
        """
    )

# --- Function to register tools with User Proxy ---
def register_functions_for_user_proxy(user_proxy_agent):
    user_proxy_agent.register_function(
        function_map={
            "search_web": search_web,
            "get_current_date": get_current_date,
            "format_trip_itinerary": format_trip_itinerary # Standardized name
        }
    )