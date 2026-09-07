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
    / "website_pages.json"
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

START_CHUNK_ID = 1000


# ==================================================
# LOAD WEBSITE PAGES
# ==================================================

with open(INPUT_PATH, "r", encoding="utf-8") as f:
    pages = json.load(f)

print(f"Total website pages: {len(pages)}")


# ==================================================
# CHUNK FUNCTION
# ==================================================

def create_chunks(text, chunk_size=500, overlap=100):

    text = re.sub(r"\s+", " ", text).strip()

    chunks = []

    start = 0

    while start < len(text):

        end = start + chunk_size

        # Try to end at a sentence
        if end < len(text):

            sentence_end = text.rfind(". ", start, end)

            if sentence_end > start + 200:
                end = sentence_end + 1

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        next_start = end - overlap

        if next_start <= start:
            break

        start = next_start

    return chunks


# ==================================================
# PROCESS ALL PAGES
# ==================================================

all_chunks = []

chunk_id = START_CHUNK_ID


for page in pages:

    url = page.get("url", "")
    title = page.get("title", "")
    text = page.get("text", "")

    if not text.strip():
        continue

    page_chunks = create_chunks(
        text,
        CHUNK_SIZE,
        CHUNK_OVERLAP
    )

    for chunk in page_chunks:

        all_chunks.append({
            "chunk_id": chunk_id,
            "text": chunk,

            "metadata": {
                "source": "LDRP-ITR Official Website",
                "source_type": "website",
                "url": url,
                "title": title,
                "chunk_size": len(chunk)
            }
        })

        chunk_id += 1


# ==================================================
# SAVE
# ==================================================

OUTPUT_PATH.parent.mkdir(
    parents=True,
    exist_ok=True
)

with open(
    OUTPUT_PATH,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        all_chunks,
        f,
        indent=2,
        ensure_ascii=False
    )


# ==================================================
# RESULT
# ==================================================

print()
print("======================================")
print("Website Chunking Completed")
print("======================================")

print(f"Pages processed : {len(pages)}")
print(f"Total chunks    : {len(all_chunks)}")
print(f"Output          : {OUTPUT_PATH}")