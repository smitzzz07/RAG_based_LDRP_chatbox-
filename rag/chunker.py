from pathlib import Path
import json
import re


# ==================================================
# PROJECT PATHS
# ==================================================

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


# ==================================================
# CHUNK SETTINGS
# ==================================================

CHUNK_SIZE = 500

CHUNK_OVERLAP = 100


# ==================================================
# CLEAN CHUNK
# ==================================================

def clean_chunk(text):

    text = re.sub(
        r"[ \t]+",
        " ",
        text
    )

    text = re.sub(
        r"\n{3,}",
        "\n\n",
        text
    )

    return text.strip()


# ==================================================
# FIND PAGE NUMBER
# ==================================================

def get_page_number(text):

    """
    Find the last PAGE marker inside the chunk.
    """

    matches = re.findall(
        r"========== PAGE (\d+) ==========",
        text
    )

    if matches:

        return int(
            matches[-1]
        )

    return None


# ==================================================
# REMOVE PAGE MARKERS
# ==================================================

def remove_page_markers(text):

    return re.sub(
        r"========== PAGE \d+ ==========",
        "",
        text
    )


# ==================================================
# FIND SPLIT POSITION
# ==================================================

def find_split_position(
    text,
    start,
    end
):

    chunk = text[start:end]

    # ----------------------------------------------
    # Prefer newline
    # ----------------------------------------------

    newline_position = chunk.rfind(
        "\n"
    )

    if newline_position > len(chunk) * 0.5:

        return (
            start
            + newline_position
            + 1
        )

    # ----------------------------------------------
    # Prefer sentence
    # ----------------------------------------------

    sentence_matches = list(
        re.finditer(
            r"[.!?]\s",
            chunk
        )
    )

    if sentence_matches:

        last_match = sentence_matches[-1]

        if (
            last_match.start()
            > len(chunk) * 0.5
        ):

            return (
                start
                + last_match.end()
            )

    # ----------------------------------------------
    # Prefer space
    # ----------------------------------------------

    space_position = chunk.rfind(
        " "
    )

    if space_position > len(chunk) * 0.5:

        return (
            start
            + space_position
            + 1
        )

    # ----------------------------------------------
    # Hard split
    # ----------------------------------------------

    return end


# ==================================================
# CREATE CHUNKS
# ==================================================

def create_chunks(
    text,
    chunk_size=CHUNK_SIZE,
    overlap=CHUNK_OVERLAP
):

    if overlap >= chunk_size:

        raise ValueError(
            "Chunk overlap must be smaller than chunk size."
        )

    chunks = []

    start = 0

    text_length = len(text)

    while start < text_length:

        target_end = min(
            start + chunk_size,
            text_length
        )

        if target_end < text_length:

            end = find_split_position(
                text,
                start,
                target_end
            )

        else:

            end = target_end

        raw_chunk = text[start:end]

        # ------------------------------------------
        # Detect page
        # ------------------------------------------

        page_number = get_page_number(
            raw_chunk
        )

        # ------------------------------------------
        # Remove page markers
        # ------------------------------------------

        chunk = remove_page_markers(
            raw_chunk
        )

        chunk = clean_chunk(
            chunk
        )

        if chunk:

            chunks.append({

                "text": chunk,

                "page": page_number,

                "start": start,

                "end": end
            })

        # ------------------------------------------
        # Move forward
        # ------------------------------------------

        next_start = end - overlap

        if next_start <= start:

            next_start = end

        start = next_start

    return chunks


# ==================================================
# MAIN
# ==================================================

def main():

    print("=" * 55)

    print(
        "        LDRP RAG - PAGE AWARE CHUNKING"
    )

    print("=" * 55)

    # ----------------------------------------------
    # Check input
    # ----------------------------------------------

    if not INPUT_PATH.exists():

        print(
            "\n❌ Cleaned text file not found!"
        )

        print(
            f"Expected: {INPUT_PATH}"
        )

        return

    # ----------------------------------------------
    # Read text
    # ----------------------------------------------

    text = INPUT_PATH.read_text(
        encoding="utf-8"
    )

    print(
        f"\nInput characters: {len(text)}"
    )

    print(
        f"Chunk size: {CHUNK_SIZE}"
    )

    print(
        f"Chunk overlap: {CHUNK_OVERLAP}"
    )

    # ----------------------------------------------
    # Create chunks
    # ----------------------------------------------

    chunks = create_chunks(
        text,
        CHUNK_SIZE,
        CHUNK_OVERLAP
    )

    print(
        f"\nTotal chunks: {len(chunks)}"
    )

    # ----------------------------------------------
    # Build JSON
    # ----------------------------------------------

    chunk_data = []

    for index, chunk in enumerate(
        chunks
    ):

        chunk_data.append({

            "chunk_id": index,

            "text": chunk["text"],

            "metadata": {

                "source":
                    "mca_syllabus.pdf",

                "page":
                    chunk["page"],

                "chunk_size":
                    len(chunk["text"]),

                "start_position":
                    chunk["start"],

                "end_position":
                    chunk["end"]
            }
        })

    # ----------------------------------------------
    # Save
    # ----------------------------------------------

    OUTPUT_PATH.write_text(

        json.dumps(
            chunk_data,
            indent=2,
            ensure_ascii=False
        ),

        encoding="utf-8"
    )

    print(
        "\n✅ Page-aware chunking completed!"
    )

    print(
        f"Saved to:\n{OUTPUT_PATH}"
    )

    # ----------------------------------------------
    # Show first chunks
    # ----------------------------------------------

    print("\n" + "=" * 55)

    print(
        "FIRST 5 CHUNKS"
    )

    print("=" * 55)

    for chunk in chunk_data[:5]:

        print(
            f"\n--- Chunk {chunk['chunk_id']} ---"
        )

        print(
            f"Page: "
            f"{chunk['metadata']['page']}"
        )

        print(
            f"Characters: "
            f"{chunk['metadata']['chunk_size']}"
        )

        print(
            chunk["text"][:300]
        )


# ==================================================
# RUN
# ==================================================

if __name__ == "__main__":

    main()