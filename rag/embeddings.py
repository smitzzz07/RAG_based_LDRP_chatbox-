from pathlib import Path
import json

from sentence_transformers import SentenceTransformer


# --------------------------------------------------
# PROJECT PATHS
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

INPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "chunks.json"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "embeddings.json"
)


# --------------------------------------------------
# EMBEDDING MODEL
# --------------------------------------------------

MODEL_NAME = "all-MiniLM-L6-v2"


def main():

    print("====================================")
    print("       LDRP RAG - EMBEDDINGS")
    print("====================================")

    # Check chunks file
    if not INPUT_PATH.exists():

        print("❌ chunks.json not found!")

        print(
            f"Expected location:\n{INPUT_PATH}"
        )

        return

    # Load chunks
    with open(
        INPUT_PATH,
        "r",
        encoding="utf-8"
    ) as file:

        chunks = json.load(file)

    print(f"✅ Loaded {len(chunks)} chunks")

    # Load embedding model
    print("\nLoading embedding model...")

    model = SentenceTransformer(
        MODEL_NAME
    )

    print("✅ Embedding model loaded")

    # Extract text
    texts = [
        chunk["text"]
        for chunk in chunks
    ]

    print("\nCreating embeddings...")

    # Generate vectors
    embeddings = model.encode(
        texts,
        show_progress_bar=True
    )

    print("✅ Embeddings created")

    print(
        f"Embedding dimensions: "
        f"{embeddings.shape[1]}"
    )

    # Add embeddings to chunks
    for i, chunk in enumerate(chunks):

        chunk["embedding"] = (
            embeddings[i].tolist()
        )

    # Save
    with open(
        OUTPUT_PATH,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            chunks,
            file,
            indent=2,
            ensure_ascii=False
        )

    print("\n====================================")
    print("SUCCESS")
    print("====================================")

    print(
        f"Saved to:\n{OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()