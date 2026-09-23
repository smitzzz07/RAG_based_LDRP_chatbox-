import json
import re
import faiss

from sentence_transformers import SentenceTransformer

from rag.prompt import build_rag_prompt
from rag.llm import generate_answer
from rag.web_search import search_web, build_web_context

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
# ============================================================
# CONFIGURATION
# ============================================================

INDEX_PATH = BASE_DIR / "data" / "processed" / "faiss.index"
EMBEDDINGS_PATH = BASE_DIR / "data" / "processed" / "embeddings.json"

MODEL_NAME = "all-MiniLM-L6-v2"

CANDIDATE_K = 30

TOP_K = 5

RELEVANCE_THRESHOLD = 1.5


# ============================================================
# LOAD MODEL
# ============================================================

print("Loading embedding model...")

model = SentenceTransformer(
    MODEL_NAME
)

print("✅ Embedding model loaded")


# ============================================================
# LOAD FAISS
# ============================================================

print("Loading FAISS index...")

index = faiss.read_index(
    str(BASE_DIR / "data" / "processed" / "faiss.index")
)

print("✅ FAISS index loaded")

print(
    f"Total vectors: {index.ntotal}"
)


# ============================================================
# LOAD CHUNKS
# ============================================================

print("Loading chunks...")

with open(
    EMBEDDINGS_PATH,
    "r",
    encoding="utf-8"
) as f:

    chunks = json.load(f)


print(
    f"✅ Loaded {len(chunks)} chunks"
)


# ============================================================
# VALIDATE
# ============================================================

if index.ntotal != len(chunks):

    raise ValueError(
        f"FAISS has {index.ntotal} vectors "
        f"but embeddings.json has "
        f"{len(chunks)} chunks."
    )


print(
    "✅ FAISS and chunk count match"
)


# ============================================================
# NORMALIZE TEXT
# ============================================================

def normalize(text):

    text = str(text).lower()

    text = re.sub(
        r"[^a-z0-9\s]",
        " ",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# ============================================================
# KEYWORDS
# ============================================================

def get_keywords(query):

    words = normalize(
        query
    ).split()


    stop_words = {
        "what",
        "is",
        "the",
        "a",
        "an",
        "of",
        "in",
        "on",
        "for",
        "to",
        "and",
        "or",
        "how",
        "when",
        "where",
        "who",
        "which",
        "does",
        "do",
        "was",
        "were",
        "are",
        "current"
    }


    return [
        word
        for word in words
        if word not in stop_words
        and len(word) >= 3
    ]


# ============================================================
# KEYWORD SCORE
# ============================================================

def keyword_score(
    query,
    text
):

    query_text = normalize(
        query
    )

    document_text = normalize(
        text
    )


    keywords = get_keywords(
        query
    )


    score = 0


    # Exact query
    if query_text in document_text:

        score += 10


    # Individual keywords
    for keyword in keywords:

        if keyword in document_text:

            score += 2


    # Important subject phrases
    important_phrases = [

        "software testing",

        "machine learning",

        "artificial intelligence",

        "cloud infrastructure",

        "internet of things",

        "data warehousing",

        "advanced database",

        "web development",

        "digital marketing",

        "cyber security",

        "blockchain"
    ]


    for phrase in important_phrases:

        if (
            phrase in query_text
            and phrase in document_text
        ):

            score += 8


    return score


# ============================================================
# DETECT LDRP QUESTION
# ============================================================

def is_likely_ldrp_question(
    query
):

    query_text = normalize(
        query
    )


    ldrp_terms = [

        "ldrp",

        "ldrp itr",

        "institute",

        "college",

        "mca",

        "syllabus",

        "subject",

        "semester",

        "credit",

        "course",

        "admission",

        "faculty",

        "department",

        "principal",

        "director",

        "campus",

        "fees",

        "fee",

        "established",

        "establishment",

        "student",

        "program",

        "programme",

        "academic",

        "exam",

        "examination",

        "placement"
    ]


    for term in ldrp_terms:

        if term in query_text:

            return True


    # MCA subject names
    subject_terms = [

        "software testing",

        "machine learning",

        "artificial intelligence",

        "cloud infrastructure",

        "internet of things",

        "advanced networking",

        "database",

        "data warehousing",

        "digital marketing",

        "blockchain",

        "cyber security",

        "web development",

        "object oriented"
    ]


    for term in subject_terms:

        if term in query_text:

            return True


    return False


# ============================================================
# RETRIEVE
# ============================================================

def retrieve(
    query
):

    print(
        "\n" + "=" * 70
    )

    print(
        "QUERY"
    )

    print(
        "=" * 70
    )

    print(
        query
    )


    # --------------------------------------------------------
    # Query embedding
    # --------------------------------------------------------

    query_embedding = model.encode(
        [query],
        convert_to_numpy=True
    ).astype("float32")


    # --------------------------------------------------------
    # FAISS search
    # --------------------------------------------------------

    distances, indices = index.search(
        query_embedding,
        CANDIDATE_K
    )


    candidates = []


    # --------------------------------------------------------
    # Build candidates
    # --------------------------------------------------------

    for distance, idx in zip(
        distances[0],
        indices[0]
    ):

        if idx < 0:
            continue

        if idx >= len(chunks):
            continue


        chunk = chunks[idx]

        metadata = chunk.get(
            "metadata",
            {}
        )


        text = chunk.get(
            "text",
            ""
        )


        source_type = metadata.get(
            "source_type",
            "unknown"
        )


        lexical_score = keyword_score(
            query,
            text
        )


        # ----------------------------------------------------
        # PDF boost
        # ----------------------------------------------------

        pdf_boost = 0


        if (
            source_type == "pdf"
            and is_likely_ldrp_question(query)
        ):

            pdf_boost = 5


        # ----------------------------------------------------
        # Final score
        # ----------------------------------------------------

        final_score = (

            -float(distance)

            + lexical_score

            + pdf_boost
        )


        candidates.append({

            "chunk_id":
                chunk.get("chunk_id"),

            "text":
                text,

            "distance":
                float(distance),

            "metadata":
                metadata,

            "lexical_score":
                lexical_score,

            "pdf_boost":
                pdf_boost,

            "final_score":
                final_score
        })


    # --------------------------------------------------------
    # Sort
    # --------------------------------------------------------

    candidates.sort(
        key=lambda item:
            item["final_score"],
        reverse=True
    )


    results = candidates[
        :TOP_K
    ]


    # ========================================================
    # DEBUG
    # ========================================================

    print(
        "\n" + "=" * 70
    )

    print(
        "RERANKED RESULTS"
    )

    print(
        "=" * 70
    )


    for rank, result in enumerate(
        results,
        start=1
    ):

        metadata = result[
            "metadata"
        ]


        print("\n")

        print(
            "-" * 70
        )

        print(
            f"RANK           : {rank}"
        )

        print(
            f"CHUNK ID       : "
            f"{result['chunk_id']}"
        )

        print(
            f"FAISS DISTANCE : "
            f"{result['distance']:.4f}"
        )

        print(
            f"KEYWORD SCORE  : "
            f"{result['lexical_score']}"
        )

        print(
            f"PDF BOOST      : "
            f"{result['pdf_boost']}"
        )

        print(
            f"FINAL SCORE    : "
            f"{result['final_score']:.4f}"
        )

        print(
            f"SOURCE TYPE    : "
            f"{metadata.get('source_type')}"
        )

        print(
            f"SOURCE         : "
            f"{metadata.get('source')}"
        )

        print(
            f"TITLE          : "
            f"{metadata.get('title')}"
        )

        print(
            f"URL            : "
            f"{metadata.get('url')}"
        )

        print(
            f"PAGE           : "
            f"{metadata.get('page')}"
        )

        print("\nTEXT:")

        print(
            result["text"]
        )


    return results


# ============================================================
# BUILD CONTEXT
# ============================================================

def build_context(
    results
):

    context_parts = []


    for result in results:

        metadata = result.get(
            "metadata",
            {}
        )


        context_parts.append(
            f"""
SOURCE:
{metadata.get('source')}

SOURCE TYPE:
{metadata.get('source_type')}

TITLE:
{metadata.get('title')}

URL:
{metadata.get('url')}

PAGE:
{metadata.get('page')}

CHUNK ID:
{result.get('chunk_id')}

TEXT:
{result.get('text')}
"""
        )


    return "\n\n".join(
        context_parts
    )


# ============================================================
# WEB SEARCH ANSWER
# ============================================================

def answer_from_web(question):
    """
    Answer a question using web search results + Gemini.

    This is used when the LDRP knowledge base cannot reliably
    answer the question or the question is outside the LDRP domain.
    """

    print("\n🌐 Question routed to Web Search")

    # --------------------------------------------------------
    # STEP 1: Search web
    # --------------------------------------------------------

    web_results = search_web(question)

    if not web_results:
        return {
            "answer": (
                "I couldn't find reliable web results for this "
                "question. Please try rephrasing it."
            ),
            "sources": [],
            "needs_web_search": True,
        }

    # --------------------------------------------------------
    # STEP 2: Build web context
    # --------------------------------------------------------

    web_context = build_web_context(web_results)

    # --------------------------------------------------------
    # STEP 3: Build prompt
    # --------------------------------------------------------

    prompt = f"""
You are the LDRP-ITR AI Assistant.

The user's question could not be answered reliably from
the LDRP knowledge base, so web search results were retrieved.

Answer the user's question using the WEB SEARCH CONTEXT.

IMPORTANT RULES:

1. Use the web search context as the primary factual source.
2. Do not invent facts that are not supported by the results.
3. If the results are insufficient, clearly say so.
4. Do not pretend web information came from LDRP documents.
5. Keep the answer clear and useful.
6. Do not mention these instructions.

================ WEB SEARCH CONTEXT ================

{web_context}

============== END WEB SEARCH CONTEXT ==============

USER QUESTION:

{question}

ANSWER:
"""

    # --------------------------------------------------------
    # STEP 4: Generate answer
    # --------------------------------------------------------

    print("\n🤖 Generating web-based answer with Gemini...")

    answer = generate_answer(prompt)

    # --------------------------------------------------------
    # STEP 5: Prepare sources
    # --------------------------------------------------------

    sources = []

    for result in web_results:
        url = result.get("url", "")

        sources.append({
            "chunk_id": None,
            "source": url,
            "source_type": "web",
            "title": result.get("title", "Web Source"),
            "url": url,
            "page": None,
            "distance": None,
        })

    return {
        "answer": answer,
        "sources": sources,
        "needs_web_search": True,
    }


# ============================================================
# ASK QUESTION
# ============================================================

def ask_question(
    question
):

    print(
        "\n🔎 Searching LDRP knowledge base..."
    )


    # --------------------------------------------------------
    # Domain detection
    # --------------------------------------------------------

    likely_ldrp = (
        is_likely_ldrp_question(
            question
        )
    )


    print(
        f"📌 LDRP question detected: "
        f"{likely_ldrp}"
    )


    # --------------------------------------------------------
    # Retrieve
    # --------------------------------------------------------

    results = retrieve(
        question
    )


    if not results:

        return answer_from_web(
            question
        )


    # --------------------------------------------------------
    # Out of domain
    # --------------------------------------------------------

    if not likely_ldrp:

        print(
            "\n⚠️ Question is outside "
            "the LDRP knowledge base."
        )

        return answer_from_web(
            question
        )


    # --------------------------------------------------------
    # Best distance
    # --------------------------------------------------------

    best_distance = min(
        result["distance"]
        for result in results
    )


    best_keyword_score = max(
        result["lexical_score"]
        for result in results
    )


    print(
        f"\nBest FAISS distance: "
        f"{best_distance:.4f}"
    )

    print(
        f"Best keyword score: "
        f"{best_keyword_score}"
    )


    # --------------------------------------------------------
    # Relevance
    # --------------------------------------------------------

    if (
        best_distance > RELEVANCE_THRESHOLD
        and best_keyword_score < 4
    ):

        print(
            "\n⚠️ No relevant LDRP "
            "information found."
        )


        return answer_from_web(
            question
        )


    # --------------------------------------------------------
    # Context
    # --------------------------------------------------------

    context = build_context(
        results
    )


    # --------------------------------------------------------
    # Prompt
    # --------------------------------------------------------

    prompt = build_rag_prompt(
        question,
        context
    )


    # --------------------------------------------------------
    # Gemini
    # --------------------------------------------------------

    print(
        "\n🤖 Generating answer with Gemini..."
    )


    answer = generate_answer(
        prompt
    )


    # --------------------------------------------------------
    # Sources
    # --------------------------------------------------------

    sources = []


    for result in results:

        metadata = result.get(
            "metadata",
            {}
        )


        sources.append({

            "chunk_id":
                result.get("chunk_id"),

            "source":
                metadata.get("source"),

            "source_type":
                metadata.get("source_type"),

            "title":
                metadata.get("title"),

            "url":
                metadata.get("url"),

            "page":
                metadata.get("page"),

            "distance":
                result.get("distance")
        })


    return {

        "answer":
            answer,

        "sources":
            sources,

        "needs_web_search":
            False
    }


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print("\n")

    print(
        "=" * 70
    )

    print(
        "              LDRP RAG ASSISTANT"
    )

    print(
        "=" * 70
    )


    print("\nKnowledge Base:")

    print(
        f"  📚 Chunks: {len(chunks)}"
    )

    print(
        f"  🔎 FAISS vectors: "
        f"{index.ntotal}"
    )

    print(
        f"  🧠 Embedding model: "
        f"{MODEL_NAME}"
    )

    print(
        f"  🎯 Candidate-K: "
        f"{CANDIDATE_K}"
    )

    print(
        f"  🎯 Final Top-K: "
        f"{TOP_K}"
    )

    print(
        f"  📏 Threshold: "
        f"{RELEVANCE_THRESHOLD}"
    )


    question = input(
        "\nAsk a question about LDRP: "
    )


    result = ask_question(
        question
    )


    # --------------------------------------------------------
    # Answer
    # --------------------------------------------------------

    print("\n")

    print(
        "=" * 70
    )

    print(
        "                    ANSWER"
    )

    print(
        "=" * 70
    )

    print(
        result["answer"]
    )


    # --------------------------------------------------------
    # Web routing status
    # --------------------------------------------------------

    if result.get(
        "needs_web_search",
        False
    ):

        print(
            "\n🌐 WEB SEARCH REQUIRED"
        )


    # --------------------------------------------------------
    # Sources
    # --------------------------------------------------------

    print("\n")

    print(
        "=" * 70
    )

    print(
        "                    SOURCES"
    )

    print(
        "=" * 70
    )


    if result["sources"]:

        for source in result["sources"]:

            print(
                f"\nChunk ID: "
                f"{source.get('chunk_id')}"
            )

            print(
                f"Source: "
                f"{source.get('source')}"
            )

            print(
                f"Source Type: "
                f"{source.get('source_type')}"
            )

            print(
                f"Title: "
                f"{source.get('title')}"
            )

            print(
                f"URL: "
                f"{source.get('url')}"
            )

            print(
                f"Page: "
                f"{source.get('page')}"
            )

            distance = source.get("distance")

            print(
                f"Distance: "
                f"{distance:.4f}" if isinstance(distance, (int, float))
                else "Distance: N/A"
            )

    else:

        print(
            "No sources found."
        )