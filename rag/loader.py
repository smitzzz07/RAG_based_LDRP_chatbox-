from pathlib import Path
import json
import pymupdf


# ==================================================
# LDRP RAG - MULTI PDF LOADER
# ==================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

RAW_DIR = PROJECT_ROOT / "data" / "raw"

EXTRACTED_PAGES_PATH = RAW_DIR / "extracted_pages.json"
EXTRACTED_TEXT_PATH = RAW_DIR / "extracted_text.txt"


def extract_all_pdfs():

    pdf_files = sorted(
        p for p in RAW_DIR.glob("*.pdf")
        if p.is_file()
    )

    if not pdf_files:
        print("❌ No PDF files found in data/raw/")
        return []

    all_pages = []
    text_parts = []

    print("=" * 70)
    print("       LDRP RAG - MULTI PDF LOADER")
    print("=" * 70)

    print(f"PDF directory: {RAW_DIR}")
    print(f"PDF files found: {len(pdf_files)}")

    total_pages = 0

    for pdf_path in pdf_files:

        print("\n" + "-" * 70)
        print(f"📄 Processing: {pdf_path.name}")

        try:
            doc = pymupdf.open(pdf_path)

        except Exception as error:
            print(
                f"❌ Could not open {pdf_path.name}: {error}"
            )
            continue

        print(f"   Pages: {len(doc)}")

        for page_number, page in enumerate(
            doc,
            start=1
        ):

            text = page.get_text().strip()

            if not text:
                continue

            total_pages += 1

            page_record = {
                "source": pdf_path.name,
                "source_type": "pdf",
                "title": pdf_path.stem.replace(
                    "_",
                    " "
                ).replace(
                    "-",
                    " "
                ).strip(),
                "page": page_number,
                "text": text
            }

            all_pages.append(page_record)

            text_parts.append(
                f"\n========== "
                f"SOURCE: {pdf_path.name} "
                f"| PAGE {page_number} "
                f"==========\n"
            )

            text_parts.append(text)

        doc.close()

        print("   ✅ Extracted")

    RAW_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    EXTRACTED_PAGES_PATH.write_text(
        json.dumps(
            all_pages,
            indent=2,
            ensure_ascii=False
        ),
        encoding="utf-8"
    )

    EXTRACTED_TEXT_PATH.write_text(
        "\n".join(text_parts),
        encoding="utf-8"
    )

    print("\n" + "=" * 70)
    print("PDF EXTRACTION COMPLETE")
    print("=" * 70)

    print(
        f"📄 PDF files processed : {len(pdf_files)}"
    )

    print(
        f"📑 Pages with text     : {total_pages}"
    )

    print(
        f"📝 Page records        : {len(all_pages)}"
    )

    print(
        f"📁 Saved               : "
        f"{EXTRACTED_PAGES_PATH}"
    )

    print(
        f"📁 Legacy text         : "
        f"{EXTRACTED_TEXT_PATH}"
    )

    print("=" * 70)

    return all_pages


if __name__ == "__main__":
    extract_all_pdfs()