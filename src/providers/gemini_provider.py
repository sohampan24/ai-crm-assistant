
import os
import re
import time
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types


PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

API_KEY = os.getenv("GEMINI_API_KEY")
MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")

# Keep requests safely below the free-tier limit of 5 requests/minute.
REQUEST_INTERVAL_SECONDS = 14

# Store token usage across all extraction calls in this run.
TOKEN_USAGE = {
    "input_tokens": 0,
    "output_tokens": 0
}

# Pricing is an editable estimate, not a live price lookup.
INPUT_COST_PER_MILLION_TOKENS = 0.0
OUTPUT_COST_PER_MILLION_TOKENS = 0.0

# Record the time of the last API request.
_LAST_REQUEST_TIME = 0.0


def wait_for_request_slot() -> None:
    """
    Ensure enough time has passed since the previous API request.
    """

    global _LAST_REQUEST_TIME

    elapsed = time.monotonic() - _LAST_REQUEST_TIME

    remaining = REQUEST_INTERVAL_SECONDS - elapsed

    if remaining > 0:
        print(
            f"Rate limit protection: "
            f"waiting {remaining:.1f} seconds..."
        )
        time.sleep(remaining)

    # Record the time immediately before sending the next request.
    _LAST_REQUEST_TIME = time.monotonic()


def get_retry_delay(error_message: str) -> float:
    """
    Extract Gemini's suggested retry delay from its error message.
    """

    # Example: Please retry in 40.7s
    match = re.search(
        r"retry in\s+([\d.]+)\s*s",
        error_message,
        re.IGNORECASE
    )

    if match:
        return float(match.group(1)) + 2

    # Example: 'retryDelay': '40s'
    match = re.search(
        r"retryDelay['\"]?\s*:\s*['\"]([\d.]+)s",
        error_message,
        re.IGNORECASE
    )

    if match:
        return float(match.group(1)) + 2

    # If Gemini gives no retry information, wait 60 seconds.
    return 60



def generate_text(prompt: str) -> str:
    """
    Send a prompt to Gemini and return its text response.
    Also records input and output token usage.
    """

    if not API_KEY:
        raise ValueError(
            "GEMINI_API_KEY is missing. Check your .env file."
        )

    client = genai.Client(api_key=API_KEY)

    max_attempts = 3

    retryable_errors = (
        "429",
        "500",
        "502",
        "503",
        "504",
        "RESOURCE_EXHAUSTED",
        "UNAVAILABLE"
    )

    for attempt in range(1, max_attempts + 1):

        try:
            wait_for_request_slot()

            response = client.models.generate_content(
                model=MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0,
                    response_mime_type="application/json"
                )
            )

            if not response.text:
                raise ValueError(
                    "Gemini returned an empty response."
                )

            usage = response.usage_metadata

            if usage:
                TOKEN_USAGE["input_tokens"] += (
                    usage.prompt_token_count or 0
                )
                TOKEN_USAGE["output_tokens"] += (
                    usage.candidates_token_count or 0
                )

            return response.text

        except Exception as error:
            error_message = str(error)
            error_upper = error_message.upper()

            is_retryable = any(
                code in error_upper
                for code in retryable_errors
            )

            if not is_retryable or attempt == max_attempts:
                raise

            if "429" in error_upper or "RESOURCE_EXHAUSTED" in error_upper:
                wait_seconds = get_retry_delay(error_message)

                if wait_seconds > 120:
                    raise RuntimeError(
                        f"Gemini quota limit reached. "
                        f"Retry requested after {wait_seconds:.0f} seconds. "
                        f"Try again after the quota resets."
                    ) from error

                error_type = "Gemini rate limit reached"

            else:
                wait_seconds = 10 * attempt
                error_type = "Temporary Gemini server error"

            print(
                f"{error_type}. "
                f"Retrying in {wait_seconds:.1f} seconds "
                f"(attempt {attempt}/{max_attempts})..."
            )

            time.sleep(wait_seconds)

    raise RuntimeError("Gemini request failed unexpectedly.")


def get_token_usage() -> dict:
    """Return a copy of accumulated token usage."""

    return TOKEN_USAGE.copy()


def calculate_estimated_cost() -> float:
    """
    Calculate estimated API cost using editable pricing constants.

    Both prices are expressed per million tokens.
    """

    input_cost = (
        TOKEN_USAGE["input_tokens"] / 1_000_000
    ) * INPUT_COST_PER_MILLION_TOKENS

    output_cost = (
        TOKEN_USAGE["output_tokens"] / 1_000_000
    ) * OUTPUT_COST_PER_MILLION_TOKENS

    return input_cost + output_cost


def reset_token_usage() -> None:
    """Reset usage counters before a new processing run."""

    TOKEN_USAGE["input_tokens"] = 0
    TOKEN_USAGE["output_tokens"] = 0


if __name__ == "__main__":

    test_prompt = (
        'Return a JSON object with one field named "message". '
        'Its value must be "Gemini CRM assistant connection successful."'
    )

    try:
        result = generate_text(test_prompt)

        print("\nGemini response:")
        print(result)

        print("\nToken usage:")
        print(get_token_usage())

        print(
            "Estimated API cost:",
            calculate_estimated_cost()
        )

    except Exception as error:
        print("\nGemini connection failed.")
        print("Error:", error)
