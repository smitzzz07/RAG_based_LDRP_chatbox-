import json
import re
from pathlib import Path

import faiss
from sentence_transformers import SentenceTransformer

from rag.prompt import build_rag_prompt
from rag.llm import generate_answer
from rag.web_search import search_web, build_web_context


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

INDEX_PATH = BASE_DIR / "data" / "processed" / "faiss.index"
CHUNKS_PATH = BASE_DIR / "data" / "processed" / "all_chunks.json"

MODEL_NAME = "all-MiniLM-L6-v2"

# Initial semantic search
CANDIDATE_K = 30

# Number of chunks finally sent to the LLM
TOP_K = 5
DIRECTORY_OVERVIEW_K = 20

# FAISS distance threshold
RELEVANCE_THRESHOLD = 1.5

# Minimum final relevance score
MIN_FINAL_SCORE = 1.5

# Normal questions may not be much weaker than the best result
MAX_SCORE_GAP = 5.0

# Structured PDFs may need several chunks from the same document.
STRUCTURED_INTENTS = {
    "holiday",
    "contact",
    "faculty",
}


# ============================================================
# CONSTANTS
# ============================================================

MONTHS = [
    "january",
    "february",
    "march",
    "april",
    "may",
    "june",
    "july",
    "august",
    "september",
    "october",
    "november",
    "december",
]


# ============================================================
# LOAD EMBEDDING MODEL
# ============================================================

print("Loading embedding model...")

model = SentenceTransformer(MODEL_NAME)

print("✅ Embedding model loaded")


# ============================================================
# LOAD FAISS INDEX
# ============================================================

print("Loading FAISS index...")

index = faiss.read_index(str(INDEX_PATH))

print("✅ FAISS index loaded")
print(f"Total vectors: {index.ntotal}")


# ============================================================
# LOAD CHUNKS
# ============================================================

print("Loading chunks...")

with open(CHUNKS_PATH, "r", encoding="utf-8") as f:
    chunks = json.load(f)

print(f"✅ Loaded {len(chunks)} chunks")


# ============================================================
# VALIDATION
# ============================================================

if index.ntotal != len(chunks):
    raise ValueError(
        f"FAISS has {index.ntotal} vectors but "
        f"all_chunks.json has {len(chunks)} chunks."
    )

print("✅ FAISS and chunk count match")


# ============================================================
# COMMON HELPERS
# ============================================================

def normalize(text):
    """Normalize text for keyword matching."""
    text = str(text or "").lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def get_keywords(query):
    """Extract useful query keywords."""
    words = normalize(query).split()

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
        "can",
        "could",
        "give",
        "tell",
        "me",
        "please",
        "about",
        "from",
        "with",
        "current",
        "information",
        "there",
        "many",
        "much",
    }

    return [
        word
        for word in words
        if word not in stop_words and len(word) >= 3
    ]


def get_requested_month(query):
    """Return the month explicitly mentioned in the question."""
    query_text = normalize(query)

    for month in MONTHS:
        if month in query_text:
            return month

    return None


def get_requested_department(query):
    """
    Return a known department explicitly mentioned in the query.

    This currently focuses on MCA because the LDRP intercom
    directory contains a structured MCA section.
    """
    query_text = normalize(query)

    if "mca" in query_text:
        return "mca"

    if "computer science" in query_text or "cs department" in query_text:
        return "computer science"

    if "electrical" in query_text:
        return "electrical"

    if "mechanical" in query_text:
        return "mechanical"

    if "civil" in query_text:
        return "civil"

    if "ec department" in query_text or "electronics" in query_text:
        return "ec"

    return None


# ============================================================
# KEYWORD SCORE
# ============================================================

def keyword_score(query, text):
    query_text = normalize(query)
    document_text = normalize(text)

    keywords = get_keywords(query)

    score = 0

    # Exact complete query
    if query_text and query_text in document_text:
        score += 10

    # Individual keywords
    for keyword in keywords:
        if keyword in document_text:
            score += 2

    # Important phrases
    important_phrases = [
        "software testing",
        "quality assurance",
        "machine learning",
        "artificial intelligence",
        "cloud infrastructure",
        "internet of things",
        "advanced database",
        "database management",
        "data warehousing",
        "advanced networking",
        "digital marketing",
        "cyber security",
        "web development",
        "object oriented",
        "object oriented programming",
        "blockchain",
        "mca faculty",
        "faculty",
        "professor",
        "teaching staff",
        "department",
        "name of faculty",
        "names of faculty",
        "names listed under",
    ]

    for phrase in important_phrases:
        if phrase in query_text and phrase in document_text:
            score += 8

    return score


# ============================================================
# QUERY INTENT
# ============================================================

def detect_query_intent(query):
    query_text = normalize(query)

    # --------------------------------------------------------
    # FACULTY
    # --------------------------------------------------------

    # --------------------------------------------------------
    # CONTACT / INTERCOM / DIRECTORY
    # Check this BEFORE faculty because queries such as
    # "all department contact list" contain the word
    # "department" but are actually directory requests.
    # --------------------------------------------------------

    contact_terms = [
        "intercom",
        "extension",
        "telephone",
        "phone",
        "contact number",
        "directory",
        "contact list",
        "department contact",
        "department contacts",
        "contact",
        "exam room",
    ]

    if any(term in query_text for term in contact_terms):
        return "contact"

    # --------------------------------------------------------
    # FACULTY
    # --------------------------------------------------------

    faculty_terms = [
        "faculty",
        "professor",
        "teacher",
        "teaching staff",
        "staff",
        "hod",
        "head of department",
        "lecturer",
        "assistant professor",
        "associate professor",
        "mca faculty",
        "names of faculty",
        "name of faculty",
    ]

    if any(term in query_text for term in faculty_terms):
        return "faculty"

    # --------------------------------------------------------
    # HOLIDAY
    # --------------------------------------------------------

    holiday_terms = [
        "holiday",
        "holidays",
        "public holiday",
        "public holidays",
        "holiday list",
        "academic calendar",
        "calendar",
    ]

    if any(term in query_text for term in holiday_terms):
        return "holiday"

    # --------------------------------------------------------
    # MCA ACADEMIC
    # --------------------------------------------------------

    academic_terms = [
        "mca",
        "syllabus",
        "subject",
        "semester",
        "credit",
        "course",
        "software testing",
        "quality assurance",
        "machine learning",
        "artificial intelligence",
        "database",
        "data warehousing",
        "advanced networking",
        "cloud",
        "internet of things",
        "digital marketing",
        "cyber security",
        "blockchain",
        "web development",
    ]

    if any(term in query_text for term in academic_terms):
        return "academic"

    # --------------------------------------------------------
    # GENERAL LDRP
    # --------------------------------------------------------

    ldrp_terms = [
        "ldrp",
        "ldrp itr",
        "institute",
        "college",
        "campus",
        "admission",
        "fees",
        "fee",
        "principal",
        "director",
        "student",
        "placement",
        "examination",
        "exam",
        "academic",
        "program",
        "programme",
        "established",
        "establishment",
        "ksv",
        "kadi sarva vishwavidyalaya",
        "sarva vishwavidyalaya",
    ]

    if any(term in query_text for term in ldrp_terms):
        return "ldrp"

    return "unknown"


def is_likely_ldrp_question(query):
    return detect_query_intent(query) != "unknown"


def select_best_source(query, candidates, intent):
    """
    Select the best source for structured questions.

    Important for directory/faculty questions:
    a semantic search can incorrectly prefer the MCA website
    even when the user explicitly asks about the intercom
    directory. In that case, search all chunks for a matching
    directory PDF and choose that source before source-wide
    expansion.
    """

    if not candidates:
        return "", ""

    # Default: the best reranked candidate.
    best = candidates[0]
    best_source = best["metadata"].get("source", "")
    best_source_type = best["metadata"].get("source_type", "")

    query_text = normalize(query)

    # --------------------------------------------------------
    # Explicit directory/intercom request
    # --------------------------------------------------------
    # If the user explicitly asks for an Intercom List or
    # directory, prefer the matching PDF source even if the
    # MCA website has a stronger semantic score.
    # --------------------------------------------------------

    if intent in {"faculty", "contact"} and any(
        term in query_text
        for term in [
            "intercom",
            "directory",
            "intercom list",
            "name of faculty",
            "names listed under",
        ]
    ):

        source_scores = {}

        for idx, chunk in enumerate(chunks):
            metadata = chunk.get("metadata", {})
            source = metadata.get("source", "") or ""
            source_type = metadata.get("source_type", "") or ""
            title = metadata.get("title", "") or ""

            if not source:
                continue

            source_text = normalize(f"{source} {title}")
            chunk_text = normalize(chunk.get("text", ""))

            score = 0

            # Strongly prefer an intercom/directory PDF.
            if source_type == "pdf":
                score += 20

            if "intercom" in source_text:
                score += 60

            if "directory" in source_text:
                score += 50

            if "mca" in query_text and "mca" in chunk_text:
                score += 35

            if "name of faculty" in chunk_text:
                score += 30

            if "phone no" in chunk_text or "phone number" in chunk_text:
                score += 15

            if "department" in chunk_text:
                score += 10

            # Use the strongest matching chunk to represent the source.
            previous = source_scores.get(source)
            if previous is None or score > previous["score"]:
                source_scores[source] = {
                    "score": score,
                    "source_type": source_type,
                    "title": title,
                }

        if source_scores:
            preferred_source, info = max(
                source_scores.items(),
                key=lambda item: item[1]["score"],
            )

            if info["score"] > 0:
                print(
                    "\n🎯 Explicit directory/contact source selection enabled"
                )
                print(
                    f"📌 Selected structured source: {preferred_source}"
                )
                print(
                    f"📌 Source selection score: {info['score']}"
                )
                return preferred_source, info["source_type"]

    return best_source, best_source_type


# ============================================================
# SOURCE RELEVANCE BOOST
# ============================================================

def source_relevance_boost(query, metadata, text):
    query_text = normalize(query)

    source = normalize(metadata.get("source", ""))
    title = normalize(metadata.get("title", ""))
    url = normalize(metadata.get("url", ""))

    document_text = normalize(text)

    combined_source = f"{source} {title} {url}"

    intent = detect_query_intent(query)

    boost = 0

    # --------------------------------------------------------
    # FACULTY
    # --------------------------------------------------------

    if intent == "faculty":

        source_terms = [
            "faculty",
            "staff",
            "department",
            "teacher",
            "professor",
            "academic",
            "mca",
        ]

        if any(term in combined_source for term in source_terms):
            boost += 12

        faculty_text_terms = [
            "professor",
            "assistant professor",
            "associate professor",
            "faculty",
            "hod",
            "head of department",
            "teaching staff",
        ]

        if any(term in document_text for term in faculty_text_terms):
            boost += 8

        # Strong department-specific boost.
        requested_department = get_requested_department(query)

        if requested_department == "mca":
            if "mca" in document_text:
                boost += 30

            # The directory uses a table header such as
            # "Department / Name of faculty / Phone No."
            if "name of faculty" in document_text:
                boost += 15

        if "names listed under" in query_text:
            if "department" in document_text:
                boost += 8

    # --------------------------------------------------------
    # HOLIDAY
    # --------------------------------------------------------

    elif intent == "holiday":

        source_terms = [
            "holiday",
            "calendar",
        ]

        if any(term in combined_source for term in source_terms):
            boost += 12

        if any(
            term in document_text
            for term in [
                "holiday",
                "public holiday",
                "calendar",
            ]
        ):
            boost += 5

    # --------------------------------------------------------
    # CONTACT / INTERCOM
    # --------------------------------------------------------

    elif intent == "contact":

        source_terms = [
            "intercom",
            "directory",
            "telephone",
            "contact",
            "department",
        ]

        if any(term in combined_source for term in source_terms):
            boost += 12

        if any(
            term in document_text
            for term in [
                "extension",
                "intercom",
                "telephone",
                "phone",
            ]
        ):
            boost += 5

    # --------------------------------------------------------
    # ACADEMIC / MCA
    # --------------------------------------------------------

    elif intent == "academic":

        source_terms = [
            "mca",
            "syllabus",
            "academic",
        ]

        if any(term in combined_source for term in source_terms):
            boost += 10

        if any(
            term in document_text
            for term in [
                "semester",
                "credit",
                "subject",
                "course",
                "mca",
            ]
        ):
            boost += 4

    # --------------------------------------------------------
    # GENERAL LDRP
    # --------------------------------------------------------

    elif intent == "ldrp":

        if "ldrp" in combined_source:
            boost += 6

        if "ksv" in combined_source:
            boost += 4

    return boost


# ============================================================
# INTENT BOOST
# ============================================================

def calculate_intent_boost(query, text, intent):
    """
    Extra score for information that directly answers a
    structured question.
    """

    normalized_query = normalize(query)
    normalized_text = normalize(text)

    boost = 0

    # --------------------------------------------------------
    # HOLIDAY
    # --------------------------------------------------------

    if intent == "holiday":

        requested_month = get_requested_month(query)

        if requested_month and requested_month in normalized_text:
            boost += 25

        if "holiday" in normalized_text:
            boost += 4

        if "public holiday" in normalized_text:
            boost += 4

        if "date" in normalized_text:
            boost += 2

    # --------------------------------------------------------
    # CONTACT
    # --------------------------------------------------------

    elif intent == "contact":

        contact_terms = [
            "extension",
            "intercom",
            "telephone",
            "phone",
            "exam room",
            "directory",
        ]

        for term in contact_terms:
            if term in normalized_query and term in normalized_text:
                boost += 15

        if (
            "all department" in normalized_query
            or "all departments" in normalized_query
            or "department contact" in normalized_query
            or "department contacts" in normalized_query
            or "contact list" in normalized_query
        ):
            if "ldrp institute intercomm list" in normalized_text:
                boost += 40
            if "name of faculty" in normalized_text:
                boost += 25
            if "phone no" in normalized_text:
                boost += 20

    # --------------------------------------------------------
    # FACULTY
    # --------------------------------------------------------

    elif intent == "faculty":

        faculty_terms = [
            "faculty",
            "professor",
            "assistant professor",
            "associate professor",
            "hod",
            "head of department",
            "teacher",
            "teaching staff",
        ]

        for term in faculty_terms:
            if term in normalized_text:
                boost += 10

        # Critical fix:
        # MCA faculty questions must prefer chunks that
        # actually contain the MCA department marker.
        requested_department = get_requested_department(query)

        if requested_department == "mca":
            if "mca" in normalized_text:
                boost += 30

            if "name of faculty" in normalized_text:
                boost += 15

            if "department" in normalized_text:
                boost += 8

    # --------------------------------------------------------
    # ACADEMIC
    # --------------------------------------------------------

    elif intent == "academic":

        academic_terms = [
            "mca",
            "semester",
            "subject",
            "credit",
            "course",
            "syllabus",
        ]

        for term in academic_terms:
            if term in normalized_query and term in normalized_text:
                boost += 5

    return boost


# ============================================================
# CREATE RESULT
# ============================================================

def make_candidate(idx, query, query_vector, intent):
    """Build one reranked candidate from all_chunks.json."""

    if idx < 0 or idx >= len(chunks):
        return None

    chunk = chunks[idx]

    metadata = chunk.get("metadata", {})
    text = chunk.get("text", "")

    chunk_vector = index.reconstruct(int(idx))

    difference = query_vector - chunk_vector

    # Squared L2 distance, same metric used by FAISS IndexFlatL2.
    distance = float((difference * difference).sum())

    lexical = keyword_score(
        query,
        text,
    )

    source_boost = source_relevance_boost(
        query,
        metadata,
        text,
    )

    intent_boost = calculate_intent_boost(
        query,
        text,
        intent,
    )

    final_score = (
        -distance
        + lexical
        + source_boost
        + intent_boost
    )

    return {
        "index": int(idx),
        "chunk_id": chunk.get("chunk_id"),
        "text": text,
        "distance": distance,
        "metadata": metadata,
        "lexical_score": lexical,
        "source_boost": source_boost,
        "intent_boost": intent_boost,
        "final_score": final_score,
    }


# ============================================================
# RETRIEVE
# ============================================================

def retrieve(query):

    print("\n" + "=" * 70)
    print("QUERY")
    print("=" * 70)
    print(query)

    intent = detect_query_intent(query)

    print(f"🎯 Query intent: {intent}")

    # ========================================================
    # STEP 1: QUERY EMBEDDING
    # ========================================================

    query_embedding = model.encode(
        [query],
        convert_to_numpy=True,
    ).astype("float32")

    query_vector = query_embedding[0]

    # ========================================================
    # STEP 2: INITIAL FAISS SEARCH
    # ========================================================

    distances, indices = index.search(
        query_embedding,
        CANDIDATE_K,
    )

    candidates = []

    for distance, idx in zip(
        distances[0],
        indices[0],
    ):

        if idx < 0 or idx >= len(chunks):
            continue

        candidate = make_candidate(
            int(idx),
            query,
            query_vector,
            intent,
        )

        if candidate is not None:
            candidates.append(candidate)

    if not candidates:
        return []

    # ========================================================
    # STEP 3: SORT INITIAL RESULTS
    # ========================================================

    candidates.sort(
        key=lambda item: item["final_score"],
        reverse=True,
    )

    # ========================================================
    # STEP 4: BEST SOURCE
    # ========================================================

    best_source, best_source_type = select_best_source(
        query,
        candidates,
        intent,
    )

    print(f"\n📚 Best source: {best_source}")

    # ========================================================
    # STEP 5: SOURCE-WIDE EXPANSION
    # ========================================================
    #
    # For holiday lists, directories and faculty documents,
    # searching only the top 30 FAISS candidates is not enough.
    #
    # We scan ALL chunks belonging to the best document.
    # ========================================================

    if (
        intent in STRUCTURED_INTENTS
        and best_source
        and best_source_type == "pdf"
    ):

        print("\n🔎 Source-wide expansion enabled")
        print(f"📄 Source: {best_source}")

        existing_indexes = {
            item["index"]
            for item in candidates
        }

        source_indexes = []

        for idx, chunk in enumerate(chunks):

            metadata = chunk.get(
                "metadata",
                {},
            )

            source = metadata.get(
                "source",
                "",
            )

            if source == best_source:
                source_indexes.append(idx)

        print(
            f"📚 Total chunks in source: "
            f"{len(source_indexes)}"
        )

        source_chunks_added = 0

        for idx in source_indexes:

            if idx in existing_indexes:
                continue

            candidate = make_candidate(
                idx,
                query,
                query_vector,
                intent,
            )

            if candidate is None:
                continue

            candidates.append(candidate)
            source_chunks_added += 1

        print(
            f"📚 Added {source_chunks_added} "
            f"same-source chunks"
        )

    # ========================================================
    # STEP 6: SORT ALL CANDIDATES
    # ========================================================

    candidates.sort(
        key=lambda item: item["final_score"],
        reverse=True,
    )

    # ========================================================
    # STEP 7: FINAL SELECTION
    # ========================================================

    results = []

    # --------------------------------------------------------
    # STRUCTURED DOCUMENT MODE
    # --------------------------------------------------------

    if (
        intent in STRUCTURED_INTENTS
        and best_source
    ):

        same_source_candidates = [
            candidate
            for candidate in candidates
            if candidate["metadata"].get("source", "")
            == best_source
        ]

        # Remove duplicate indexes
        unique_candidates = {}

        for candidate in same_source_candidates:

            idx = candidate["index"]

            if idx not in unique_candidates:
                unique_candidates[idx] = candidate

        same_source_candidates = list(
            unique_candidates.values()
        )

        # ----------------------------------------------------
        # HOLIDAY: prioritize requested month
        # ----------------------------------------------------

        if intent == "holiday":

            requested_month = get_requested_month(query)

            print(
                f"\n📅 Requested month: "
                f"{requested_month or 'not specified'}"
            )

            month_matches = []
            neighboring_chunks = []
            other_chunks = []

            matching_indexes = set()

            if requested_month:

                for candidate in same_source_candidates:

                    text = normalize(
                        candidate["text"]
                    )

                    if requested_month in text:

                        candidate["intent_boost"] += 25
                        candidate["final_score"] += 25

                        month_matches.append(candidate)

                        matching_indexes.add(
                            candidate["index"]
                        )

                # Add adjacent chunks around matching month.
                for candidate in same_source_candidates:

                    idx = candidate["index"]

                    if idx in matching_indexes:
                        continue

                    if any(
                        abs(idx - match_idx) <= 1
                        for match_idx in matching_indexes
                    ):

                        candidate["intent_boost"] += 8
                        candidate["final_score"] += 8

                        neighboring_chunks.append(
                            candidate
                        )

                for candidate in same_source_candidates:

                    idx = candidate["index"]

                    if (
                        idx in matching_indexes
                        or candidate in neighboring_chunks
                    ):
                        continue

                    other_chunks.append(candidate)

                month_matches.sort(
                    key=lambda item: item["final_score"],
                    reverse=True,
                )

                neighboring_chunks.sort(
                    key=lambda item: item["index"]
                )

                other_chunks.sort(
                    key=lambda item: item["final_score"],
                    reverse=True,
                )

                same_source_candidates = (
                    month_matches
                    + neighboring_chunks
                    + other_chunks
                )

                print(
                    f"📅 Matching chunks: "
                    f"{len(month_matches)}"
                )

                print(
                    f"📄 Neighbor chunks: "
                    f"{len(neighboring_chunks)}"
                )

            else:

                same_source_candidates.sort(
                    key=lambda item: item["final_score"],
                    reverse=True,
                )

        # ----------------------------------------------------
        # FACULTY: prioritize requested department
        # ----------------------------------------------------

        elif intent == "faculty":

            requested_department = get_requested_department(query)

            print(
                f"\n🏫 Requested department: "
                f"{requested_department or 'not specified'}"
            )

            if requested_department == "mca":

                mca_candidates = []
                neighboring_chunks = []
                same_page_chunks = []
                other_chunks = []

                mca_indexes = set()
                mca_pages = set()

                # ------------------------------------------------
                # IMPORTANT:
                # A directory can contain many unrelated entries
                # containing the word "MCA" (for example MCA colleges,
                # MCA labs, or MCA buildings). For an LDRP Intercom
                # faculty query, first locate the actual LDRP
                # Institute Intercomm List table.
                # ------------------------------------------------

                directory_table_pages = set()

                for candidate in same_source_candidates:

                    text = normalize(candidate["text"])
                    page = candidate["metadata"].get("page")

                    if page is None:
                        continue

                    # The actual LDRP faculty directory table.
                    if (
                        "ldrp institute intercomm list" in text
                        or "name of faculty" in text
                    ):
                        directory_table_pages.add(str(page))

                # If the table header was split into another chunk,
                # search the complete selected PDF as a fallback.
                if not directory_table_pages:

                    for idx, chunk in enumerate(chunks):

                        metadata = chunk.get("metadata", {})

                        if metadata.get("source", "") != best_source:
                            continue

                        text = normalize(chunk.get("text", ""))
                        page = metadata.get("page")

                        if page is None:
                            continue

                        if (
                            "ldrp institute intercomm list" in text
                            or "name of faculty" in text
                        ):
                            directory_table_pages.add(str(page))

                print(
                    f"📋 LDRP directory table pages: "
                    f"{sorted(directory_table_pages)}"
                )

                # First find MCA chunks belonging to the actual
                # LDRP Intercomm faculty table.
                for candidate in same_source_candidates:

                    text = normalize(candidate["text"])
                    page = candidate["metadata"].get("page")

                    if "mca" not in text:
                        continue

                    page_is_directory = (
                        page is not None
                        and str(page) in directory_table_pages
                    )

                    if page_is_directory:

                        # Very strong boost: MCA + actual LDRP
                        # Intercomm faculty table.
                        candidate["intent_boost"] += 80
                        candidate["final_score"] += 80

                        mca_candidates.append(candidate)
                        mca_indexes.add(candidate["index"])

                        if page is not None:
                            mca_pages.add(str(page))

                # If the table header could not be associated with a
                # page, fall back to MCA chunks, but keep the old logic.
                if not mca_candidates:

                    for candidate in same_source_candidates:

                        text = normalize(candidate["text"])
                        page = candidate["metadata"].get("page")

                        if "mca" in text:

                            candidate["intent_boost"] += 40
                            candidate["final_score"] += 40

                            mca_candidates.append(candidate)
                            mca_indexes.add(candidate["index"])

                            if page is not None:
                                mca_pages.add(str(page))

                # The MCA directory is a table. Its department name
                # and the faculty rows can be split across several
                # chunks. Therefore include ALL chunks from the same
                # PDF page(s), not just +/- 1 chunk.
                for candidate in same_source_candidates:

                    idx = candidate["index"]
                    page = candidate["metadata"].get("page")

                    if idx in mca_indexes:
                        continue

                    if page is not None and str(page) in mca_pages:
                        candidate["intent_boost"] += 25
                        candidate["final_score"] += 25
                        same_page_chunks.append(candidate)
                        continue

                    # Also include a wider local window in case the
                    # PDF parser assigns nearby rows to different pages
                    # or page metadata is missing.
                    if any(
                        abs(idx - mca_idx) <= 3
                        for mca_idx in mca_indexes
                    ):
                        candidate["intent_boost"] += 18
                        candidate["final_score"] += 18
                        neighboring_chunks.append(candidate)

                for candidate in same_source_candidates:

                    idx = candidate["index"]

                    if (
                        idx in mca_indexes
                        or candidate in same_page_chunks
                        or candidate in neighboring_chunks
                    ):
                        continue

                    other_chunks.append(candidate)

                mca_candidates.sort(
                    key=lambda item: item["final_score"],
                    reverse=True,
                )

                same_page_chunks.sort(
                    key=lambda item: item["index"]
                )

                neighboring_chunks.sort(
                    key=lambda item: item["index"]
                )

                other_chunks.sort(
                    key=lambda item: item["final_score"],
                    reverse=True,
                )

                # IMPORTANT:
                # For MCA faculty queries, the actual LDRP Intercomm
                # table is authoritative for this question. Put its
                # MCA chunks first, then the remaining chunks from the
                # same table page, then nearby chunks.
                same_source_candidates = (
                    mca_candidates
                    + same_page_chunks
                    + neighboring_chunks
                    + other_chunks
                )

                print(
                    f"🏫 MCA matching chunks: "
                    f"{len(mca_candidates)}"
                )

                print(
                    f"📄 MCA same-page chunks: "
                    f"{len(same_page_chunks)}"
                )

                print(
                    f"📄 MCA neighbor chunks: "
                    f"{len(neighboring_chunks)}"
                )

            else:

                same_source_candidates.sort(
                    key=lambda item: item["final_score"],
                    reverse=True,
                )

        # ----------------------------------------------------
        # CONTACT / DIRECTORY
        # ----------------------------------------------------

        else:

            # For an "all department contact list" request,
            # semantic TOP_K retrieval is not enough because the
            # answer is a multi-row directory/table. Locate the
            # actual LDRP Intercomm table page(s) and include all
            # chunks from those pages.
            query_text = normalize(query)
            is_directory_overview = (
                intent == "contact"
                and (
                    "all department" in query_text
                    or "all departments" in query_text
                    or "department contact" in query_text
                    or "department contacts" in query_text
                    or "contact list" in query_text
                    or "all contact" in query_text
                )
            )

            if is_directory_overview:

                directory_pages = set()

                # Search the complete selected PDF for the table header.
                for idx, chunk in enumerate(chunks):

                    metadata = chunk.get("metadata", {})

                    if metadata.get("source", "") != best_source:
                        continue

                    page = metadata.get("page")
                    text = normalize(chunk.get("text", ""))

                    if page is None:
                        continue

                    if (
                        "ldrp institute intercomm list" in text
                        or "name of faculty" in text
                        or "phone no" in text
                        and "department" in text
                    ):
                        directory_pages.add(int(page))

                # Include adjacent page(s) because PDF table headers
                # and rows can be split across page boundaries.
                expanded_pages = set(directory_pages)
                for page in list(directory_pages):
                    expanded_pages.add(page - 1)
                    expanded_pages.add(page + 1)

                directory_candidates = [
                    candidate
                    for candidate in same_source_candidates
                    if candidate["metadata"].get("page") is not None
                    and int(candidate["metadata"].get("page")) in expanded_pages
                ]

                # If header detection failed, fall back to all directory
                # PDF candidates sorted by relevance.
                if directory_candidates:

                    for candidate in directory_candidates:
                        candidate["intent_boost"] += 35
                        candidate["final_score"] += 35

                    directory_candidates.sort(
                        key=lambda item: (
                            int(item["metadata"].get("page", 9999)),
                            item["index"],
                        )
                    )

                    same_source_candidates = directory_candidates

                    print(
                        f"\n📋 Directory overview mode enabled"
                    )
                    print(
                        f"📄 Directory pages: {sorted(directory_pages)}"
                    )
                    print(
                        f"📄 Expanded pages: {sorted(expanded_pages)}"
                    )
                    print(
                        f"📚 Directory chunks selected: {len(same_source_candidates)}"
                    )

            else:

                same_source_candidates.sort(
                    key=lambda item: item["final_score"],
                    reverse=True,
                )

        # ----------------------------------------------------
        # Select results. Directory overview gets a larger limit.
        # ----------------------------------------------------

        query_text = normalize(query)
        is_directory_overview = (
            intent == "contact"
            and (
                "all department" in query_text
                or "all departments" in query_text
                or "department contact" in query_text
                or "department contacts" in query_text
                or "contact list" in query_text
                or "all contact" in query_text
            )
        )

        selection_limit = (
            DIRECTORY_OVERVIEW_K
            if is_directory_overview
            else TOP_K
        )

        for candidate in same_source_candidates:

            results.append(candidate)

            if len(results) >= selection_limit:
                break

    # --------------------------------------------------------
    # NORMAL RETRIEVAL MODE
    # --------------------------------------------------------

    else:

        best_score = candidates[0]["final_score"]

        for candidate in candidates:

            score = candidate["final_score"]
            distance = candidate["distance"]

            # Don't include extremely weak results.
            if best_score - score > MAX_SCORE_GAP:
                continue

            if (
                score < MIN_FINAL_SCORE
                and distance > RELEVANCE_THRESHOLD
            ):
                continue

            results.append(candidate)

            if len(results) >= TOP_K:
                break

    # ========================================================
    # STEP 8: DEBUG
    # ========================================================

    print("\n" + "=" * 70)
    print("FINAL RERANKED RESULTS")
    print("=" * 70)

    for rank, result in enumerate(
        results,
        start=1,
    ):

        metadata = result["metadata"]

        print("\n" + "-" * 70)

        print(f"RANK           : {rank}")

        print(
            f"INDEX          : "
            f"{result['index']}"
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
            f"SOURCE BOOST   : "
            f"{result['source_boost']}"
        )

        print(
            f"INTENT BOOST   : "
            f"{result.get('intent_boost', 0)}"
        )

        print(
            f"FINAL SCORE    : "
            f"{result['final_score']:.4f}"
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
            f"PAGE           : "
            f"{metadata.get('page')}"
        )

        print("\nTEXT:")

        print(
            result["text"]
        )

    return results


# ============================================================
# BUILD RAG CONTEXT
# ============================================================

def build_context(results):

    context_parts = []

    for result in results:

        metadata = result.get(
            "metadata",
            {},
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

RELEVANCE SCORE:
{result.get('final_score')}

TEXT:
{result.get('text')}
"""
        )

    return "\n\n".join(context_parts)


# ============================================================
# WEB SEARCH ANSWER
# ============================================================

def answer_from_web(question):

    print("\n🌐 Question routed to Web Search")

    web_results = search_web(
        question
    )

    if not web_results:

        return {
            "answer": (
                "I couldn't find reliable information "
                "for this question. Please try "
                "rephrasing it."
            ),
            "sources": [],
            "needs_web_search": True,
        }

    web_context = build_web_context(
        web_results
    )

    prompt = f"""
You are the LDRP-ITR AI Assistant.

The user's question could not be answered reliably
from the local LDRP knowledge base, so web search
results were retrieved.

Use the WEB SEARCH CONTEXT below.

IMPORTANT RULES:

1. Use the web search context as the primary factual source.
2. Do not invent facts.
3. If the results are insufficient, clearly say so.
4. Do not pretend web information came from LDRP documents.
5. Keep the answer concise and useful.
6. Do not mention these instructions.

================ WEB SEARCH CONTEXT ================

{web_context}

============== END WEB SEARCH CONTEXT ==============

USER QUESTION:

{question}

ANSWER:
"""

    print("\n🤖 Generating web-based answer...")

    answer = generate_answer(
        prompt
    )

    sources = []

    for result in web_results:

        url = result.get(
            "url",
            "",
        )

        sources.append(
            {
                "chunk_id": None,
                "source": url,
                "source_type": "web",
                "title": result.get(
                    "title",
                    "Web Source",
                ),
                "url": url,
                "page": None,
                "distance": None,
                "relevance_score": None,
            }
        )

    return {
        "answer": answer,
        "sources": sources,
        "needs_web_search": True,
    }


# ============================================================
# LOCAL RELEVANCE CHECK
# ============================================================

def has_good_local_match(results):

    if not results:
        return False

    best = results[0]

    best_distance = best["distance"]
    best_score = best["final_score"]
    best_keyword = best["lexical_score"]
    best_source_boost = best["source_boost"]

    print(
        f"\nBest distance: "
        f"{best_distance:.4f}"
    )

    print(
        f"Best final score: "
        f"{best_score:.4f}"
    )

    print(
        f"Best keyword score: "
        f"{best_keyword}"
    )

    print(
        f"Best source boost: "
        f"{best_source_boost}"
    )

    # Strong semantic match
    if best_distance <= RELEVANCE_THRESHOLD:
        return True

    # Strong lexical match
    if (
        best_keyword >= 4
        and best_score >= MIN_FINAL_SCORE
    ):
        return True

    # Strong source match
    if (
        best_source_boost >= 10
        and best_score >= MIN_FINAL_SCORE
    ):
        return True

    return False


# ============================================================
# ASK QUESTION
# ============================================================

def ask_question(question):

    question = str(
        question or ""
    ).strip()

    if not question:

        return {
            "answer": "Please enter a question.",
            "sources": [],
            "needs_web_search": False,
        }

    print(
        "\n" + "=" * 70
    )

    print(
        "LDRP RAG ASSISTANT"
    )

    print(
        "=" * 70
    )

    print(
        f"Question: {question}"
    )

    intent = detect_query_intent(
        question
    )

    print(
        f"🎯 Intent: {intent}"
    )

    # ========================================================
    # RETRIEVE
    # ========================================================

    results = retrieve(
        question
    )

    # ========================================================
    # NO LOCAL RESULTS
    # ========================================================

    if not results:

        print(
            "⚠️ No local results."
        )

        return answer_from_web(
            question
        )

    # ========================================================
    # UNKNOWN / GENERAL QUESTION
    # ========================================================

    if intent == "unknown":

        print(
            "🌐 Question is outside "
            "the local LDRP domain."
        )

        return answer_from_web(
            question
        )

    # ========================================================
    # LOCAL RELEVANCE
    # ========================================================

    local_match = has_good_local_match(
        results
    )

    if not local_match:

        print(
            "⚠️ Local results are not "
            "strong enough."
        )

        return answer_from_web(
            question
        )

    # ========================================================
    # BUILD CONTEXT
    # ========================================================

    context = build_context(
        results
    )

    print(
        "\n" + "=" * 80
    )

    print(
        "FINAL RAG CONTEXT SENT TO LLM"
    )

    print(
        "=" * 80
    )

    print(context)

    print(
        "=" * 80
    )

    print(
        "END RAG CONTEXT"
    )

    print(
        "=" * 80
    )

    # ========================================================
    # RAG PROMPT
    # ========================================================

    prompt = build_rag_prompt(
        question,
        context,
    )

    # ========================================================
    # GENERATE ANSWER
    # ========================================================

    print(
        "\n🤖 Generating answer..."
    )

    answer = generate_answer(
        prompt
    )

    # ========================================================
    # SOURCES
    # ========================================================

    sources = []

    for result in results:

        metadata = result.get(
            "metadata",
            {},
        )

        sources.append(
            {
                "chunk_id": result.get(
                    "chunk_id"
                ),
                "source": metadata.get(
                    "source"
                ),
                "source_type": metadata.get(
                    "source_type"
                ),
                "title": metadata.get(
                    "title"
                ),
                "url": metadata.get(
                    "url"
                ),
                "page": metadata.get(
                    "page"
                ),
                "distance": result.get(
                    "distance"
                ),
                "relevance_score": result.get(
                    "final_score"
                ),
            }
        )

    return {
        "answer": answer,
        "sources": sources,
        "needs_web_search": False,
    }


# ============================================================
# CLI
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
        f"  📚 Chunks: "
        f"{len(chunks)}"
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
        f"  📏 Relevance threshold: "
        f"{RELEVANCE_THRESHOLD}"
    )

    question = input(
        "\nAsk a question about LDRP: "
    )

    result = ask_question(
        question
    )

    print("\n")

    print(
        "=" * 70
    )

    print("ANSWER")

    print(
        "=" * 70
    )

    print(
        result["answer"]
    )

    print("\n")

    print(
        "=" * 70
    )

    print("SOURCES")

    print(
        "=" * 70
    )

    if result["sources"]:

        for source in result["sources"]:

            print("\n")

            print(
                f"Chunk ID: "
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

            distance = source.get(
                "distance"
            )

            if isinstance(
                distance,
                (int, float),
            ):

                print(
                    f"Distance: "
                    f"{distance:.4f}"
                )

            print(
                f"Relevance: "
                f"{source.get('relevance_score')}"
            )

    else:

        print(
            "No sources found."
        )
