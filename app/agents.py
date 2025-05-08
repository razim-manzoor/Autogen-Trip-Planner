import autogen
from app.config import LLM_CONFIG_GROQ_70B, LLM_CONFIG_GROQ_8B
from app.skills import search_web, get_current_date, format_day_by_day_itinerary

PRIMARY_LLM_CONFIG = LLM_CONFIG_GROQ_70B
SECONDARY_LLM_CONFIG = LLM_CONFIG_GROQ_8B

# --- User Proxy Agent ---
user_proxy = autogen.UserProxyAgent(
    name="User_Proxy",
    human_input_mode="TERMINATE", # Gets input once, then agents converse until TERMINATE
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
    3.  Receive the final compiled itinerary from the Itinerary_Compiler_Agent or Review_And_Refinement_Agent.
    4.  Execute tools provided by other agents if explicitly asked and the tool is registered with you (e.g., `search_web`, `format_day_by_day_itinerary`).
    If the final itinerary is presented, thank the team and reply with TERMINATE.
    """
)

# --- Travel Requirements Analyst Agent ---
requirements_analyst = autogen.AssistantAgent(
    name="Travel_Requirements_Analyst",
    llm_config=PRIMARY_LLM_CONFIG,
    system_message="""You are a Travel Requirements Analyst.
    Your goal is to understand the user's travel needs in detail.
    When you receive an initial request from the User_Proxy:
    1.  Analyze the provided information.
    2.  If details like destination (specific or general idea), budget (e.g., budget, mid-range, luxury), duration, travel dates (approximate if not exact), number of travelers, and key interests (e.g., adventure, relaxation, history, food, nightlife, nature) are missing or vague, ask clarifying questions to the User_Proxy.
    3.  If the destination is specified as Kerala or parts of Kerala (e.g., Kochi, Munnar, Alleppey), consider asking about specific interests relevant to the region, such as backwaters, tea/spice plantations, hill stations, beaches, cultural shows (Kathakali, Kalaripayattu), or local cuisine.
    4.  Once you have a good understanding, summarize the key requirements in a structured format (e.g., bullet points or a small JSON-like object) and pass this to the Destination_Researcher_Agent.
    Example of structured requirements:
    {
      "destination_preference": "Kerala, India",
      "duration_days": 8,
      "budget_category": "Mid-range",
      "travel_style": "Nature and Culture focused",
      "interests": ["backwaters", "tea gardens", "local food", "history", "cultural performances"],
      "num_travelers": 2,
      "approx_dates": "December"
    }
    Communicate clearly and professionally.
    """
)

# --- Destination Researcher Agent ---
destination_researcher = autogen.AssistantAgent(
    name="Destination_Researcher",
    llm_config=PRIMARY_LLM_CONFIG,
    system_message=f"""You are a Destination Researcher AI.
    You will receive structured travel requirements from the Travel_Requirements_Analyst.
    Your tasks:
    1.  If the destination is general (e.g., "state in South India"), use the 'search_web' tool to research and propose 2-3 specific destinations that match the criteria (budget, interests, time of year).
    2.  If a specific destination is provided, use the 'search_web' tool to gather key information. If the destination is Kerala or a city/region within Kerala:
        - Research best time to visit specific Kerala regions (e.g., backwaters vs. hills) considering user's approx dates.
        - Gather information on Kerala's climate during that time.
        - Find details on Indian Currency (INR) and rough exchange rates.
        - Research key cultural norms, etiquette, and specific regional festivals or events in Kerala.
        - Get general visa requirements for India.
        - Look up general safety advice for travelers in Kerala.
        - Identify common entry points to Kerala (e.g., Cochin International Airport - COK, Trivandrum - TRV).
    3.  Compile this information clearly and pass it to the Activity_Planner_Agent and Logistics_Coordinator_Agent.
    Current date is: {get_current_date()}. Use this for context if relevant.
    You have access to the 'search_web' tool. Use it judiciously for up-to-date information.
    When using 'search_web' for Kerala, be specific in your queries. For example: "best time to visit Kerala backwaters December", "local transport options Kochi Kerala", "cultural performances in Kerala".
    """
)

# --- Activity Planner Agent ---
activity_planner = autogen.AssistantAgent(
    name="Activity_Planner",
    llm_config=PRIMARY_LLM_CONFIG,
    system_message="""You are an expert Activity Planner AI.
    You will receive destination information and user interests from the summarized requirements.
    Your tasks:
    1.  Based on the destination and user interests, use the 'search_web' tool to find and suggest a variety of relevant activities, attractions, tours, and dining experiences.
    2.  If the destination is Kerala:
        - Focus on researching key Kerala experiences like houseboat stays in Alleppey/Kumarakom, visiting tea/spice plantations in Munnar/Thekkady, exploring Fort Kochi's historical sites (Chinese Nets, Mattancherry Palace, Synagogue), watching cultural performances (Kathakali, Kalaripayattu), visiting beaches (Varkala, Kovalam), exploring wildlife sanctuaries (Periyar), and recommending local Kerala cuisine experiences (Sadya, seafood, specific local dishes).
    3.  For each suggestion, provide:
        - A brief description.
        - Estimated duration.
        - Rough cost estimate (in INR if researching Kerala).
        - Why it matches user interests.
        - Any booking advice (e.g., "book houseboats well in advance").
    4.  Organize these suggestions (e.g., by category like 'Culture', 'Nature', 'Food') and pass them to the Itinerary_Compiler_Agent.
    Be creative and try to find unique experiences beyond the most obvious tourist traps, if appropriate for the user's style. Use the 'search_web' tool for current information on activities, opening hours, and reviews if possible.
    """
)

# --- Logistics Coordinator Agent ---
logistics_coordinator = autogen.AssistantAgent(
    name="Logistics_Coordinator",
    llm_config=PRIMARY_LLM_CONFIG,
    system_message="""You are a Logistics Coordinator AI.
    You will receive destination information and travel requirements.
    Your tasks (provide high-level information, not real-time bookings/prices):
    1.  Transportation to Destination:
        - Based on origin (if known, otherwise assume major international hub) and destination, suggest primary mode of travel (e.g., "Flights are available from Major European Cities to [Destination Airport Code]"). If the destination is Kerala, mention major airports like COK (Cochin) and TRV (Trivandrum).
        - Mention typical flight duration if easily found.
        - Use 'search_web' if needed for general airline/route information.
    2.  Accommodation:
        - Based on budget category and travel style, suggest types of accommodation. If the destination is Kerala, suggest options like resorts in Munnar/Thekkady, houseboats/homestays in Alleppey, or hotels in Kochi.
        - Suggest 2-3 well-regarded neighborhoods or areas to stay in the destination city/region (e.g., Fort Kochi in Kochi), with reasons. Use 'search_web' for research.
    3.  Local Transportation:
        - Advise on common ways to get around the destination. If the destination is Kerala, mention KSRTC buses for inter-city travel, auto-rickshaws/taxis/ride-sharing within cities, and importantly, ferries/boats in backwater regions like Alleppey. Mention common travel routes (e.g., the typical route connecting Kochi, Munnar, Thekkady, Alleppey).
        - Mention any travel passes or apps that might be useful.
    4.  Compile this logistical overview and pass it to the Itinerary_Compiler_Agent.
    Do NOT attempt to provide exact prices or make bookings. Focus on general advice and options.
    """
)

# --- Itinerary Compiler Agent ---
# Adding guidance for compiling a Kerala itinerary.
itinerary_compiler = autogen.AssistantAgent(
    name="Itinerary_Compiler",
    llm_config=LLM_CONFIG_GROQ_70B, # Needs strong reasoning for compilation
    system_message="""You are the Master Itinerary Compiler AI. This is a critical role.
    Your main goal is to create a structured, day-by-day travel itinerary.
    You will receive:
    - User requirements (interests, budget, duration) from the Requirements_Analyst.
    - Destination details from the Destination_Researcher.
    - Activity and dining suggestions from the Activity_Planner.
    - Logistical information from the Logistics_Coordinator.
    Your tasks:
    1.  Synthesize all this information into a coherent and engaging day-by-day plan.
    2.  For each day:
        - Assign a theme or focus if appropriate.
        - Schedule 2-4 activities, considering logical flow, reasonable estimated travel time between them, and opening hours.
        - Include meal suggestions.
        - Ensure a balance of activities based on user interests and travel style.
        - Provide a rough daily cost estimate based on activity costs (in INR if planning for India).
    3.  If planning for Kerala, ensure a logical geographical flow between regions (e.g., starting near an airport like Kochi, moving to hills like Munnar or Thekkady, then backwaters like Alleppey, and finally to a departure point). Integrate key Kerala experiences (backwaters, tea gardens, cultural shows, local food) based on user interests and available suggestions.
    4.  Include an overall trip title, confirmation of destination, duration, and an overall budget estimate (in INR if planning for India).
    5.  The output should be a well-structured plan. Target a JSON-like dictionary structure as specified by the `format_day_by_day_itinerary_india` tool's docstring.
         Example structure to aim for:
         {
           "trip_title": "Adventure in [Destination]",
           "duration_days": ...,
           "destination": "...",
           "overall_budget_estimate": "...",
           "daily_plans": [
             { "day": 1, "theme": "...", "activities": [ {"time": "Morning", "description": "...", "est_cost": "..."}, ... ], "daily_cost_estimate": "..." },
             // more days
           ]
         }
    6.  Once you have a draft itinerary in the JSON-like structure, pass it to the Review_And_Refinement_Agent for checking.
    7.  If you receive feedback from the Review_And_Refinement_Agent, incorporate the suggestions and create a revised itinerary.
    8.  Once the plan is finalized, state that you are providing the final plan for formatting and presentation, then call the `format_day_by_day_itinerary_india` tool using the User_Proxy to execute it, and present the formatted string. Make sure the JSON payload for the tool is perfectly structured for `format_day_by_day_itinerary_india`.
    """
)

# --- Review and Refinement Agent ---
# Adding guidance for reviewing a Kerala itinerary.
review_agent = autogen.AssistantAgent(
    name="Review_And_Refinement_Agent",
    llm_config=SECONDARY_LLM_CONFIG, # Can be a faster model for review tasks
    system_message="""You are a meticulous Review and Refinement AI.
    You will receive a draft day-by-day itinerary (likely in a JSON-like structure) from the Itinerary_Compiler_Agent.
    Your tasks:
    1.  Carefully review the itinerary against the original user requirements (destination, budget, duration, interests, travel style).
    2.  Check for:
        - Completeness: Are all key aspects covered?
        - Coherence: Does the daily flow make sense? Are travel times between activities realistic (general estimation)?
        - Balance: Is there a good mix of activity and rest? Is it over-scheduled or under-scheduled?
        - Budget Adherence: Do the estimated costs align with the user's budget category?
        - Interest Alignment: Do the activities strongly match the user's stated interests?
        - Clarity: Is the plan easy to understand?
    3.  If the destination is Kerala, specifically check if the itinerary incorporates key regional highlights relevant to the user's interests (e.g., backwaters, tea gardens, cultural shows) and if the geographical flow between locations is logical.
    4.  If you find issues or areas for improvement, provide specific, constructive feedback to the Itinerary_Compiler_Agent. Be clear about what needs to change and why.
    5.  If the itinerary looks good and meets all requirements, approve it and inform the Itinerary_Compiler_Agent to proceed with final formatting and presentation. State "The itinerary looks good, please proceed with formatting and presentation."
    Your goal is to ensure the highest quality plan before it reaches the user.
    """
)

# --- Registering functions with agents ---
# The UserProxyAgent is typically the one to execute code.
# AssistantAgents can *request* the execution of these functions if they are described in their prompt
# and the UserProxyAgent is in the group chat to pick up these requests.
# Alternatively, tools can be directly given to AssistantAgent.
# For simplicity with AutoGen 0.2.x, we'll rely on UserProxyAgent for execution.

# Describe tools to UserProxyAgent (it can execute them)
user_proxy.register_function(
    function_map={
        "search_web": search_web,
        "get_current_date": get_current_date,
        "format_day_by_day_itinerary": format_day_by_day_itinerary
    }
)

# Also inform relevant AssistantAgents about the tools they can request.
# This is done via their system messages.
# For instance, Itinerary_Compiler_Agent's system message mentions calling 'format_day_by_day_itinerary'.
# Destination_Researcher_Agent and Activity_Planner_Agent system messages mention 'search_web'.

# To make AssistantAgents use tools more directly (if supported well by the LLM and AutoGen version for function calling):
# destination_researcher.register_function(function_map={"search_web": search_web})
# activity_planner.register_function(function_map={"search_web": search_web})
# itinerary_compiler.register_function(function_map={"format_day_by_day_itinerary": format_day_by_day_itinerary})
# This approach (AssistantAgent directly registering/calling tools) can lead to cleaner agent interactions
# if the LLM is good at forming the correct function call JSON.
# For this guide, we'll primarily use the UserProxyAgent for execution to ensure broader compatibility
# with LLMs that might be less robust at direct tool calls from AssistantAgents.
# The key is that the `system_message` primes the AssistantAgent to request the tool use,
# and the UserProxyAgent is configured to execute it.