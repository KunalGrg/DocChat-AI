import os
import requests
import logging
from typing import Optional

# --------------------------------------------------
# Logging Configuration
# --------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --------------------------------------------------
# Ollama Configuration
# --------------------------------------------------
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_GENERATE_URL = f"{OLLAMA_BASE_URL}/api/generate"
OLLAMA_TAGS_URL = f"{OLLAMA_BASE_URL}/api/tags"

DEFAULT_MODEL = os.getenv("OLLAMA_DEFAULT_MODEL", "llama3")


# --------------------------------------------------
# Model Selection
# --------------------------------------------------
def select_available_model() -> str:
    """
    Select an available Ollama model.
    Priority:
    1. DEFAULT_MODEL if installed
    2. First available model
    3. Fallback to DEFAULT_MODEL
    """
    try:
        response = requests.get(OLLAMA_TAGS_URL, timeout=5)
        response.raise_for_status()

        models = response.json().get("models", [])
        if not models:
            logger.warning("No models returned from Ollama. Using default model.")
            return DEFAULT_MODEL

        model_names = [m.get("name") for m in models if "name" in m]

        if DEFAULT_MODEL in model_names:
            return DEFAULT_MODEL

        logger.warning(
            f"Default model '{DEFAULT_MODEL}' not found. Using '{model_names[0]}' instead."
        )
        return model_names[0]

    except Exception as e:
        logger.error(f"Failed to fetch available models: {e}")
        return DEFAULT_MODEL


# --------------------------------------------------
# Prompt Construction
# --------------------------------------------------
def construct_prompt(document_text: str, question: str) -> str:
    """
    Build the LLM prompt with strict document grounding.
    """
    return f"""
Answer the user's question strictly using the provided document context.
If the answer is not present, respond exactly with:
"The document does not contain this information."

Document:
{document_text}

Question:
{question}
""".strip()


# --------------------------------------------------
# Query Local LLM (Ollama)
# --------------------------------------------------
def query_llm(
    document_text: str,
    question: str,
    model_name: Optional[str] = None,
) -> str:
    """
    Send a request to the local Ollama LLM and return the response text.
    """

    if not model_name:
        model_name = select_available_model()

    prompt = construct_prompt(document_text, question)

    payload = {
        "model": model_name,
        "prompt": prompt,
        "stream": False,
    }

    try:
        response = requests.post(
            OLLAMA_GENERATE_URL,
            json=payload,
            timeout=60,
        )
        response.raise_for_status()

        result = response.json()
        return result.get("response", "No response text found.")

    except requests.exceptions.ConnectionError:
        logger.error("Could not connect to Ollama service.")
        return (
            "Error: Could not connect to local Ollama instance at http://localhost:11434. "
            "Please ensure Ollama is running."
        )

    except requests.exceptions.Timeout:
        logger.error("LLM request timed out.")
        return "Error: The request to the local LLM timed out."

    except Exception as e:
        logger.exception("Unexpected error while querying LLM.")
        return f"Error querying LLM: {str(e)}"