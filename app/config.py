import os
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=dotenv_path)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

# Define the OAI_CONFIG_LIST for AutoGen
OAI_CONFIG_LIST_GROQ = [
    {
        "model": "llama3-70b-8192", # Powerful model for planning and complex reasoning
        "api_key": GROQ_API_KEY,
        "base_url": "https://api.groq.com/openai/v1",
        "api_type": "openai", 
    },
    {
        "model": "llama3-8b-8192", # Fast model for simpler tasks
        "api_key": GROQ_API_KEY,
        "base_url": "https://api.groq.com/openai/v1",
        "api_type": "openai",
    }
]

# Configuration for the agents, specifying which LLM config to use
# use the more powerful model by default for most agents
LLM_CONFIG_GROQ_70B = {
    "config_list": [config for config in OAI_CONFIG_LIST_GROQ if config["model"] == "llama3-70b-8192"],
    "cache_seed": 42,  # For reproducibility 
    # "temperature": 0.6, # Adjust creativity/determinism
}

LLM_CONFIG_GROQ_8B = {
    "config_list": [config for config in OAI_CONFIG_LIST_GROQ if config["model"] == "llama3-8b-8192"],
    "cache_seed": 42,
    # "temperature": 0.5,
}

# Ensure at least one config is present
if not LLM_CONFIG_GROQ_70B["config_list"]:
    print("Warning: llama3-70b-8192 configuration not found. Falling back.")
    LLM_CONFIG_GROQ_70B["config_list"] = OAI_CONFIG_LIST_GROQ
if not LLM_CONFIG_GROQ_8B["config_list"]:
    print("Warning: llama3-8b-8192 configuration not found. Falling back.")
    LLM_CONFIG_GROQ_8B["config_list"] = OAI_CONFIG_LIST_GROQ

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not found in .env file. Please add it.")

TAVILY_ENABLED = bool(TAVILY_API_KEY)