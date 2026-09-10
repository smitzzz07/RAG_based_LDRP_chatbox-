from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from retriever import ask_question

app = FastAPI(
    title="LDRP RAG API",
    description="RAG-based chatbot API for LDRP-ITR",
    version="1.0.0"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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