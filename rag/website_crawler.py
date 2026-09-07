from pathlib import Path
import json
import requests

from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse


# ==================================================
# PROJECT PATHS
# ==================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

OUTPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "website_pages.json"
)


# ==================================================
# SETTINGS
# ==================================================

BASE_URL = "https://ldrp.ac.in"

MAX_PAGES = 30

TIMEOUT = 20


# ==================================================
# HEADERS
# ==================================================

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/151.0 Safari/537.36"
    )
}


# ==================================================
# CHECK LDRP URL
# ==================================================

def is_same_domain(url):

    base_domain = urlparse(BASE_URL).netloc

    current_domain = urlparse(url).netloc

    return current_domain == base_domain


# ==================================================
# NORMALIZE URL
# ==================================================

def normalize_url(url):

    url = url.split("#")[0]

    return url.rstrip("/")


# ==================================================
# DOWNLOAD PAGE
# ==================================================

def download_page(url):

    try:

        response = requests.get(
            url,
            headers=HEADERS,
            timeout=TIMEOUT
        )

        response.raise_for_status()

        return response.text

    except requests.RequestException as e:

        print(
            f"⚠️ Failed: {url}"
        )

        print(
            f"   {e}"
        )

        return None


# ==================================================
# EXTRACT PAGE
# ==================================================

def extract_page(html, url):

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    # ----------------------------------------------
    # Title
    # ----------------------------------------------

    title = ""

    if soup.title:

        title = soup.title.get_text(
            " ",
            strip=True
        )

    # ----------------------------------------------
    # Remove unwanted elements
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
    # Main content
    # ----------------------------------------------

    main_content = (
        soup.find("main")
        or soup.find("article")
        or soup.find("body")
    )

    if main_content is None:

        return title, "", []

    # ----------------------------------------------
    # Extract text
    # ----------------------------------------------

    text = main_content.get_text(
        separator="\n",
        strip=True
    )

    # ----------------------------------------------
    # Clean text
    # ----------------------------------------------

    lines = []

    for line in text.splitlines():

        line = line.strip()

        if line:

            lines.append(line)

    # Remove immediate duplicates

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

    # ----------------------------------------------
    # Extract links
    # ----------------------------------------------

    links = []

    for link in soup.find_all("a"):

        href = link.get("href")

        if not href:

            continue

        absolute_url = urljoin(
            url,
            href
        )

        absolute_url = normalize_url(
            absolute_url
        )

        if is_same_domain(
            absolute_url
        ):

            links.append(
                absolute_url
            )

    return title, text, links


# ==================================================
# CRAWLER
# ==================================================

def crawl_website():

    visited = set()

    queue = [
        normalize_url(BASE_URL)
    ]

    pages = []

    while queue and len(pages) < MAX_PAGES:

        current_url = queue.pop(0)

        current_url = normalize_url(
            current_url
        )

        # ------------------------------------------
        # Skip already visited
        # ------------------------------------------

        if current_url in visited:

            continue

        visited.add(
            current_url
        )

        print(
            f"\n[{len(pages) + 1}/{MAX_PAGES}] "
            f"Crawling:"
        )

        print(
            current_url
        )

        # ------------------------------------------
        # Download
        # ------------------------------------------

        html = download_page(
            current_url
        )

        if html is None:

            continue

        # ------------------------------------------
        # Extract
        # ------------------------------------------

        title, text, links = extract_page(
            html,
            current_url
        )

        # ------------------------------------------
        # Save page
        # ------------------------------------------

        if text:

            pages.append({

                "source":
                    "LDRP-ITR Official Website",

                "source_type":
                    "website",

                "url":
                    current_url,

                "title":
                    title,

                "text":
                    text

            })

            print(
                f"✅ Extracted "
                f"{len(text)} characters"
            )

        else:

            print(
                "⚠️ No text found"
            )

        # ------------------------------------------
        # Add new links
        # ------------------------------------------

        for link in links:

            if (
                link not in visited
                and link not in queue
            ):

                queue.append(
                    link
                )

    return pages


# ==================================================
# MAIN
# ==================================================

def main():

    print("=" * 60)

    print(
        "       LDRP RAG - WEBSITE CRAWLER"
    )

    print("=" * 60)

    print(
        f"\nStarting URL: {BASE_URL}"
    )

    print(
        f"Maximum pages: {MAX_PAGES}"
    )

    # ----------------------------------------------
    # Crawl
    # ----------------------------------------------

    pages = crawl_website()

    print(
        "\n" + "=" * 60
    )

    print(
        "CRAWLING COMPLETED"
    )

    print(
        "=" * 60
    )

    print(
        f"\nPages collected: {len(pages)}"
    )

    # ----------------------------------------------
    # Create directory
    # ----------------------------------------------

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    # ----------------------------------------------
    # Save
    # ----------------------------------------------

    OUTPUT_PATH.write_text(

        json.dumps(
            pages,
            indent=2,
            ensure_ascii=False
        ),

        encoding="utf-8"
    )

    print(
        "\n✅ Website pages saved!"
    )

    print(
        f"Location:\n{OUTPUT_PATH}"
    )

    # ----------------------------------------------
    # Summary
    # ----------------------------------------------

    print(
        "\n" + "=" * 60
    )

    print(
        "PAGES"
    )

    print(
        "=" * 60
    )

    for index, page in enumerate(pages):

        print(
            f"\n{index + 1}. "
            f"{page['title']}"
        )

        print(
            f"   {page['url']}"
        )

        print(
            f"   Characters: "
            f"{len(page['text'])}"
        )


# ==================================================
# RUN
# ==================================================

if __name__ == "__main__":

    main()