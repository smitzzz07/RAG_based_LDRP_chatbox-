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
# PAGE MARKER
# ==================================================

PAGE_PATTERN = r"========== PAGE (\d+) =========="


# ==================================================
# CLEAN TEXT
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
# GET PAGE AT POSITION
# ==================================================

def get_page_at_position(text, position):

    matches = list(
        re.finditer(
            PAGE_PATTERN,
            text[:position + 1]
        )
    )

    if not matches:
        return None

    return int(
        matches[-1].group(1)
    )


# ==================================================
# GET PAGE RANGE
# ==================================================

def get_page_range(text, start, end):

    start_page = get_page_at_position(
        text,
        start
    )

    end_page = get_page_at_position(
        text,
        max(start, end - 1)
    )

    # If the chunk starts before the first page marker,
    # use the first page marker found inside the chunk.
    if start_page is None:

        first_match = re.search(
            PAGE_PATTERN,
            text[start:end]
        )

        if first_match:

            start_page = int(
                first_match.group(1)
            )

    # If end page is still missing, use start page.
    if end_page is None:

        end_page = start_page

    return start_page, end_page


# ==================================================
# REMOVE PAGE MARKERS
# ==================================================

def remove_page_markers(text):

    return re.sub(
        PAGE_PATTERN,
        "",
        text
    )


# ==================================================
# FIND GOOD SPLIT POSITION
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


        # Get page information before removing marker
        start_page, end_page = get_page_range(
            text,
            start,
            end
        )


        raw_chunk = text[start:end]


        # Remove page marker
        chunk = remove_page_markers(
            raw_chunk
        )


        chunk = clean_chunk(
            chunk
        )


        if chunk:

            chunks.append(
                {
                    "text": chunk,

                    "start_page": start_page,

                    "end_page": end_page,

                    "start": start,

                    "end": end
                }
            )


        if end >= text_length:
            break


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
        "       LDRP RAG - PAGE AWARE CHUNKING"
    )

    print("=" * 60)


    # Check input
    if not INPUT_PATH.exists():

        print(
            "\n❌ Cleaned text file not found!"
        )

        print(
            f"Expected:\n{INPUT_PATH}"
        )

        return


    # Read text
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


    # Create chunks
    chunks = create_chunks(
        text
    )


    print(
        f"\nTotal chunks: {len(chunks)}"
    )


    # Build final JSON
    chunk_data = []


    for index, chunk in enumerate(chunks):

        chunk_data.append(
            {
                "chunk_id": index,

                "text": chunk["text"],

                "metadata":
                {
                    "source": "mca_syllabus.pdf",

                    "source_type": "pdf",

                    "title": "MCA Syllabus",

                    "url": None,

                    "page":
                        chunk["start_page"],

                    "start_page":
                        chunk["start_page"],

                    "end_page":
                        chunk["end_page"],

                    "chunk_size":
                        len(chunk["text"]),

                    "start_position":
                        chunk["start"],

                    "end_position":
                        chunk["end"]
                }
            }
        )


    # Save
    OUTPUT_PATH.write_text(
        json.dumps(
            chunk_data,
            indent=2,
            ensure_ascii=False
        ),
        encoding="utf-8"
    )


    # Summary
    print(
        "\n✅ Page-aware chunking completed!"
    )

    print(
        f"Saved to:\n{OUTPUT_PATH}"
    )


    print(
        "\n" + "=" * 60
    )

    print(
        "FIRST 5 CHUNKS"
    )

    print(
        "=" * 60
    )


    for chunk in chunk_data[:5]:

        metadata = chunk["metadata"]

        print(
            f"\nChunk {chunk['chunk_id']}"
        )

        print(
            f"Page: {metadata['page']}"
        )

        print(
            f"Page range: "
            f"{metadata['start_page']} → "
            f"{metadata['end_page']}"
        )

        print(
            f"Characters: "
            f"{metadata['chunk_size']}"
        )

        print(
            chunk["text"][:300]
        )


# ==================================================
# RUN
# ==================================================

if __name__ == "__main__":

    main()