
import json
import os
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


# Local Ollama API address.
OLLAMA_URL = os.getenv(
    "OLLAMA_URL",
    "http://localhost:11434/api/generate"
)

# Model to use for CRM extraction.
MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")

# Track token usage reported by Ollama.
TOKEN_USAGE = {
    "input_tokens": 0,
    "output_tokens": 0
}

# Ollama runs locally; these constants do not represent
# electricity, hardware or other operating costs.
INPUT_COST_PER_MILLION_TOKENS = 0.0
OUTPUT_COST_PER_MILLION_TOKENS = 0.0


def generate_text(prompt: str) -> str:
    """
    Send a prompt to the local Ollama model
    and return its generated text.

    Also records token usage when Ollama provides it.
    """

    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0
        }
    }

    request = Request(
        OLLAMA_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json"
        },
        method="POST"
    )

    try:
        with urlopen(request, timeout=180) as response:
            response_data = json.loads(
                response.read().decode("utf-8")
            )

    except HTTPError as error:
        error_body = error.read().decode(
            "utf-8",
            errors="replace"
        )

        raise RuntimeError(
            f"Ollama API returned HTTP {error.code}: "
            f"{error_body}"
        ) from error

    except URLError as error:
        raise RuntimeError(
            "Could not connect to Ollama. "
            "Make sure Ollama is running."
        ) from error

    generated_text = response_data.get("response")

    if not generated_text:
        raise ValueError(
            "Ollama returned an empty response."
        )

    # Ollama reports token counts for the prompt
    # and generated response.
    TOKEN_USAGE["input_tokens"] += (
        response_data.get("prompt_eval_count") or 0
    )

    TOKEN_USAGE["output_tokens"] += (
        response_data.get("eval_count") or 0
    )

    return generated_text


def get_token_usage() -> dict:
    """Return a copy of accumulated token usage."""

    return TOKEN_USAGE.copy()


def calculate_estimated_cost() -> float:
    """
    Return zero API cost because inference runs locally.

    This does not include electricity or hardware costs.
    """

    return 0.0


def reset_token_usage() -> None:
    """Reset token counters before a new processing run."""

    TOKEN_USAGE["input_tokens"] = 0
    TOKEN_USAGE["output_tokens"] = 0


if __name__ == "__main__":

    test_prompt = """
    Return a JSON object with exactly one field:
    "message": "Ollama CRM assistant connection successful."
    """

    try:
        result = generate_text(test_prompt)

        print("\nOllama response:")
        print(result)

        print("\nToken usage:")
        print(get_token_usage())

    except Exception as error:
        print("\nOllama connection failed.")
        print("Error:", error)
