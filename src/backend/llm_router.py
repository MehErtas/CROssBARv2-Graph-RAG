from providers.openai_provider import call_openai
from providers.genai_provider import call_gemini
from providers.anthropic_provider import call_anthropic
from providers.mistral_provider import call_mistral
from providers.local_provider import call_local
from providers.openrouter_provider import call_openrouter
import os

def get_key(api_key: Optional[str], env_var: str) -> str:
    """
    Prefer user-provided api_key; fall back to env var.
    Raise a helpful error if neither exists.
    """
    key = (api_key or "").strip() or (os.getenv(env_var) or "").strip()
    if not key:
        raise ValueError(f"Missing API key. Provide api_key or set {env_var} in environment.")
    return key

def generate_response(model: str, prompt: str, api_key: str) -> str:
    if model.startswith("chatgpt") or model.startswith("o"):
        api_key = get_key(api_key, "OPENAI_API_KEY")
        return call_openai(model, prompt, api_key)
    elif model.startswith("gemini"):
        api_key = get_key(api_key, "GEMINI_API_KEY")
        return call_gemini(model, prompt, api_key)
    elif model.startswith("claude"):
        api_key = get_key(api_key, "ANTHROPIC_API_KEY")
        return call_anthropic(model, prompt, api_key)
    elif model.startswith("mistral"):
        api_key = get_key(api_key, "MISTRAL_API_KEY")
        return call_mistral(model, prompt, api_key)
    elif model.startswith("local"):
        return call_local(model, prompt)
    elif model.startswith("llama"):
        return call_local(model, prompt)
    elif model.startswith("deepseek"):
        return call_openrouter(model, prompt)
    else:
        raise ValueError(f"Unsupported model: {model}")
