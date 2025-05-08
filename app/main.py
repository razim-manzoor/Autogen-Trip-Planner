import autogen
from app.agents import (
    user_proxy,
    requirements_analyst,
    destination_researcher,
    activity_planner,
    logistics_coordinator,
    itinerary_compiler,
    review_agent
)
from app.config import LLM_CONFIG_GROQ_70B

def run_trip_planner_chat(initial_request: str):
    """
    Initializes and runs the agent chat for trip planning.
    """
    # Define the group chat and manager
    # The order of agents here can influence the conversation flow if speaker_selection_method is not 'auto'
    # or if 'auto' has biases.
    groupchat = autogen.GroupChat(
        agents=[
            user_proxy,
            requirements_analyst,
            destination_researcher,
            activity_planner,
            logistics_coordinator,
            itinerary_compiler,
            review_agent
        ],
        messages=[],
        max_round=30,  # Increased max rounds for a more complex task
        # speaker_selection_method="round_robin" # For more deterministic flow initially
        # speaker_selection_method="auto" # 'auto' can be powerful but less predictable.
                                        # Requires very clear prompts.
        # For a complex workflow like this, a more controlled handoff can be beneficial.
        # We can try 'auto' first. If it struggles, explicit instructions or a round_robin approach
        # coupled with clear instructions in agent prompts ("After you do X, talk to Agent Y") are needed.
        # A custom speaker transition graph can also be defined.
        # Let's try 'auto' with strong prompts.
        speaker_selection_method="auto",
        send_introductions=True, # Helps agents know who is in the team
    )

    manager = autogen.GroupChatManager(
        groupchat=groupchat,
        llm_config=LLM_CONFIG_GROQ_70B # Manager uses an LLM to decide next speaker with "auto"
    )
    
    # Initiate the chat
    # The initial message should guide the first agent (Requirements Analyst)
    user_proxy.initiate_chat(
        manager,
        message=f"Hello team, I need your help planning a trip. Here's my initial thought: '{initial_request}'. Please start by having the Travel_Requirements_Analyst clarify the details with me (User_Proxy) if needed, then proceed with the planning process. The final output should be a formatted itinerary presented by the Itinerary_Compiler_Agent after review from the Review_And_Refinement_Agent. The User_Proxy will then terminate the conversation."
    )

if __name__ == "__main__":
    print("Welcome to the AI Agentic Trip Planner!")
    print("Powered by AutoGen and Groq.")
    print("To start, please describe your desired trip. For example:")
    print("- 'A 5-day trip to Kerala for 2 people in January, focusing on backwaters in Alleppey and tea gardens in Munnar, mid-range budget.'")
    print("- 'Plan a 10-day journey through Kerala for a family of 4, exploring Kochi, Munnar, Thekkady, and Alleppey, with interests in nature, wildlife, and culture, sometime next winter.'")
    print("- 'Suggest a 4-day food and history tour of Fort Kochi for a solo traveler next month, budget friendly.'\n")
    
    initial_user_request = input("Your trip request: ")

    if not initial_user_request.strip():
        print("No request entered. Exiting.")
    else:
        print("\nInitializing AI agent team... This may take a moment.\n")
        run_trip_planner_chat(initial_user_request)
        print("\nTrip planning session concluded.")