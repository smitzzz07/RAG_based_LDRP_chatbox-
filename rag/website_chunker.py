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
    / "raw"
    / "website_data.json"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "website_chunks.json"
)


# ==================================================
# CHUNK SETTINGS
# ==================================================

CHUNK_SIZE = 500
CHUNK_OVERLAP = 100


# ==================================================
# CLEAN TEXT
# ==================================================

def clean_text(text):

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
# FIND SPLIT POSITION
# ==================================================

def find_split_position(
    text,
    start,
    end
):

    chunk = text[start:end]

    # Prefer newline
    newline_position = chunk.rfind("\n")

    if newline_position > len(chunk) * 0.5:

        return (
            start
            + newline_position
            + 1
        )

    # Prefer sentence
    sentence_matches = list(
        re.finditer(
            r"[.!?]\s",
            chunk
        )
    )

    if sentence_matches:

        last_match = sentence_matches[-1]

        if last_match.start() > len(chunk) * 0.5:

            return (
                start
                + last_match.end()
            )

    # Prefer space
    space_position = chunk.rfind(" ")

    if space_position > len(chunk) * 0.5:

        return (
            start
            + space_position
            + 1
        )

    # Hard split
    return end


# ==================================================
# CREATE WEBSITE CHUNKS
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

        chunk = clean_text(
            text[start:end]
        )

        if chunk:

            chunks.append({
                "text": chunk,
                "start": start,
                "end": end
            })

        next_start = end - overlap

        if next_start <= start:

            next_start = end

        start = next_start

    return chunks


# ==================================================
# MAIN
# ==================================================

def main():

    print("=" * 60)

    print(
        "       LDRP RAG - WEBSITE CHUNKER"
    )

    print("=" * 60)

    # ----------------------------------------------
    # Check input
    # ----------------------------------------------

    if not INPUT_PATH.exists():

        print(
            "\n❌ website_data.json not found!"
        )

        print(
            f"Expected:\n{INPUT_PATH}"
        )

        return

    # ----------------------------------------------
    # Load website data
    # ----------------------------------------------

    with open(
        INPUT_PATH,
        "r",
        encoding="utf-8"
    ) as file:

        website_data = json.load(file)

    source = website_data.get(
        "source",
        "Unknown source"
    )

    url = website_data.get(
        "url",
        ""
    )

    title = website_data.get(
        "title",
        ""
    )

    text = website_data.get(
        "text",
        ""
    )

    print(
        f"\nSource: {source}"
    )

    print(
        f"URL: {url}"
    )

    print(
        f"Title: {title}"
    )

    print(
        f"Characters: {len(text)}"
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
        f"\nTotal website chunks: {len(chunks)}"
    )

    # ----------------------------------------------
    # Build output
    # ----------------------------------------------

    chunk_data = []

    for index, chunk in enumerate(chunks):

        # Start website chunk IDs at 1000
        # so they don't collide with PDF IDs.
        chunk_id = 1000 + index

        chunk_data.append({

            "chunk_id":
                chunk_id,

            "text":
                chunk["text"],

            "metadata": {

                "source":
                    source,

                "source_type":
                    "website",

                "url":
                    url,

                "title":
                    title,

                "page":
                    None,

                "chunk_size":
                    len(chunk["text"]),

                "start_position":
                    chunk["start"],

                "end_position":
                    chunk["end"]
            }
        })

    # ----------------------------------------------
    # Create directory
    # ----------------------------------------------

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

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
        "\n✅ Website chunking completed!"
    )

    print(
        f"Saved to:\n{OUTPUT_PATH}"
    )

    # ----------------------------------------------
    # Show preview
    # ----------------------------------------------

    print(
        "\n" + "=" * 60
    )

    print(
        "FIRST 3 WEBSITE CHUNKS"
    )

    print(
        "=" * 60
    )

    for chunk in chunk_data[:3]:

        print(
            f"\n--- Chunk {chunk['chunk_id']} ---"
        )

        print(
            f"Source: "
            f"{chunk['metadata']['source']}"
        )

        print(
            f"Type: "
            f"{chunk['metadata']['source_type']}"
        )

        print(
            f"URL: "
            f"{chunk['metadata']['url']}"
        )

        print(
            chunk["text"][:400]
        )


# ==================================================
# RUN
# ==================================================

if __name__ == "__main__":

    main()