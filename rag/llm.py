import os
import time

from dotenv import load_dotenv
from google import genai


# ==================================================
# 1. Load environment variables
# ==================================================

load_dotenv()


# ==================================================
# 2. Get Gemini API key
# ==================================================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError(
        "GEMINI_API_KEY was not found.\n"
        "Please create a .env file in the project root "
        "and add GEMINI_API_KEY=your_key"
    )


# ==================================================
# 3. Create Gemini client
# ==================================================

client = genai.Client(
    api_key=GEMINI_API_KEY
)


# ==================================================
# 4. Gemini model
# ==================================================

MODEL_NAME = "gemini-3.6-flash"


# ==================================================
# 5. Generate answer
# ==================================================

def generate_answer(prompt):
    """
    Send the prompt to Gemini and return the answer.

    Handles:
    - 503 temporary server errors
    - 429 quota/rate-limit errors
    - empty responses
    - other Gemini errors
    """

    max_retries = 3

    for attempt in range(1, max_retries + 1):

        try:

            print(
                f"\n📡 Gemini request "
                f"(attempt {attempt}/{max_retries})..."
            )

            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt
            )

            if response.text:

                print("✅ Gemini response received")

                return response.text.strip()

            print("⚠️ Gemini returned an empty response.")

            return (
                "Gemini returned an empty response. "
                "Please try again."
            )

        except Exception as e:

            error_text = str(e)

            print("\n⚠️ Gemini request failed:")
            print(f"{type(e).__name__}: {e}")

            # ==================================================
            # 429 - Quota / Rate Limit
            # ==================================================

            if (
                "429" in error_text
                or "RESOURCE_EXHAUSTED" in error_text
            ):

                print(
                    "\n🚫 Gemini API quota has been exhausted."
                )

                print(
                    "Please wait for the quota to reset "
                    "or use a project with available quota."
                )

                return (
                    "The AI generation service has reached "
                    "its current Gemini API quota. "
                    "Your question was successfully processed "
                    "and the relevant sources were retrieved. "
                    "Please try again after the quota resets."
                )

            # ==================================================
            # 503 - Temporary Gemini server problem
            # ==================================================

            if (
                "503" in error_text
                or "UNAVAILABLE" in error_text
            ):

                if attempt < max_retries:

                    wait_time = attempt * 3

                    print(
                        f"⏳ Gemini temporarily unavailable. "
                        f"Retrying in {wait_time} seconds..."
                    )

                    time.sleep(wait_time)

                    continue

                return (
                    "Gemini is temporarily unavailable. "
                    "Please try again shortly."
                )

            # ==================================================
            # Other errors
            # ==================================================

            return (
                "Unable to generate an answer from "
                "Gemini at the moment."
            )

    # ==================================================
    # All retries failed
    # ==================================================

    return (
        "Gemini is temporarily unavailable. "
        "Please try again."
    )


# ==================================================
# 6. Test Gemini
# ==================================================

if __name__ == "__main__":

    test_prompt = """
You are an academic assistant.

Explain Retrieval-Augmented Generation (RAG)
in simple words in 3 sentences.
"""

    answer = generate_answer(test_prompt)

    print("\n")
    print("=" * 50)
    print("GEMINI RESPONSE")
    print("=" * 50)
    print(answer)
    print("=" * 50)