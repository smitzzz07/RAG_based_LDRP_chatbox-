from pathlib import Path
import json


# ==================================================
# PROJECT PATHS
# ==================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

PDF_CHUNKS_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "chunks.json"
)

WEBSITE_CHUNKS_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "website_chunks.json"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "all_chunks.json"
)


# ==================================================
# LOAD JSON
# ==================================================

def load_json(path):

    if not path.exists():

        raise FileNotFoundError(
            f"File not found:\n{path}"
        )


    with open(
        path,
        "r",
        encoding="utf-8"
    ) as file:

        data = json.load(file)


    if not isinstance(data, list):

        raise ValueError(
            f"Expected a JSON list in:\n{path}"
        )


    return data


# ==================================================
# VALIDATE CHUNK
# ==================================================

def validate_chunk(
    chunk,
    source_name
):

    required_fields = [
        "chunk_id",
        "text",
        "metadata"
    ]


    for field in required_fields:

        if field not in chunk:

            raise ValueError(
                f"Missing '{field}' in "
                f"{source_name} chunk"
            )


    if not isinstance(
        chunk["metadata"],
        dict
    ):

        raise ValueError(
            f"Invalid metadata in "
            f"{source_name} chunk "
            f"{chunk['chunk_id']}"
        )


    if not chunk["text"].strip():

        raise ValueError(
            f"Empty text in "
            f"{source_name} chunk "
            f"{chunk['chunk_id']}"
        )


# ==================================================
# VALIDATE CHUNKS
# ==================================================

def validate_chunks(
    chunks,
    source_name
):

    for chunk in chunks:

        validate_chunk(
            chunk,
            source_name
        )


# ==================================================
# FIX PDF METADATA
# ==================================================

def prepare_pdf_chunks(
    chunks
):

    for chunk in chunks:

        metadata = chunk["metadata"]

        metadata["source"] = (
            "mca_syllabus.pdf"
        )

        metadata["source_type"] = (
            "pdf"
        )

        metadata["title"] = (
            "MCA Syllabus"
        )

        metadata["url"] = None


# ==================================================
# FIX WEBSITE METADATA
# ==================================================

def prepare_website_chunks(
    chunks
):

    for chunk in chunks:

        metadata = chunk["metadata"]

        metadata["source_type"] = (
            "website"
        )

        if not metadata.get("source"):

            metadata["source"] = (
                "LDRP-ITR Official Website"
            )


# ==================================================
# MAIN
# ==================================================

def main():

    print("=" * 60)

    print(
        "       LDRP RAG - COMBINE KNOWLEDGE"
    )

    print("=" * 60)


    # --------------------------------------------------
    # PDF
    # --------------------------------------------------

    print(
        "\n📄 Loading PDF chunks..."
    )

    pdf_chunks = load_json(
        PDF_CHUNKS_PATH
    )


    print(
        f"✅ PDF chunks loaded: "
        f"{len(pdf_chunks)}"
    )


    validate_chunks(
        pdf_chunks,
        "PDF"
    )


    prepare_pdf_chunks(
        pdf_chunks
    )


    print(
        "✅ PDF metadata prepared"
    )


    # --------------------------------------------------
    # WEBSITE
    # --------------------------------------------------

    print(
        "\n🌐 Loading website chunks..."
    )

    website_chunks = load_json(
        WEBSITE_CHUNKS_PATH
    )


    print(
        f"✅ Website chunks loaded: "
        f"{len(website_chunks)}"
    )


    validate_chunks(
        website_chunks,
        "Website"
    )


    prepare_website_chunks(
        website_chunks
    )


    print(
        "✅ Website metadata prepared"
    )


    # --------------------------------------------------
    # COMBINE
    # --------------------------------------------------

    all_chunks = (
        pdf_chunks
        + website_chunks
    )


    # --------------------------------------------------
    # CHECK IDS
    # --------------------------------------------------

    chunk_ids = [
        chunk["chunk_id"]
        for chunk in all_chunks
    ]


    if len(chunk_ids) != len(set(chunk_ids)):

        duplicates = [
            chunk_id
            for chunk_id in set(chunk_ids)
            if chunk_ids.count(chunk_id) > 1
        ]

        raise ValueError(
            f"Duplicate chunk IDs:\n{duplicates}"
        )


    print(
        "✅ All chunk IDs are unique"
    )


    # --------------------------------------------------
    # CHECK EMPTY
    # --------------------------------------------------

    empty_chunks = [
        chunk["chunk_id"]
        for chunk in all_chunks
        if not chunk["text"].strip()
    ]


    if empty_chunks:

        raise ValueError(
            f"Empty chunks detected:\n"
            f"{empty_chunks}"
        )


    print(
        "✅ No empty chunks found"
    )


    # --------------------------------------------------
    # SAVE
    # --------------------------------------------------

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )


    OUTPUT_PATH.write_text(
        json.dumps(
            all_chunks,
            indent=2,
            ensure_ascii=False
        ),
        encoding="utf-8"
    )


    # --------------------------------------------------
    # SUMMARY
    # --------------------------------------------------

    pdf_count = sum(
        1
        for chunk in all_chunks
        if chunk["metadata"].get(
            "source_type"
        ) == "pdf"
    )


    website_count = sum(
        1
        for chunk in all_chunks
        if chunk["metadata"].get(
            "source_type"
        ) == "website"
    )


    print(
        "\n" + "=" * 60
    )

    print(
        "       KNOWLEDGE BASE SUMMARY"
    )

    print(
        "=" * 60
    )

    print(
        f"📄 PDF chunks:      {pdf_count}"
    )

    print(
        f"🌐 Website chunks:  {website_count}"
    )

    print(
        f"📚 Total chunks:    {len(all_chunks)}"
    )

    print(
        "=" * 60
    )

    print(
        "\n✅ Knowledge base created successfully!"
    )

    print(
        f"\n📁 Saved to:\n{OUTPUT_PATH}"
    )


# ==================================================
# RUN
# ==================================================

if __name__ == "__main__":

    main()