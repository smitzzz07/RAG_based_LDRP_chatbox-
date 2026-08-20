import os

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
    """

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt
    )

    return response.text


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