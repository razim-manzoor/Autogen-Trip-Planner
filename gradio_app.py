import gradio as gr
import sys
import os
from io import StringIO
import threading # To run autogen in a separate thread and not block Gradio

# Add the app directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'app')))

try:
    from app import main as autogen_main_module
    from app.agents import user_proxy # To reset if needed
    # We need to be careful about how autogen_main_module.run_trip_planner_chat is structured
    # It's better to have a function that returns the final result or captures it.
except ImportError as e:
    print(f"Error importing AutoGen modules for Gradio: {e}")
    # This error will show in console, Gradio app might fail to start or run properly.


# --- Global variable to store conversation ---
# This is a simple way, for more complex apps, consider state management
conversation_log_list = []

def capture_and_run_autogen(initial_request):
    global conversation_log_list
    conversation_log_list = ["Processing your request... This might take several minutes.\n"] # Reset log

    # Capture stdout
    old_stdout = sys.stdout
    sys.stdout = captured_output = StringIO()

    # Reset agents for a fresh run in Gradio (important!)
    # This requires agents to be accessible and have a reset method or be re-initialized.
    # For simplicity, we rely on re-initialization if main.py is structured that way,
    # or if agents are initialized within the run_trip_planner_chat function.
    # A more robust way is to have a clear reset function for the agent setup.
    # For now, the main.py creates agents fresh each time it's called via run_trip_planner_chat

    # AutoGen's initiate_chat is blocking. To prevent Gradio from freezing,
    # run it in a separate thread.
    # However, directly getting the "final result" from a threaded AutoGen chat is tricky
    # without modifying AutoGen's core or adding specific callbacks/queues.
    # For this example, we'll capture all stdout and try to parse the final report.

    try:
        # Ensure human_input_mode is 'NEVER' or 'TERMINATE' for UserProxyAgent if running non-interactively.
        # In our main.py, User_Proxy is 'TERMINATE', which is fine.
        autogen_main_module.run_trip_planner_chat(initial_request)
    except Exception as e:
        conversation_log_list.append(f"An error occurred: {str(e)}\n")
    finally:
        sys.stdout = old_stdout # Restore stdout
        full_log = captured_output.getvalue()
        conversation_log_list.append(full_log) # Add the full log

    # Try to extract the final itinerary (this is brittle, better if agent saves it)
    final_itinerary_text = "Could not automatically extract final itinerary. See full log."
    log_content_for_search = "\n".join(conversation_log_list) # Search in the captured log

    # Look for markers or the typical structure of the formatted itinerary
    # This depends heavily on the Itinerary_Compiler_Agent's final output format.
    # If `format_day_by_day_itinerary` always starts with "**Trip Title**"
    # and ends with "Disclaimer:", we can use that.

    # A better approach: modify Itinerary_Compiler_Agent or User_Proxy to explicitly
    # store the final formatted itinerary in a shared variable or return it.
    # For example, User_Proxy could have a `self.final_plan = None` and it's set when
    # it receives the final message containing the formatted itinerary.

    # Simple extraction attempt:
    if "Disclaimer: This is a suggested itinerary." in log_content_for_search:
        # Find the last occurrence of a potential start marker for the formatted plan
        # This is very heuristic.
        potential_starts = ["**", "Trip Title:", "Your Trip Itinerary"]
        best_start_index = -1
        for ps in potential_starts:
            idx = log_content_for_search.rfind(ps)
            if idx != -1:
                if best_start_index == -1 or idx > best_start_index: # Try to get the latest one
                    # Check if "Disclaimer" comes after this potential start
                    disclaimer_idx = log_content_for_search.rfind("Disclaimer: This is a suggested itinerary.")
                    if disclaimer_idx > idx:
                         best_start_index = idx
        
        if best_start_index != -1:
            end_index = log_content_for_search.rfind("Disclaimer: This is a suggested itinerary.") + len("Disclaimer: This is a suggested itinerary.")
            final_itinerary_text = log_content_for_search[best_start_index : end_index].strip()
        else: # Fallback if start marker not found but disclaimer is
            disclaimer_idx = log_content_for_search.rfind("Disclaimer: This is a suggested itinerary.")
            # Try to find a reasonable start before disclaimer; this is very rough
            start_search_area = log_content_for_search[max(0, disclaimer_idx - 2000):disclaimer_idx] # Search in 2000 chars before
            temp_start = start_search_area.rfind("--- Day 1:") # Heuristic
            if temp_start != -1:
                final_itinerary_text = start_search_area[temp_start:] + log_content_for_search[disclaimer_idx : disclaimer_idx + len("Disclaimer: This is a suggested itinerary.")]
            

    return final_itinerary_text, "\n".join(conversation_log_list)


def trip_planning_interface(request):
    # This function will be called by Gradio.
    # It needs to run the AutoGen logic and return results.
    # Since AutoGen is blocking and can take time, consider threading for responsiveness.
    # For this example, we'll run it directly, Gradio will show "loading".
    
    # Using a global list for logs for simplicity in this example.
    # More robust solutions would involve instance-based logging or queues for threaded operations.
    global conversation_log_list
    conversation_log_list = [] # Clear previous logs for new request

    final_plan, full_log = capture_and_run_autogen(request)
    return final_plan, full_log

# --- Gradio Interface Definition ---
with gr.Blocks(theme=gr.themes.Soft()) as demo:
    gr.Markdown("# AI Agentic Trip Planner")
    gr.Markdown("Enter your trip preferences below and let the AI agents plan your itinerary!")

    with gr.Row():
        with gr.Column(scale=1):
            trip_request_input = gr.Textbox(
                label="Your Trip Request",
                placeholder="e.g., A 10-day cultural trip to Japan for 2 people in autumn, mid-range budget, interested in temples, food, and nature.",
                lines=5
            )
            submit_button = gr.Button("Plan My Trip!", variant="primary")
        
        with gr.Column(scale=2):
            gr.Markdown("### Generated Itinerary")
            itinerary_output = gr.Markdown("Your itinerary will appear here...") # Using Markdown for rich text
            
    with gr.Accordion("Show Full Agent Interaction Log", open=False):
        log_output = gr.Textbox(label="Agent Interaction Log", lines=20, interactive=False)

    submit_button.click(
        fn=trip_planning_interface,
        inputs=trip_request_input,
        outputs=[itinerary_output, log_output]
    )
    
    gr.Markdown("---")
    gr.Markdown("Powered by AutoGen, Groq, and Gradio. Project by [Your Name/Student Project].")
    gr.Markdown("Disclaimer: This is an AI-generated plan. Verify all details before making bookings. Tavily API used for web search if enabled.")

if __name__ == "__main__":
    print("Starting Gradio UI for AI Trip Planner...")
    print("Ensure your .env file is configured with API keys.")
    if not os.path.exists(os.path.join(os.path.dirname(__file__), '.env')):
        print("WARNING: .env file not found in the project root. API keys might not be loaded.")
    demo.launch(share=False) # Set share=True to create a temporary public link (use with caution)
