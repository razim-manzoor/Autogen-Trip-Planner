import autogen
from app.agents import (
    create_user_proxy,
    create_requirements_analyst,
    create_destination_researcher,
    create_activity_planner,
    create_logistics_coordinator,
    create_itinerary_compiler,
    create_review_agent,
    register_functions_for_user_proxy
)
from app.config import LLM_CONFIG_GROQ_70B

def run_trip_planner_chat(initial_request: str) -> str:
    """
    Initializes and runs the agent chat for trip planning.
    Returns the final formatted itinerary string.
    """
    # Create fresh agent instances for each run
    user_proxy = create_user_proxy()
    requirements_analyst = create_requirements_analyst()
    destination_researcher = create_destination_researcher()
    activity_planner = create_activity_planner()
    logistics_coordinator = create_logistics_coordinator()
    itinerary_compiler = create_itinerary_compiler()
    review_agent = create_review_agent()

    # Register functions for the newly created user_proxy
    register_functions_for_user_proxy(user_proxy)

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
        max_round=35,  # Increased max rounds for complex task + formatting step
        speaker_selection_method="auto",
        send_introductions=True,
    )

    manager = autogen.GroupChatManager(
        groupchat=groupchat,
        llm_config=LLM_CONFIG_GROQ_70B
    )

    # Initiate the chat
    user_proxy.initiate_chat(
        manager,
        message=f"""Hello team, I need your help planning a trip. Here's my initial thought: '{initial_request}'.
        The Travel_Requirements_Analyst should start by clarifying details if needed.
        The Itinerary_Compiler_Agent is responsible for generating the plan, getting it reviewed by Review_And_Refinement_Agent,
        then calling the 'format_trip_itinerary' tool, and finally presenting the formatted string output from that tool to me.
        I (User_Proxy) will terminate the conversation once I receive this complete formatted itinerary string.
        """
    )

    # --- Extract the final formatted itinerary ---
    # The Itinerary_Compiler_Agent is instructed to present the exact string from the
    # format_trip_itinerary tool as its final message to the User_Proxy.
    # The User_Proxy is instructed to terminate after receiving this.
    # So, the last message User_Proxy received from Itinerary_Compiler should be the plan.

    final_plan_str = "Error: Could not extract the final formatted itinerary."

    # Get chat history between User_Proxy and Itinerary_Compiler
    itinerary_compiler_messages = user_proxy.chat_messages.get(itinerary_compiler, [])

    if itinerary_compiler_messages:
        # Iterate backwards through messages from Itinerary_Compiler to User_Proxy
        for msg in reversed(itinerary_compiler_messages):
            content = msg.get("content", "")
            # The formatted plan should be a string and contain specific markers
            # from the format_trip_itinerary function.
            # It should NOT be a tool_call itself.
            if isinstance(content, str) and \
               "**" in content and \
               "--- Day" in content and \
               "Disclaimer: This is a suggested itinerary." in content and \
               not msg.get("tool_calls"): # Ensure it's not a request to call a tool
                final_plan_str = content
                break
    
    # Fallback: if the above didn't find it, check all messages in the group chat for the last one from itinerary_compiler.
    # This is less precise.
    if final_plan_str.startswith("Error:"): # if not found by previous method
        for msg in reversed(groupchat.messages):
            if msg.get("name") == itinerary_compiler.name and msg.get("role") == "assistant":
                content = msg.get("content", "")
                if isinstance(content, str) and \
                   "**" in content and \
                   "--- Day" in content and \
                   "Disclaimer: This is a suggested itinerary." in content and \
                   not msg.get("tool_calls"):
                    final_plan_str = content
                    break
    
    return final_plan_str


if __name__ == "__main__":
    print("Welcome to the AI Agentic Trip Planner!")
    print("Powered by AutoGen and Groq.")
    print("To start, please describe your desired trip. For example:")
    print("- 'A 5-day trip to Kerala for 2 people in January, focusing on backwaters and tea gardens, mid-range budget.'")
    print("- 'Plan a 10-day journey through Kerala for a family of 4, exploring Kochi, Munnar, Thekkady, and Alleppey, sometime next winter.'\n")

    initial_user_request = input("Your trip request: ")

    if not initial_user_request.strip():
        print("No request entered. Exiting.")
    else:
        print("\nInitializing AI agent team... This may take a moment.\n")
        # Capture stdout for full log, even if we get direct result
        import sys
        from io import StringIO
        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()
        
        try:
            final_itinerary = run_trip_planner_chat(initial_user_request)
            print("\n--- FINAL ITINERARY (Direct Result) ---")
            print(final_itinerary)
        except Exception as e:
            print(f"An error occurred during trip planning: {e}")
        finally:
            sys.stdout = old_stdout # Restore stdout
            full_log = captured_output.getvalue()
            print("\n--- FULL AGENT INTERACTION LOG ---")
            print(full_log)
            print("\nTrip planning session concluded.")