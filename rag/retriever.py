from pathlib import Path
import json

import faiss
from sentence_transformers import SentenceTransformer

from prompt import build_rag_prompt
from llm import generate_answer


# ==================================================
# PROJECT PATHS
# ==================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

VECTOR_DB_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "faiss.index"
)

CHUNKS_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "embeddings.json"
)


# ==================================================
# SETTINGS
# ==================================================

MODEL_NAME = "all-MiniLM-L6-v2"

TOP_K = 3

# FAISS uses L2 distance.
# Smaller distance = more similar.
RELEVANCE_THRESHOLD = 1.5


# ==================================================
# LOAD EMBEDDING MODEL
# ==================================================

print("Loading embedding model...")

model = SentenceTransformer(
    MODEL_NAME
)

print("✅ Embedding model loaded")


# ==================================================
# LOAD FAISS INDEX
# ==================================================

if not VECTOR_DB_PATH.exists():

    print("❌ FAISS index not found!")

    print(
        f"Expected:\n{VECTOR_DB_PATH}"
    )

    exit()


index = faiss.read_index(
    str(VECTOR_DB_PATH)
)

print("✅ FAISS index loaded")

print(
    f"Total vectors: {index.ntotal}"
)


# ==================================================
# LOAD CHUNKS
# ==================================================

if not CHUNKS_PATH.exists():

    print("❌ embeddings.json not found!")

    print(
        f"Expected:\n{CHUNKS_PATH}"
    )

    exit()


with open(
    CHUNKS_PATH,
    "r",
    encoding="utf-8"
) as file:

    chunks = json.load(file)


print(
    f"✅ Loaded {len(chunks)} chunks"
)


# ==================================================
# RETRIEVE
# ==================================================

def retrieve(query, top_k=TOP_K):

    # ----------------------------------------------
    # Convert question into embedding
    # ----------------------------------------------

    query_embedding = model.encode(
        [query]
    )

    query_embedding = query_embedding.astype(
        "float32"
    )

    # ----------------------------------------------
    # Search FAISS
    # ----------------------------------------------

    distances, indices = index.search(
        query_embedding,
        top_k
    )

    results = []

    # ----------------------------------------------
    # Get matching chunks
    # ----------------------------------------------

    for distance, index_id in zip(
        distances[0],
        indices[0]
    ):

        if index_id == -1:
            continue

        chunk = chunks[index_id]

        results.append({

            "chunk_id": chunk["chunk_id"],

            "text": chunk["text"],

            "distance": float(distance),

            "metadata": chunk["metadata"]
        })

    return results


# ==================================================
# CHECK RELEVANCE
# ==================================================

def has_relevant_results(results):

    """
    Determine whether the retrieved documents
    are relevant enough to answer the question.
    """

    if not results:

        return False

    best_distance = min(
        result["distance"]
        for result in results
    )

    print(
        f"Best FAISS distance: {best_distance:.4f}"
    )

    if best_distance <= RELEVANCE_THRESHOLD:

        return True

    return False


# ==================================================
# BUILD CONTEXT
# ==================================================

def build_context(results):

    context_parts = []

    for result in results:

        source = result["metadata"].get(
            "source",
            "Unknown source"
        )

        chunk_id = result["chunk_id"]

        text = result["text"]

        context_parts.append(
            f"""
Source: {source}
Chunk ID: {chunk_id}

{text}
"""
        )

    return (
        "\n"
        "----------------------------------------"
        "\n"
    ).join(context_parts)


# ==================================================
# OUT-OF-PDF RESPONSE
# ==================================================

def outside_pdf_response():

    return (
        "I could not find relevant information about "
        "this question in the available LDRP documents.\n\n"
        "I can help you with information contained "
        "in the LDRP documents."
    )


# ==================================================
# COMPLETE RAG PIPELINE
# ==================================================

def ask_rag(question):

    # ----------------------------------------------
    # STEP 1: Retrieve
    # ----------------------------------------------

    print("\n🔎 Searching LDRP documents...")

    results = retrieve(
        question,
        TOP_K
    )

    if not results:

        print(
            "❌ No documents retrieved."
        )

        return {

            "answer": outside_pdf_response(),

            "sources": [],

            "used_rag": False
        }

    print(
        f"✅ Retrieved {len(results)} relevant chunks"
    )

    # ----------------------------------------------
    # STEP 2: Check relevance
    # ----------------------------------------------

    relevant = has_relevant_results(
        results
    )

    if not relevant:

        print(
            "⚠️ Question appears to be outside "
            "the available LDRP documents."
        )

        return {

            "answer": outside_pdf_response(),

            "sources": [],

            "used_rag": False
        }

    # ----------------------------------------------
    # STEP 3: Build context
    # ----------------------------------------------

    context = build_context(
        results
    )

    # ----------------------------------------------
    # STEP 4: Build prompt
    # ----------------------------------------------

    prompt = build_rag_prompt(
        question,
        context
    )

    # ----------------------------------------------
    # STEP 5: Generate answer
    # ----------------------------------------------

    print(
        "🤖 Generating answer with Gemini..."
    )

    answer = generate_answer(
        prompt
    )

    # ----------------------------------------------
    # STEP 6: Prepare sources
    # ----------------------------------------------

    sources = []

    for result in results:

        sources.append({

            "chunk_id":
                result["chunk_id"],

            "source":
                result["metadata"].get(
                    "source",
                    "Unknown source"
                ),

            "page":
            result["metadata"].get(
                "page",
                "Unknown"
            ),

            "distance":
                result["distance"]
        })

    # ----------------------------------------------
    # STEP 7: Return result
    # ----------------------------------------------

    return {

        "answer": answer,

        "sources": sources,

        "used_rag": True
    }


# ==================================================
# MAIN PROGRAM
# ==================================================

if __name__ == "__main__":

    print("\n")

    print("=" * 60)

    print(
        "              LDRP RAG ASSISTANT"
    )

    print("=" * 60)

    question = input(
        "\nAsk a question about LDRP syllabus: "
    )

    result = ask_rag(
        question
    )

    # ----------------------------------------------
    # ANSWER
    # ----------------------------------------------

    print("\n")

    print("=" * 60)

    print(
        "                    ANSWER"
    )

    print("=" * 60)

    print(
        result["answer"]
    )

    # ----------------------------------------------
    # SOURCES
    # ----------------------------------------------

    print("\n")

    print("=" * 60)

    print(
        "                    SOURCES"
    )

    print("=" * 60)

    if result["used_rag"]:

        for source in result["sources"]:

            print(
                f"\nChunk ID: "
                f"{source['chunk_id']}"
            )

            print(
                f"Source: "
                f"{source['source']}"
            )

            print(
                f"Distance: "
                f"{source['distance']:.4f}"
            )
            print(
                f"Page: {source['page']}"
            )

    else:

        print(
            "No LDRP source used."
        )

    print("\n")

    print("=" * 60)