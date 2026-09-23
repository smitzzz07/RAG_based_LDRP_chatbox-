from ddgs import DDGS


# ============================================================
# WEB SEARCH CONFIGURATION
# ============================================================

MAX_RESULTS = 5


# ============================================================
# SEARCH WEB
# ============================================================

def search_web(query, max_results=MAX_RESULTS):
    """
    Search the public web and normalize the results.
    """

    print("\n🌐 Searching the web...")
    print(f"🔎 Query: {query}")

    try:
        results = DDGS().text(
            query,
            region="in-en",
            safesearch="moderate",
            max_results=max_results,
        )

        normalized_results = []

        for result in results:
            title = result.get("title", "")
            url = result.get("href", "")
            snippet = result.get("body", "")

            if not title and not url:
                continue

            normalized_results.append({
                "title": title,
                "url": url,
                "snippet": snippet,
            })

        print(
            f"✅ Web results found: "
            f"{len(normalized_results)}"
        )

        return normalized_results

    except Exception as error:
        print(
            f"❌ Web search failed: "
            f"{type(error).__name__}: {error}"
        )
        return []


# ============================================================
# BUILD WEB CONTEXT
# ============================================================

def build_web_context(results):
    context_parts = []

    for index, result in enumerate(results, start=1):
        context_parts.append(
            f"""
WEB SOURCE {index}

TITLE:
{result.get("title", "")}

URL:
{result.get("url", "")}

SNIPPET:
{result.get("snippet", "")}
"""
        )

    return "\n\n".join(context_parts)


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    question = input(
        "Search the web: "
    ).strip()

    results = search_web(question)

    print("\n" + "=" * 70)
    print("WEB SEARCH RESULTS")
    print("=" * 70)

    for index, result in enumerate(results, start=1):
        print(
            f"\n{index}. {result['title']}"
        )
        print(result["url"])
        print(result["snippet"])
