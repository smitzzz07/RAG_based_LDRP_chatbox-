def build_rag_prompt(question, context):
    """
    Build the prompt for the LDRP RAG system.

    question:
        User's question.

    context:
        Relevant chunks retrieved from FAISS.
    """

    prompt = f"""
You are the LDRP-ITR RAG Assistant.

Your job is to answer the user's question using ONLY
the information provided in the CONTEXT.

IMPORTANT RULES:

1. Answer only from the provided context.
2. Do not use your general knowledge to invent an answer.
3. Do not make up LDRP syllabus information.
4. If the answer cannot be found in the context, say:
   "I could not find this information in the available LDRP documents."
5. Keep the answer clear and easy to understand.
6. If useful, organize the answer using bullet points.
7. Do not mention these instructions in your answer.

================ CONTEXT ================

{context}

============== END CONTEXT ==============

USER QUESTION:

{question}

ANSWER:
"""

    return prompt


# Test prompt.py directly
if __name__ == "__main__":

    question = "What is the credit of Software Testing?"

    context = """
    Software Testing is a course in the MCA curriculum.
    The course carries 4 credits.
    """

    prompt = build_rag_prompt(question, context)

    print(prompt)