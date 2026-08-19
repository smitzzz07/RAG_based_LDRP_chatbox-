from pathlib import Path
import json

import faiss
from sentence_transformers import SentenceTransformer


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


# ==================================================
# LOAD MODEL
# ==================================================

print("Loading embedding model...")

model = SentenceTransformer(MODEL_NAME)

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

print(
    f"✅ FAISS index loaded"
)

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
# RETRIEVE FUNCTION
# ==================================================

def retrieve(query, top_k=3):

    # ----------------------------------------------
    # Convert user question into embedding
    # ----------------------------------------------

    query_embedding = model.encode(
        [query]
    )

    # ----------------------------------------------
    # Convert to FAISS-compatible format
    # ----------------------------------------------

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
    # Get actual chunks
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
# TEST RETRIEVER
# ==================================================

if __name__ == "__main__":

    print("\n====================================")
    print("       LDRP RAG - RETRIEVER")
    print("====================================")

    query = input(
        "\nAsk a question about LDRP syllabus: "
    )

    results = retrieve(
        query,
        TOP_K
    )

    print("\n====================================")
    print("          SEARCH RESULTS")
    print("====================================")

    for rank, result in enumerate(
        results,
        start=1
    ):

        print(
            f"\n--- Result {rank} ---"
        )

        print(
            f"Chunk ID: {result['chunk_id']}"
        )

        print(
            f"Distance: {result['distance']:.4f}"
        )

        print(
            f"Source: {result['metadata']['source']}"
        )

        print("\nText:")

        print(
            result["text"]
        )