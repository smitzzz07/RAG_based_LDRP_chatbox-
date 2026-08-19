from pathlib import Path
import pymupdf


# Find project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# PDF location
PDF_PATH = PROJECT_ROOT / "data" / "raw" / "mca_syllabus.pdf"

# Output location
OUTPUT_PATH = PROJECT_ROOT / "data" / "raw" / "extracted_text.txt"


print("PDF path:", PDF_PATH)
print("PDF exists:", PDF_PATH.exists())


if not PDF_PATH.exists():
    print("❌ PDF not found!")
    exit()


# Open PDF
doc = pymupdf.open(PDF_PATH)

print(f"✅ PDF loaded successfully!")
print(f"Total pages: {len(doc)}")


all_text = []


# Extract text page by page
for page_number, page in enumerate(doc, start=1):

    text = page.get_text()

    all_text.append(
        f"\n========== PAGE {page_number} ==========\n"
    )

    all_text.append(text)


# Combine everything
final_text = "\n".join(all_text)


# Save extracted text
OUTPUT_PATH.write_text(
    final_text,
    encoding="utf-8"
)


print("✅ Text extraction completed!")
print(f"Characters extracted: {len(final_text)}")
print(f"Saved to: {OUTPUT_PATH}")