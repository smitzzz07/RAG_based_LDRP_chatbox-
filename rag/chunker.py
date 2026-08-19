from pathlib import Path
import json
import re


# --------------------------------------------------
# PROJECT PATHS
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

INPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "cleaned_text.txt"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "chunks.json"
)


# --------------------------------------------------
# CHUNK SETTINGS
# --------------------------------------------------

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150


# --------------------------------------------------
# SPLIT TEXT INTO CHUNKS
# --------------------------------------------------

def create_chunks(text, chunk_size=1000, overlap=150):

    if overlap >= chunk_size:
        raise ValueError(
            "Chunk overlap must be smaller than chunk size."
        )

    chunks = []

    start = 0
    text_length = len(text)

    while start < text_length:

        end = start + chunk_size

        chunk = text[start:end]

        # Try to avoid cutting a sentence in half
        if end < text_length:

            last_newline = chunk.rfind("\n")

            last_period = chunk.rfind(".")

            split_position = max(
                last_newline,
                last_period
            )

            if split_position > chunk_size * 0.5:
                end = start + split_position + 1
                chunk = text[start:end]

        chunk = chunk.strip()

        if chunk:
            chunks.append(chunk)

        # Move forward while keeping overlap
        start = end - overlap

    return chunks


# --------------------------------------------------
# MAIN
# --------------------------------------------------

def main():

    print("====================================")
    print("        LDRP RAG - CHUNKING")
    print("====================================")

    # Check input file
    if not INPUT_PATH.exists():

        print("❌ Cleaned text file not found!")
        print(f"Expected: {INPUT_PATH}")

        return

    # Read cleaned text
    text = INPUT_PATH.read_text(
        encoding="utf-8"
    )

    print(f"Input characters: {len(text)}")

    # Create chunks
    chunks = create_chunks(
        text,
        CHUNK_SIZE,
        CHUNK_OVERLAP
    )

    print(f"Total chunks: {len(chunks)}")

    # Create JSON objects
    chunk_data = []

    for index, chunk in enumerate(chunks):

        chunk_data.append({
            "chunk_id": index,
            "text": chunk,
            "metadata": {
                "source": "mca_syllabus.pdf",
                "chunk_size": len(chunk)
            }
        })

    # Save chunks
    OUTPUT_PATH.write_text(
        json.dumps(
            chunk_data,
            indent=2,
            ensure_ascii=False
        ),
        encoding="utf-8"
    )

    print("✅ Chunking completed!")

    print(
        f"Saved chunks to: {OUTPUT_PATH}"
    )

    # Show first few chunks
    print("\n====================================")
    print("FIRST 3 CHUNKS")
    print("====================================")

    for chunk in chunk_data[:3]:

        print(
            f"\n--- Chunk {chunk['chunk_id']} ---"
        )

        print(chunk["text"][:500])


# --------------------------------------------------
# RUN
# --------------------------------------------------

if __name__ == "__main__":
    main()