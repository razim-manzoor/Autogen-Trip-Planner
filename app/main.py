import logging
from io import StringIO
import autogen
from app.agents import (
    create_user_proxy,
    create_requirements_analyst,
    create_destination_researcher,
    create_activity_planner,
    create_logistics_coordinator,
    create_itinerary_compiler,
    create_review_agent,
    register_functions_for_user_proxy,
)
from app.config import LLM_CONFIG_GROQ_70B

# Set up module‐wide logger
logger = logging.getLogger("trip_planner")
handler = logging.StreamHandler(StringIO())
handler.setLevel(logging.INFO)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

def run_trip_planner_chat(initial_request: str) -> str:
    # Instantiate agents...
    user_proxy = create_user_proxy()
    # register tools
    register_functions_for_user_proxy(user_proxy)
    # build groupchat & manager
    group = autogen.GroupChat(
        agents=[user_proxy, create_requirements_analyst(), create_destination_researcher(),
                create_activity_planner(), create_logistics_coordinator(),
                create_itinerary_compiler(), create_review_agent()],
        messages=[],
        max_round=35,
        speaker_selection_method="auto",
        send_introductions=True,
    )
    mgr = autogen.GroupChatManager(groupchat=group, llm_config=LLM_CONFIG_GROQ_70B)
    user_proxy.initiate_chat(mgr, message=initial_request)

    # run until user_proxy terminates
    mgr.run()
    # extract final formatted itinerary by sentinel
    full_log = handler.stream.getvalue()
    msgs = [m.get("content","") for m in group.messages if isinstance(m.get("content"), str)]
    for content in reversed(msgs):
        if "__END_ITINERARY__" in content:
            return content.split("__END_ITINERARY__")[0]
    return "Error: itinerary not found."
