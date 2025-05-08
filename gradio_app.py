import gradio as gr
import sys
import os
from io import StringIO

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'app')))

try:
    from app import main as autogen_main_module
    # We no longer need to import user_proxy here for reset, as agents are created fresh.
except ImportError as e:
    print(f"Critical Error: Could not import AutoGen modules for Gradio: {e}")
    print("Ensure 'app' directory is in the same directory as gradio_app.py and contains __init__.py if necessary.")
    autogen_main_module = None # Prevent app from running if core module fails

# --- Global variable to store conversation log (for stdout capture) ---
# This is a simple way, for more complex apps, consider state management
# Note: This is only for the *full stdout log*, not the direct itinerary.
conversation_log_list = []

def capture_and_run_autogen(initial_request: str):
    global conversation_log_list
    conversation_log_list = ["Processing your request... This might take several minutes.\n(UI will be unresponsive during this time)\n\n"]

    final_itinerary_text = "Error: Trip planning did not complete or failed to extract itinerary."
    full_log_output = ""

    if not autogen_main_module:
        error_msg = "AutoGen module not loaded. Cannot process request."
        conversation_log_list.append(error_msg)
        return error_msg, "\n".join(conversation_log_list)

    # Capture stdout for the detailed log
    old_stdout = sys.stdout
    sys.stdout = captured_output = StringIO()

    try:
        # The run_trip_planner_chat function now directly returns the final itinerary
        final_itinerary_text = autogen_main_module.run_trip_planner_chat(initial_request)
    except Exception as e:
        error_msg = f"An error occurred during AutoGen execution: {str(e)}"
        print(error_msg) # Also print to console
        conversation_log_list.append(error_msg + "\n")
        # final_itinerary_text remains the error message initialized above
    finally:
        sys.stdout = old_stdout # Restore stdout
        full_log_output = captured_output.getvalue()
        # Prepend earlier messages to the full log
        full_log_with_initial_msgs = "".join(conversation_log_list) + full_log_output
        # No need to append to conversation_log_list again, just use the combined string.

    # Check if the returned itinerary still indicates an error from the run_trip_planner_chat function itself
    if final_itinerary_text.startswith("Error:"):
        # Keep the error message as the main output if extraction failed internally
        pass # final_itinerary_text already holds the error
    elif not final_itinerary_text or not final_itinerary_text.strip():
        final_itinerary_text = "No itinerary was generated, or it was empty. Check the full log for details."

    return final_itinerary_text, full_log_with_initial_msgs


def trip_planning_interface(request: str):
    if not request or not request.strip():
        return "Please enter your trip request.", "No request provided."
    
    # Call the refactored function that directly returns the itinerary
    # and also captures the full log.
    final_plan, full_log = capture_and_run_autogen(request)
    return final_plan, full_log

# --- Gradio Interface Definition ---
with gr.Blocks(theme=gr.themes.Soft(), css=".gradio-container {max-width: 90% !important;}") as demo:
    gr.Markdown("# AI Agentic Trip Planner")
    gr.Markdown("Enter your trip preferences below and let the AI agents plan your itinerary! (Powered by AutoGen & Groq)")

    with gr.Row():
        with gr.Column(scale=1):
            trip_request_input = gr.Textbox(
                label="Your Trip Request",
                placeholder="e.g., A 10-day cultural trip to Kerala for 2 people in monsoon, mid-range budget, interested in historic location, food, and nature.",
                lines=5,
                elem_id="trip_request_input"
            )
            submit_button = gr.Button("Plan My Trip!", variant="primary", elem_id="submit_button_trip_planner")

        with gr.Column(scale=2):
            gr.Markdown("### Generated Itinerary")
            itinerary_output = gr.Markdown("Your itinerary will appear here...", elem_id="itinerary_output_markdown")

    with gr.Accordion("Show Full Agent Interaction Log", open=False):
        log_output = gr.Textbox(label="Agent Interaction Log (stdout capture)", lines=20, interactive=False, show_copy_button=True)

    submit_button.click(
        fn=trip_planning_interface,
        inputs=trip_request_input,
        outputs=[itinerary_output, log_output],
        api_name="plan_trip"
    )

    gr.Markdown("---")
    gr.Markdown("Project by Razim Manzoor, powered by AutoGen & Groq.")
    gr.Markdown("Disclaimer: This is an AI-generated plan. Verify all details before making bookings.")

if __name__ == "__main__":
    print("Starting Gradio UI for AI Trip Planner...")
    env_path_check = os.path.join(os.path.dirname(__file__), '.env')
    if not os.path.exists(env_path_check):
        print(f"WARNING: .env file not found at {env_path_check}. API keys might not be loaded if not set in environment.")
    elif autogen_main_module is None:
         print("CRITICAL: AutoGen module failed to load. Gradio application cannot function properly. Check console for import errors.")
    
    if autogen_main_module: # Only launch if core module is loaded
        demo.launch(share=False) # Set share=True for a temporary public link (use with caution)
    else:
        print("Gradio demo will not launch due to critical errors during initialization.")