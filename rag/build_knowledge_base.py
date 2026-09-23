"""
Multi-PDF Knowledge Base Builder
---------------------------------

Builds the complete LDRP RAG knowledge base from:

    data/raw/*.pdf
    data/processed/website_chunks.json

Outputs:

    data/processed/all_chunks.json
    data/processed/embeddings.json
    data/processed/faiss.index

Run from project root:

    python rag/build_knowledge_base.py
"""

from pathlib import Path
import json
import re
import sys

import fitz  # PyMuPDF
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

WEBSITE_CHUNKS_PATH = PROCESSED_DIR / "website_chunks.json"
ALL_CHUNKS_PATH = PROCESSED_DIR / "all_chunks.json"
EMBEDDINGS_PATH = PROCESSED_DIR / "embeddings.json"
FAISS_PATH = PROCESSED_DIR / "faiss.index"


# ============================================================
# SETTINGS
# ============================================================

MODEL_NAME = "all-MiniLM-L6-v2"

CHUNK_SIZE = 500
CHUNK_OVERLAP = 100

# PDF chunks start from 0.
# Website chunks will be assigned IDs after all PDF chunks.
PDF_START_ID = 0


# ============================================================
# UTILITY
# ============================================================

def clean_text(text: str) -> str:
    """
    Clean extracted PDF text.
    """

    if not text:
        return ""

    # Normalize line endings
    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    # Remove excessive spaces/tabs
    text = re.sub(r"[ \t]+", " ", text)

    # Remove excessive blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Remove spaces around newlines
    text = re.sub(r" *\n *", "\n", text)

    return text.strip()


def split_text(text: str, chunk_size=500, overlap=100):
    """
    Split text into overlapping chunks.

    Character-based chunking is intentionally kept compatible
    with the existing chunking approach.
    """

    if not text:
        return []

    if overlap >= chunk_size:
        raise ValueError("CHUNK_OVERLAP must be smaller than CHUNK_SIZE")

    chunks = []

    start = 0
    text_length = len(text)

    while start < text_length:

        end = min(start + chunk_size, text_length)

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= text_length:
            break

        start = end - overlap

    return chunks


# ============================================================
# PDF EXTRACTION
# ============================================================

def extract_pdf_pages(pdf_path: Path):
    """
    Extract text from every page of a PDF.

    Returns:

        [
            {
                "page": 1,
                "text": "..."
            },
            ...
        ]
    """

    print()
    print("=" * 70)
    print(f"📄 Processing PDF: {pdf_path.name}")
    print("=" * 70)

    pages = []

    try:
        document = fitz.open(pdf_path)
    except Exception as e:
        print(f"❌ Could not open {pdf_path.name}")
        print(f"   Error: {e}")
        return pages

    print(f"   Pages found: {len(document)}")

    for page_index in range(len(document)):

        page_number = page_index + 1

        try:
            page = document[page_index]
            text = page.get_text("text")
            text = clean_text(text)

            if not text:
                print(f"   ⚠️ Page {page_number}: no text")
                continue

            pages.append(
                {
                    "page": page_number,
                    "text": text
                }
            )

        except Exception as e:
            print(
                f"   ⚠️ Error reading page "
                f"{page_number}: {e}"
            )

    document.close()

    print(f"   ✅ Extracted pages: {len(pages)}")

    return pages


# ============================================================
# BUILD PDF CHUNKS
# ============================================================

def build_pdf_chunks(pdf_path: Path, start_chunk_id: int):
    """
    Convert one PDF into chunks while preserving:

        source
        title
        page
        source_type
    """

    pages = extract_pdf_pages(pdf_path)

    if not pages:
        return [], start_chunk_id

    chunks = []

    chunk_id = start_chunk_id

    title = pdf_path.stem.replace("_", " ").replace("-", " ").strip()

    for page_data in pages:

        page_number = page_data["page"]
        page_text = page_data["text"]

        text_chunks = split_text(
            page_text,
            CHUNK_SIZE,
            CHUNK_OVERLAP
        )

        for chunk_number, chunk_text in enumerate(text_chunks):

            chunk = {
                "chunk_id": chunk_id,

                "text": chunk_text,

                "metadata": {
                    "source": pdf_path.name,
                    "source_type": "pdf",
                    "title": title,
                    "page": page_number,
                    "chunk_number": chunk_number,
                    "url": None
                }
            }

            chunks.append(chunk)

            chunk_id += 1

    print(f"   🧩 Chunks created: {len(chunks)}")

    return chunks, chunk_id


# ============================================================
# LOAD WEBSITE CHUNKS
# ============================================================

def load_website_chunks(start_chunk_id: int):
    """
    Load existing website chunks.

    Their IDs are reassigned so there can never be a collision
    with PDF chunks.
    """

    if not WEBSITE_CHUNKS_PATH.exists():

        print()
        print("🌐 No website_chunks.json found.")
        print("   Skipping website chunks.")

        return [], start_chunk_id

    print()
    print("=" * 70)
    print("🌐 Loading Website Chunks")
    print("=" * 70)

    try:

        with open(
            WEBSITE_CHUNKS_PATH,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

    except Exception as e:

        print("❌ Could not load website_chunks.json")
        print(f"   Error: {e}")

        return [], start_chunk_id

    # Support either:
    #
    # [
    #   {...}
    # ]
    #
    # OR
    #
    # {
    #   "chunks": [...]
    # }

    if isinstance(data, list):

        website_chunks = data

    elif isinstance(data, dict):

        website_chunks = data.get("chunks", [])

    else:

        website_chunks = []

    result = []

    chunk_id = start_chunk_id

    for chunk in website_chunks:

        if not isinstance(chunk, dict):
            continue

        text = chunk.get("text", "")

        if not text:
            continue

        metadata = chunk.get("metadata", {})

        if not isinstance(metadata, dict):
            metadata = {}

        metadata = dict(metadata)

        metadata["source_type"] = "website"

        if not metadata.get("source"):
            metadata["source"] = "LDRP Official Website"

        if not metadata.get("title"):
            metadata["title"] = "LDRP Official Website"

        if "url" not in metadata:
            metadata["url"] = None

        result.append(
            {
                "chunk_id": chunk_id,
                "text": text,
                "metadata": metadata
            }
        )

        chunk_id += 1

    print(f"   🌐 Website chunks loaded: {len(result)}")

    return result, chunk_id


# ============================================================
# VALIDATE CHUNKS
# ============================================================

def validate_chunks(chunks):
    """
    Make sure every chunk has the fields required by the
    retriever.
    """

    print()
    print("=" * 70)
    print("🔍 Validating Chunks")
    print("=" * 70)

    if not chunks:

        raise RuntimeError(
            "No chunks were generated. "
            "Add at least one PDF to data/raw/."
        )

    ids = set()

    for index, chunk in enumerate(chunks):

        if not isinstance(chunk, dict):
            raise ValueError(
                f"Chunk {index} is not a dictionary."
            )

        if "chunk_id" not in chunk:
            raise ValueError(
                f"Chunk {index} has no chunk_id."
            )

        if "text" not in chunk:
            raise ValueError(
                f"Chunk {index} has no text."
            )

        if "metadata" not in chunk:
            raise ValueError(
                f"Chunk {index} has no metadata."
            )

        chunk_id = chunk["chunk_id"]

        if chunk_id in ids:

            raise ValueError(
                f"Duplicate chunk ID detected: {chunk_id}"
            )

        ids.add(chunk_id)

    print(f"   ✅ Total chunks: {len(chunks)}")
    print("   ✅ No duplicate chunk IDs")


# ============================================================
# SAVE ALL CHUNKS
# ============================================================

def save_all_chunks(chunks):

    PROCESSED_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        ALL_CHUNKS_PATH,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            chunks,
            file,
            indent=2,
            ensure_ascii=False
        )

    print()
    print(f"💾 Saved: {ALL_CHUNKS_PATH}")


# ============================================================
# CREATE EMBEDDINGS
# ============================================================

def create_embeddings(chunks):

    print()
    print("=" * 70)
    print("🧠 Creating Embeddings")
    print("=" * 70)

    print(f"   Model: {MODEL_NAME}")
    print(f"   Chunks: {len(chunks)}")

    try:

        model = SentenceTransformer(MODEL_NAME)

    except Exception as e:

        print("❌ Could not load embedding model.")
        print(f"   Error: {e}")

        raise

    texts = [
        chunk["text"]
        for chunk in chunks
    ]

    embeddings = model.encode(
        texts,
        show_progress_bar=True,
        convert_to_numpy=True
    )

    embeddings = np.asarray(
        embeddings,
        dtype="float32"
    )

    print(
        f"   ✅ Embedding shape: "
        f"{embeddings.shape}"
    )

    embedding_data = []

    for index, chunk in enumerate(chunks):

        embedding_data.append(
            {
                "chunk_id": chunk["chunk_id"],
                "embedding": embeddings[index].tolist()
            }
        )

    with open(
        EMBEDDINGS_PATH,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            embedding_data,
            file,
            ensure_ascii=False
        )

    print(f"💾 Saved: {EMBEDDINGS_PATH}")

    return embeddings


# ============================================================
# CREATE FAISS INDEX
# ============================================================

def create_faiss_index(embeddings):

    print()
    print("=" * 70)
    print("🔎 Building FAISS Index")
    print("=" * 70)

    if len(embeddings) == 0:

        raise RuntimeError(
            "Cannot create FAISS index with zero embeddings."
        )

    dimension = embeddings.shape[1]

    print(f"   Vector dimension: {dimension}")
    print(f"   Number of vectors: {len(embeddings)}")

    index = faiss.IndexFlatL2(dimension)

    index.add(embeddings)

    print(
        f"   ✅ FAISS vectors: "
        f"{index.ntotal}"
    )

    faiss.write_index(
        index,
        str(FAISS_PATH)
    )

    print(f"💾 Saved: {FAISS_PATH}")

    return index


# ============================================================
# SHOW SUMMARY
# ============================================================

def show_summary(
    pdf_files,
    pdf_chunks,
    website_chunks,
    embeddings,
    index
):

    print()
    print()
    print("=" * 70)
    print("🎉 KNOWLEDGE BASE BUILD COMPLETE")
    print("=" * 70)

    print()
    print("📚 PDFs")
    print(f"   Files: {len(pdf_files)}")

    for pdf in pdf_files:
        print(f"   • {pdf.name}")

    print()
    print("🧩 CHUNKS")
    print(f"   PDF chunks:     {len(pdf_chunks)}")
    print(f"   Website chunks: {len(website_chunks)}")
    print(
        f"   Total chunks:   "
        f"{len(pdf_chunks) + len(website_chunks)}"
    )

    print()
    print("🧠 EMBEDDINGS")
    print(f"   Model: {MODEL_NAME}")
    print(f"   Shape: {embeddings.shape}")

    print()
    print("🔎 FAISS")
    print(f"   Vectors: {index.ntotal}")

    print()
    print("📁 OUTPUT")
    print(f"   {ALL_CHUNKS_PATH}")
    print(f"   {EMBEDDINGS_PATH}")
    print(f"   {FAISS_PATH}")

    print()
    print("🚀 Your RAG knowledge base is ready.")
    print("=" * 70)


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("╔══════════════════════════════════════════════════════════╗")
    print("║          LDRP RAG MULTI-PDF KNOWLEDGE BUILDER          ║")
    print("╚══════════════════════════════════════════════════════════╝")

    # --------------------------------------------------------
    # Check raw directory
    # --------------------------------------------------------

    if not RAW_DIR.exists():

        print()
        print(f"❌ Raw directory does not exist:")
        print(f"   {RAW_DIR}")

        sys.exit(1)

    # --------------------------------------------------------
    # Find ALL PDFs
    # --------------------------------------------------------

    pdf_files = sorted(
        RAW_DIR.glob("*.pdf")
    )

    if not pdf_files:

        print()
        print("❌ No PDF files found.")
        print()
        print("Put your PDFs inside:")
        print(f"   {RAW_DIR}")
        print()

        sys.exit(1)

    print()
    print(f"📚 Found {len(pdf_files)} PDF file(s):")

    for pdf in pdf_files:
        print(f"   • {pdf.name}")

    # --------------------------------------------------------
    # Process PDFs
    # --------------------------------------------------------

    all_pdf_chunks = []

    next_chunk_id = PDF_START_ID

    for pdf_path in pdf_files:

        chunks, next_chunk_id = build_pdf_chunks(
            pdf_path,
            next_chunk_id
        )

        all_pdf_chunks.extend(chunks)

    # --------------------------------------------------------
    # Load website chunks
    # --------------------------------------------------------

    website_chunks, next_chunk_id = load_website_chunks(
        next_chunk_id
    )

    # --------------------------------------------------------
    # Combine
    # --------------------------------------------------------

    all_chunks = (
        all_pdf_chunks +
        website_chunks
    )

    # --------------------------------------------------------
    # Validate
    # --------------------------------------------------------

    validate_chunks(all_chunks)

    # --------------------------------------------------------
    # Save all_chunks.json
    # --------------------------------------------------------

    save_all_chunks(all_chunks)

    # --------------------------------------------------------
    # Create embeddings
    # --------------------------------------------------------

    embeddings = create_embeddings(
        all_chunks
    )

    # --------------------------------------------------------
    # Create FAISS
    # --------------------------------------------------------

    index = create_faiss_index(
        embeddings
    )

    # --------------------------------------------------------
    # Final consistency check
    # --------------------------------------------------------

    if index.ntotal != len(all_chunks):

        raise RuntimeError(
            "❌ FAISS/chunk count mismatch: "
            f"FAISS={index.ntotal}, "
            f"chunks={len(all_chunks)}"
        )

    if len(embeddings) != len(all_chunks):

        raise RuntimeError(
            "❌ Embedding/chunk count mismatch: "
            f"embeddings={len(embeddings)}, "
            f"chunks={len(all_chunks)}"
        )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    show_summary(
        pdf_files,
        all_pdf_chunks,
        website_chunks,
        embeddings,
        index
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()