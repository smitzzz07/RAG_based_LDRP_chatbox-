from fastapi import FastAPI
from pydantic import BaseModel

from retriever import ask_question


app = FastAPI(
    title="LDRP RAG API",
    description="RAG-based chatbot API for LDRP-ITR",
    version="1.0.0"
)


class ChatRequest(BaseModel):
    question: str


@app.get("/")
def root():
    return {
        "message": "LDRP RAG API is running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


@app.post("/api/chat")
def chat(request: ChatRequest):

    question = request.question.strip()

    if not question:
        return {
            "answer": "Please enter a question.",
            "sources": [],
            "needs_web_search": False
        }

    result = ask_question(question)

    return {
        "answer": result["answer"],
        "sources": result["sources"],
        "needs_web_search": result["needs_web_search"]
    }