from pathlib import Path
import json
import numpy as np
import faiss


# ----------------------------------------
# PROJECT PATHS
# ----------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

INPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "embeddings.json"
)

VECTOR_DB_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "faiss.index"
)


# ----------------------------------------
# MAIN
# ----------------------------------------

def main():

    print("====================================")
    print("       LDRP RAG - VECTOR STORE")
    print("====================================")

    # Check embeddings file
    if not INPUT_PATH.exists():

        print("❌ embeddings.json not found!")

        print(f"Expected: {INPUT_PATH}")

        return

    # Load embeddings
    with open(
        INPUT_PATH,
        "r",
        encoding="utf-8"
    ) as file:

        chunks = json.load(file)

    print(f"✅ Loaded {len(chunks)} chunks")

    # ----------------------------------------
    # Convert embeddings to NumPy array
    # ----------------------------------------

    embeddings = np.array(
        [
            chunk["embedding"]
            for chunk in chunks
        ],
        dtype="float32"
    )

    print(
        f"Embedding shape: {embeddings.shape}"
    )

    # ----------------------------------------
    # Create FAISS index
    # ----------------------------------------

    dimension = embeddings.shape[1]

    index = faiss.IndexFlatL2(dimension)

    # Add vectors
    index.add(embeddings)

    print(
        f"✅ Added {index.ntotal} vectors"
    )

    # ----------------------------------------
    # Save index
    # ----------------------------------------

    faiss.write_index(
        index,
        str(VECTOR_DB_PATH)
    )

    print("✅ FAISS vector database created!")

    print(
        f"Saved to:\n{VECTOR_DB_PATH}"
    )


if __name__ == "__main__":
    main()