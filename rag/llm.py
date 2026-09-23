import os
import time

from dotenv import load_dotenv
from google import genai
from groq import Groq


# ==================================================
# 1. Load environment variables
# ==================================================

load_dotenv()


# ==================================================
# 2. API Keys
# ==================================================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")


# ==================================================
# 3. Gemini Configuration
# ==================================================

GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.6-flash"
)


# ==================================================
# 4. Groq Configuration
# ==================================================

GROQ_MODEL = os.getenv(
    "GROQ_MODEL",
    "llama-3.3-70b-versatile"
)


# ==================================================
# 5. OpenRouter Configuration
# ==================================================

OPENROUTER_MODEL = os.getenv(
    "OPENROUTER_MODEL",
    "openai/gpt-oss-20b"
)


# ==================================================
# 6. Create clients
# ==================================================

gemini_client = None
groq_client = None


if GEMINI_API_KEY:
    gemini_client = genai.Client(
        api_key=GEMINI_API_KEY
    )


if GROQ_API_KEY:
    groq_client = Groq(
        api_key=GROQ_API_KEY
    )


# ==================================================
# 7. Generate with Gemini
# ==================================================

def generate_with_gemini(prompt):
    """
    Generate an answer using Gemini.

    Gemini is the primary LLM.
    """

    if not gemini_client:
        raise RuntimeError(
            "GEMINI_API_KEY is not configured."
        )

    max_retries = 3

    for attempt in range(1, max_retries + 1):

        try:

            print(
                f"\n🟣 Gemini request "
                f"(attempt {attempt}/{max_retries})..."
            )

            response = gemini_client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt
            )

            if response.text:

                print("✅ Gemini response received")

                return response.text.strip()

            raise RuntimeError(
                "Gemini returned an empty response."
            )

        except Exception as e:

            error_text = str(e)

            print(
                f"\n⚠️ Gemini failed:"
                f"\n{type(e).__name__}: {e}"
            )

            # ------------------------------------------
            # Rate limit / quota
            # ------------------------------------------

            if (
                "429" in error_text
                or "RESOURCE_EXHAUSTED" in error_text
            ):

                print(
                    "🚫 Gemini quota/rate limit detected."
                )

                # Don't retry quota errors.
                # Move directly to Groq.
                raise

            # ------------------------------------------
            # Temporary server error
            # ------------------------------------------

            if (
                "503" in error_text
                or "UNAVAILABLE" in error_text
                or "500" in error_text
            ):

                if attempt < max_retries:

                    wait_time = attempt * 2

                    print(
                        f"⏳ Gemini temporarily unavailable."
                        f" Retrying in {wait_time}s..."
                    )

                    time.sleep(wait_time)

                    continue

                raise

            # ------------------------------------------
            # Any other error
            # ------------------------------------------

            raise

    raise RuntimeError(
        "Gemini failed after all retries."
    )


# ==================================================
# 8. Generate with Groq
# ==================================================

def generate_with_groq(prompt):
    """
    Generate an answer using Groq.

    Groq is the first fallback after Gemini.
    """

    if not groq_client:
        raise RuntimeError(
            "GROQ_API_KEY is not configured."
        )

    print("\n🟢 Trying Groq...")

    response = groq_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.2,
        max_tokens=2048,
    )

    answer = response.choices[0].message.content

    if not answer:
        raise RuntimeError(
            "Groq returned an empty response."
        )

    print("✅ Groq response received")

    return answer.strip()


# ==================================================
# 9. Generate with OpenRouter
# ==================================================

def generate_with_openrouter(prompt):
    """
    Generate an answer using OpenRouter.

    OpenRouter is the second LLM fallback.
    """

    if not OPENROUTER_API_KEY:
        raise RuntimeError(
            "OPENROUTER_API_KEY is not configured."
        )

    print("\n🔵 Trying OpenRouter...")

    import requests

    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:5173",
        "X-Title": "LDRP-ITR AI Assistant",
    }

    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.2,
        "max_tokens": 2048,
    }

    response = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=60
    )

    response.raise_for_status()

    data = response.json()

    answer = (
        data
        .get("choices", [{}])[0]
        .get("message", {})
        .get("content")
    )

    if not answer:
        raise RuntimeError(
            "OpenRouter returned an empty response."
        )

    print("✅ OpenRouter response received")

    return answer.strip()


# ==================================================
# 10. Main LLM fallback system
# ==================================================

def generate_answer(prompt):
    """
    Automatic multi-LLM fallback system.

    Priority:

        1. Gemini
        2. Groq
        3. OpenRouter

    If all providers fail, raise an exception so the
    retriever can decide what fallback response/context
    should be returned.
    """

    print("\n")
    print("=" * 60)
    print("🤖 LLM FALLBACK SYSTEM")
    print("=" * 60)

    # ==================================================
    # PRIMARY: GEMINI
    # ==================================================

    if GEMINI_API_KEY:

        try:

            answer = generate_with_gemini(prompt)

            print("=" * 60)
            print("🟣 PROVIDER USED: GEMINI")
            print("=" * 60)

            return answer

        except Exception as e:

            print(
                f"\n⚠️ Gemini unavailable."
                f"\nReason: {e}"
            )

    else:

        print(
            "\n⚠️ GEMINI_API_KEY not configured."
        )


    # ==================================================
    # FALLBACK 1: GROQ
    # ==================================================

    if GROQ_API_KEY:

        try:

            answer = generate_with_groq(prompt)

            print("=" * 60)
            print("🟢 PROVIDER USED: GROQ")
            print("=" * 60)

            return answer

        except Exception as e:

            print(
                f"\n⚠️ Groq unavailable."
                f"\nReason: {e}"
            )

    else:

        print(
            "\n⚠️ GROQ_API_KEY not configured."
        )


    # ==================================================
    # FALLBACK 2: OPENROUTER
    # ==================================================

    if OPENROUTER_API_KEY:

        try:

            answer = generate_with_openrouter(prompt)

            print("=" * 60)
            print("🔵 PROVIDER USED: OPENROUTER")
            print("=" * 60)

            return answer

        except Exception as e:

            print(
                f"\n⚠️ OpenRouter unavailable."
                f"\nReason: {e}"
            )

    else:

        print(
            "\n⚠️ OPENROUTER_API_KEY not configured."
        )


    # ==================================================
    # ALL PROVIDERS FAILED
    # ==================================================

    print("=" * 60)
    print("❌ ALL LLM PROVIDERS FAILED")
    print("=" * 60)

    raise RuntimeError(
        "All configured LLM providers are currently unavailable."
    )


# ==================================================
# 11. Test
# ==================================================

if __name__ == "__main__":

    test_prompt = """
You are an academic assistant.

Explain Retrieval-Augmented Generation (RAG)
in simple words in 3 sentences.
"""

    try:

        answer = generate_answer(test_prompt)

        print("\n")
        print("=" * 60)
        print("FINAL RESPONSE")
        print("=" * 60)
        print(answer)
        print("=" * 60)

    except Exception as e:

        print("\n")
        print("=" * 60)
        print("❌ ALL PROVIDERS FAILED")
        print("=" * 60)
        print(e)
        print("=" * 60)