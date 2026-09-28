from pathlib import Path
import json


# ==================================================
# LDRP RAG - COMBINE PDF + WEBSITE KNOWLEDGE
# ==================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

PDF_CHUNKS_PATH = PROJECT_ROOT / "data" / "processed" / "chunks.json"
WEBSITE_CHUNKS_PATH = PROJECT_ROOT / "data" / "processed" / "website_chunks.json"
OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "all_chunks.json"


def load_json(path):
    if not path.exists():
        raise FileNotFoundError(f"File not found:\n{path}")

    data = json.loads(path.read_text(encoding="utf-8"))

    if not isinstance(data, list):
        raise ValueError(f"Expected a JSON list in:\n{path}")

    return data


def validate_chunk(chunk, source_name):
    required_fields = ["chunk_id", "text", "metadata"]

    for field in required_fields:
        if field not in chunk:
            raise ValueError(
                f"Missing '{field}' in {source_name} chunk"
            )

    if not isinstance(chunk["metadata"], dict):
        raise ValueError(
            f"Invalid metadata in {source_name} chunk {chunk['chunk_id']}"
        )

    if not chunk["text"].strip():
        raise ValueError(
            f"Empty text in {source_name} chunk {chunk['chunk_id']}"
        )


def prepare_pdf_chunks(chunks):
    for chunk in chunks:
        metadata = chunk["metadata"]
        metadata.setdefault("source_type", "pdf")
        metadata.setdefault("title", metadata.get("source", "PDF"))
        metadata.setdefault("url", None)


def prepare_website_chunks(chunks):
    for chunk in chunks:
        metadata = chunk["metadata"]
        metadata["source_type"] = "website"

        if not metadata.get("source"):
            metadata["source"] = "LDRP-ITR Official Website"


def main():
    print("=" * 70)
    print("       LDRP RAG - COMBINE KNOWLEDGE")
    print("=" * 70)

    print("\n📄 Loading PDF chunks...")
    pdf_chunks = load_json(PDF_CHUNKS_PATH)

    print(f"✅ PDF chunks loaded: {len(pdf_chunks)}")
    for chunk in pdf_chunks:
        validate_chunk(chunk, "PDF")
    prepare_pdf_chunks(pdf_chunks)

    print("\n🌐 Loading website chunks...")
    website_chunks = load_json(WEBSITE_CHUNKS_PATH)

    print(f"✅ Website chunks loaded: {len(website_chunks)}")
    for chunk in website_chunks:
        validate_chunk(chunk, "Website")
    prepare_website_chunks(website_chunks)

    # Combine first, then assign ONE global ID sequence.
    all_chunks = pdf_chunks + website_chunks

    for new_id, chunk in enumerate(all_chunks):
        chunk["chunk_id"] = new_id

    if len(all_chunks) != len(
        {chunk["chunk_id"] for chunk in all_chunks}
    ):
        raise ValueError("Duplicate chunk IDs detected.")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    OUTPUT_PATH.write_text(
        json.dumps(
            all_chunks,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    pdf_count = sum(
        1 for c in all_chunks
        if c["metadata"].get("source_type") == "pdf"
    )

    website_count = sum(
        1 for c in all_chunks
        if c["metadata"].get("source_type") == "website"
    )

    sources = {}
    for chunk in all_chunks:
        source = chunk["metadata"].get("source", "unknown")
        sources[source] = sources.get(source, 0) + 1

    print("\n" + "=" * 70)
    print("KNOWLEDGE BASE SUMMARY")
    print("=" * 70)

    print(f"📄 PDF chunks     : {pdf_count}")
    print(f"🌐 Website chunks : {website_count}")
    print(f"📚 Total chunks   : {len(all_chunks)}")

    print("\nChunks by source:")
    for source, count in sources.items():
        print(f"  • {source}: {count}")

    print(f"\n📁 Saved: {OUTPUT_PATH}")
    print("✅ Knowledge base created successfully!")


if __name__ == "__main__":
    main()
