import re
from pathlib import Path


def clean_text(text):
    # 1. Normalize Windows/Linux line endings
    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    # 2. Remove excessive spaces/tabs
    text = re.sub(r"[ \t]+", " ", text)

    # 3. Remove excessive blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    # 4. Remove spaces at the beginning/end of lines
    lines = [line.strip() for line in text.split("\n")]

    # 5. Remove empty lines
    lines = [line for line in lines if line]

    # 6. Join lines back together
    cleaned_text = "\n".join(lines)

    return cleaned_text


if __name__ == "__main__":

    # Find project root
    PROJECT_ROOT = Path(__file__).resolve().parent.parent

    # File containing extracted raw text
    RAW_TEXT_PATH = PROJECT_ROOT / "data" / "raw" / "extracted_text.txt"

    # Output cleaned text
    CLEAN_TEXT_PATH = PROJECT_ROOT / "data" / "processed" / "cleaned_text.txt"

    # Make processed folder if it doesn't exist
    CLEAN_TEXT_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Check input file
    if not RAW_TEXT_PATH.exists():
        print("❌ extracted_text.txt not found!")
        print(f"Expected location: {RAW_TEXT_PATH}")
        exit()

    # Read raw text
    raw_text = RAW_TEXT_PATH.read_text(encoding="utf-8")

    # Clean text
    cleaned_text = clean_text(raw_text)

    # Save cleaned text
    CLEAN_TEXT_PATH.write_text(cleaned_text, encoding="utf-8")

    print("✅ Text cleaning completed!")
    print(f"Raw characters: {len(raw_text)}")
    print(f"Clean characters: {len(cleaned_text)}")
    print(f"Saved to: {CLEAN_TEXT_PATH}")