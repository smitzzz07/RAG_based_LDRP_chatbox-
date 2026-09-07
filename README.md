# 🎓 LDRP RAG Assistant

An AI-powered Retrieval-Augmented Generation (RAG) system for querying LDRP/KSV academic documents.

The system allows students to ask questions about academic syllabus documents and retrieves relevant information before generating an answer.

---

## 🚀 Features

- 📄 PDF document loading
- 🧹 Text cleaning
- ✂️ Intelligent document chunking
- 🧠 Text embeddings
- 🔎 Semantic vector search
- ⚡ FAISS vector database
- 🤖 LLM-based answer generation
- 📚 Source-aware answers
- 🔐 Authentication
- 💬 Chat interface
- 📊 Admin document management

---

# 🏗️ RAG Architecture

```text
                PDF DOCUMENT
                     │
                     ▼
              ┌─────────────┐
              │ PDF Loader  │
              │  PyMuPDF    │
              └──────┬──────┘
                     │
                     ▼
              Extracted Text
                     │
                     ▼
              ┌─────────────┐
              │   Cleaner   │
              └──────┬──────┘
                     │
                     ▼
                Clean Text
                     │
                     ▼
              ┌─────────────┐
              │   Chunker   │
              └──────┬──────┘
                     │
                     ▼
                  Chunks
                     │
                     ▼
              ┌─────────────┐
              │  Embedding  │
              │    Model    │
              └──────┬──────┘
                     │
                     ▼
                 Vectors
                     │
                     ▼
              ┌─────────────┐
              │    FAISS    │
              │ Vector Store│
              └──────┬──────┘
                     │
                     │
USER QUESTION ────────┘
      │
      ▼
Question Embedding
      │
      ▼
Similarity Search
      │
      ▼
Relevant Chunks
      │
      ▼
     LLM
      │
      ▼
Final Answer