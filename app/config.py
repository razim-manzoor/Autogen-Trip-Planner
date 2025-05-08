import os
from dotenv import load_dotenv, find_dotenv
from typing import List, Dict, Any

# Load .env reliably
dotenv_path = find_dotenv()
load_dotenv(dotenv_path)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

if not GROQ_API_KEY:
    raise EnvironmentError("GROQ_API_KEY not set in environment.")

# Base config list
OAI_CONFIG_LIST_GROQ: List[Dict[str, Any]] = [
    {
        "model": "llama3-70b-8192",
        "api_key": GROQ_API_KEY,
        "base_url": "https://api.groq.com/openai/v1",
        "api_type": "openai",
        "request_timeout": 60,     # 60s timeout on every call
    },
    {
        "model": "llama3-8b-8192",
        "api_key": GROQ_API_KEY,
        "base_url": "https://api.groq.com/openai/v1",
        "api_type": "openai",
        "request_timeout": 60,
    }
]

def _pick_config(model_name: str):
    cfgs = [c for c in OAI_CONFIG_LIST_GROQ if c["model"] == model_name]
    if not cfgs:
        raise ValueError(f"No config for model {model_name}")
    return cfgs

LLM_CONFIG_GROQ_70B = {
    "config_list": _pick_config("llama3-70b-8192"),
    "cache_seed": 42,
}

LLM_CONFIG_GROQ_8B = {
    "config_list": _pick_config("llama3-8b-8192"),
    "cache_seed": 42,
}

TAVILY_ENABLED = bool(TAVILY_API_KEY)
