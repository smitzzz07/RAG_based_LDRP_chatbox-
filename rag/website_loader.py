from pathlib import Path
import json
import requests
from bs4 import BeautifulSoup


# ==================================================
# PROJECT PATHS
# ==================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

OUTPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "website_data.json"
)


# ==================================================
# OFFICIAL LDRP WEBSITE
# ==================================================

URL = "https://ldrp.ac.in/index.html"


# ==================================================
# LOAD WEBSITE
# ==================================================

def load_website(url):

    headers = {
        "User-Agent": (
            "Mozilla/5.0 "
            "(Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/151.0 Safari/537.36"
        )
    }

    response = requests.get(
        url,
        headers=headers,
        timeout=20
    )

    response.raise_for_status()

    # Force UTF-8 decoding because the current
    # website content contains UTF-8 characters.
    html = response.content.decode(
        "utf-8",
        errors="replace"
    )

    return html


# ==================================================
# EXTRACT WEBSITE TEXT
# ==================================================

def extract_text(html):

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    # ----------------------------------------------
    # Get page title
    # ----------------------------------------------

    title = ""

    if soup.title:

        title = soup.title.get_text(
            " ",
            strip=True
        )

    # ----------------------------------------------
    # Remove non-content elements
    # ----------------------------------------------

    for tag in soup([
        "script",
        "style",
        "noscript",
        "nav",
        "footer"
    ]):

        tag.decompose()

    # ----------------------------------------------
    # Prefer main content
    # ----------------------------------------------

    main_content = (
        soup.find("main")
        or soup.find("article")
        or soup.find("body")
    )

    if main_content is None:

        return title, ""

    # ----------------------------------------------
    # Extract visible text
    # ----------------------------------------------

    text = main_content.get_text(
        separator="\n",
        strip=True
    )

    # ----------------------------------------------
    # Clean lines
    # ----------------------------------------------

    lines = []

    for line in text.splitlines():

        line = line.strip()

        if not line:
            continue

        lines.append(line)

    # ----------------------------------------------
    # Remove immediate duplicates
    # ----------------------------------------------

    cleaned_lines = []

    for line in lines:

        if (
            not cleaned_lines
            or cleaned_lines[-1] != line
        ):

            cleaned_lines.append(line)

    text = "\n".join(
        cleaned_lines
    )

    return title, text


# ==================================================
# MAIN
# ==================================================

def main():

    print("=" * 60)

    print(
        "       LDRP RAG - WEBSITE LOADER"
    )

    print("=" * 60)

    print(
        f"\nURL: {URL}"
    )

    try:

        # ------------------------------------------
        # Download website
        # ------------------------------------------

        html = load_website(
            URL
        )

        print(
            "\n✅ Website downloaded successfully"
        )

        # ------------------------------------------
        # Extract text
        # ------------------------------------------

        title, text = extract_text(
            html
        )

        print(
            "✅ Website text extracted"
        )

        # ------------------------------------------
        # Build JSON
        # ------------------------------------------

        data = {

            "source":
                "LDRP-ITR Official Website",

            "url":
                URL,

            "title":
                title,

            "text":
                text
        }

        # ------------------------------------------
        # Create output directory
        # ------------------------------------------

        OUTPUT_PATH.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        # ------------------------------------------
        # Save JSON
        # ------------------------------------------

        OUTPUT_PATH.write_text(

            json.dumps(
                data,
                indent=2,
                ensure_ascii=False
            ),

            encoding="utf-8"
        )

        # ------------------------------------------
        # Result
        # ------------------------------------------

        print(
            "\n✅ Website ingestion completed!"
        )

        print(
            f"Title: {title}"
        )

        print(
            f"Characters extracted: {len(text)}"
        )

        print(
            f"Saved to:\n{OUTPUT_PATH}"
        )

        print(
            "\n" + "=" * 60
        )

        print(
            "TEXT PREVIEW"
        )

        print(
            "=" * 60
        )

        print(
            text[:2000]
        )

    except requests.exceptions.RequestException as e:

        print(
            "\n❌ Website request failed"
        )

        print(
            f"Error: {e}"
        )

    except Exception as e:

        print(
            "\n❌ Unexpected error"
        )

        print(
            "\nType:",
            type(e).__name__
        )

        print(
            "Error:",
            e
        )


# ==================================================
# RUN
# ==================================================

if __name__ == "__main__":

    main()