from pathlib import Path
import pymupdf


# ==================================================
# PROJECT PATHS
# ==================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

PDF_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "mca_syllabus.pdf"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "extracted_text.txt"
)


# ==================================================
# CHECK PDF
# ==================================================

print("==============================================")
print("        LDRP RAG - PDF LOADER")
print("==============================================")

print(
    f"PDF path: {PDF_PATH}"
)

print(
    f"PDF exists: {PDF_PATH.exists()}"
)


if not PDF_PATH.exists():

    print("❌ PDF not found!")

    exit()


# ==================================================
# OPEN PDF
# ==================================================

doc = pymupdf.open(
    PDF_PATH
)

print(
    "\n✅ PDF loaded successfully!"
)

print(
    f"Total pages: {len(doc)}"
)


# ==================================================
# EXTRACT PAGE BY PAGE
# ==================================================

all_text = []


for page_number, page in enumerate(
    doc,
    start=1
):

    print(
        f"Extracting page {page_number}/{len(doc)}..."
    )

    text = page.get_text()

    # ----------------------------------------------
    # Add explicit page marker
    # ----------------------------------------------

    all_text.append(
        f"\n"
        f"========== PAGE {page_number} ==========\n"
    )

    all_text.append(
        text
    )


# ==================================================
# COMBINE TEXT
# ==================================================

final_text = "\n".join(
    all_text
)


# ==================================================
# SAVE
# ==================================================

OUTPUT_PATH.write_text(
    final_text,
    encoding="utf-8"
)


# ==================================================
# CLOSE PDF
# ==================================================

doc.close()


# ==================================================
# RESULT
# ==================================================

print("\n==============================================")

print(
    "✅ Text extraction completed!"
)

print(
    f"Characters extracted: {len(final_text)}"
)

print(
    f"Saved to: {OUTPUT_PATH}"
)

print("==============================================")