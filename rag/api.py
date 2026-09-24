from datetime import datetime

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from rag import models
from rag.auth import get_current_user, router as auth_router
from rag.database import Base, engine, get_db
from rag.retriever import ask_question
from rag.schemas import (
    ChatMessageResponse,
    ChatRequest,
    ConversationDetail,
    ConversationSummary,
)

# Create database tables if they do not exist.
Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="LDRP RAG API",
    description="RAG-based chatbot API for LDRP-ITR",
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth_router)


@app.get("/")
def root():
    return {"message": "LDRP RAG API is running"}


@app.get("/health")
def health():
    return {"status": "healthy"}


def make_conversation_title(question: str) -> str:
    """Create a short sidebar title from the first user question."""
    title = " ".join(question.strip().split())

    if len(title) <= 52:
        return title

    return title[:52].rstrip() + "..."


def get_user_conversation(
    conversation_id: int,
    user_id: int,
    db: Session,
):
    conversation = (
        db.query(models.Conversation)
        .filter(
            models.Conversation.id == conversation_id,
            models.Conversation.user_id == user_id,
        )
        .first()
    )

    if not conversation:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found.",
        )

    return conversation


@app.post("/api/chat")
def chat(
    request: ChatRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    question = request.question.strip()

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Please enter a question.",
        )

    # Reuse the selected conversation, or create one automatically.
    if request.conversation_id is not None:
        conversation = get_user_conversation(
            request.conversation_id,
            current_user.id,
            db,
        )
    else:
        conversation = models.Conversation(
            user_id=current_user.id,
            title=make_conversation_title(question),
        )

        db.add(conversation)
        db.commit()
        db.refresh(conversation)

    # Save user message before generating the answer.
    user_message = models.Message(
        conversation_id=conversation.id,
        role="user",
        content=question,
        sources=[],
    )

    db.add(user_message)
    db.commit()

    try:
        result = ask_question(question)
    except Exception as exc:
        # Don't leave a half-broken conversation title/update.
        raise HTTPException(
            status_code=500,
            detail=f"RAG processing failed: {exc}",
        )

    answer = result.get(
        "answer",
        "Unable to generate an answer.",
    )

    sources = result.get("sources", []) or []

    assistant_message = models.Message(
        conversation_id=conversation.id,
        role="assistant",
        content=answer,
        sources=sources,
    )

    db.add(assistant_message)

    # Make recently used conversations appear first.
    conversation.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(assistant_message)

    return {
        "conversation_id": conversation.id,
        "answer": answer,
        "sources": sources,
        "needs_web_search": result.get(
            "needs_web_search",
            False,
        ),
    }


@app.get(
    "/api/chat/history",
    response_model=list[ConversationSummary],
)
def chat_history(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conversations = (
        db.query(models.Conversation)
        .filter(
            models.Conversation.user_id == current_user.id
        )
        .order_by(
            models.Conversation.updated_at.desc()
        )
        .all()
    )

    return conversations


@app.get(
    "/api/chat/{conversation_id}",
    response_model=ConversationDetail,
)
def get_chat(
    conversation_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conversation = get_user_conversation(
        conversation_id,
        current_user.id,
        db,
    )

    return ConversationDetail(
        id=conversation.id,
        title=conversation.title,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        messages=[
            ChatMessageResponse(
                id=message.id,
                role=message.role,
                content=message.content,
                sources=message.sources or [],
                created_at=message.created_at,
            )
            for message in conversation.messages
        ],
    )


@app.delete("/api/chat/{conversation_id}")
def delete_chat(
    conversation_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conversation = get_user_conversation(
        conversation_id,
        current_user.id,
        db,
    )

    db.delete(conversation)
    db.commit()

    return {
        "message": "Conversation deleted successfully.",
        "conversation_id": conversation_id,
    }
