import re
import chromadb
from sentence_transformers import SentenceTransformer


# ==========================================
# 1. SETTINGS
# ==========================================

CHROMA_FOLDER = "chroma_db"
COLLECTION_NAME = "ip_sakti_knowledge_v1"
MODEL_NAME = "all-MiniLM-L6-v2"

# Retrieve more candidates first, then rerank them
CANDIDATES_TO_RETRIEVE = 20
FINAL_RESULTS = 5


# ==========================================
# 2. LOAD EMBEDDING MODEL
# ==========================================

print("Loading embedding model...")

model = SentenceTransformer(MODEL_NAME)

print("Embedding model loaded!")


# ==========================================
# 3. CONNECT TO CHROMADB
# ==========================================

print("Connecting to ChromaDB...")

client = chromadb.PersistentClient(
    path=CHROMA_FOLDER
)

collection = client.get_collection(
    name=COLLECTION_NAME
)

print(
    f"Knowledge base loaded: "
    f"{collection.count()} records"
)

# ==========================================
# PRIORITY AYURVEDA INGREDIENT RECORDS
# ==========================================

priority_records = [
    {
        "id": "AY-ING-GYMNEMA",
        "title": "Gudmar / Gymnema sylvestre",
        "tags": "gudmar gymnema sylvestre meshashringi ayurveda herb ingredient extract",
        "document": (
            "AYURVEDA INGREDIENT: Gudmar, "
            "Gymnema sylvestre. "
            "Official Ayurveda pharmacopoeia material should be "
            "verified for the exact monograph, plant part and "
            "preparation. For an extract formulation, the exact "
            "plant part, extraction method and specification "
            "must be separately established."
        ),
        "source": "PCIM&H / Ayurvedic Pharmacopoeia of India"
    },
    {
        "id": "AY-ING-PTEROCARPUS",
        "title": "Vijayasara / Pterocarpus marsupium",
        "tags": "vijayasara asana pterocarpus marsupium ayurveda herb ingredient extract",
        "document": (
            "AYURVEDA INGREDIENT: Vijayasara / Asana, "
            "Pterocarpus marsupium. "
            "Official Ayurveda pharmacopoeia material should be "
            "verified for the exact monograph, plant part and "
            "preparation. For an extract formulation, the exact "
            "plant part, extraction method and specification "
            "must be separately established."
        ),
        "source": "PCIM&H / Ayurvedic Pharmacopoeia of India"
    }
]

# Add records only if they do not already exist
existing = collection.get(
    ids=[record["id"] for record in priority_records]
)

existing_ids = set(existing.get("ids", []))

new_records = [
    record
    for record in priority_records
    if record["id"] not in existing_ids
]

if new_records:
    documents = [record["document"] for record in new_records]

    metadatas = [
        {
            "record_id": record["id"],
            "domain": "ayurveda",
            "record_type": "ingredient",
            "title": record["title"],
            "tags": record["tags"],
            "source_note": record["source"],
            "confidence": "source-indexed; verify monograph/version"
        }
        for record in new_records
    ]

    embeddings = model.encode(documents).tolist()

    collection.add(
        ids=[record["id"] for record in new_records],
        documents=documents,
        metadatas=metadatas,
        embeddings=embeddings
    )

    print(
        f"Added {len(new_records)} priority Ayurveda ingredient records."
    )



# ==========================================
# 4. QUERY TOPIC DETECTION
# ==========================================

def detect_topics(query):

    query_lower = query.lower()

    topics = set()

    # Patent / IP
    patent_words = [
        "patent",
        "patentability",
        "filing",
        "inventive step",
        "novelty",
        "prior art",
        "section 3",
        "3(p)",
        "3(e)",
        "ip",
        "intellectual property"
    ]

    # ABS / biodiversity
    abs_words = [
        "abs",
        "access and benefit",
        "benefit sharing",
        "biodiversity",
        "biological resource",
        "wild collected",
        "nba",
        "state biodiversity"
    ]

    # Ayurveda
    ayurveda_words = [
        "ayurveda",
        "ayurvedic",
        "formulation",
        "herb",
        "herbal",
        "ingredient",
        "churna",
        "kwath",
        "extract",
        "ashwagandha",
        "guduchi",
        "amalaki",
        "chyawanprash"
    ]

    # Licensing / regulation
    licensing_words = [
        "license",
        "licensing",
        "licence",
        "drug",
        "drugs and cosmetics",
        "rule 158",
        "regulatory",
        "regulation",
        "classical",
        "p&p",
        "phytopharmaceutical"
    ]

    # International
    international_words = [
        "international",
        "wipo",
        "trips",
        "nagoya",
        "pct",
        "madrid",
        "hague",
        "foreign",
        "export"
    ]

    if any(word in query_lower for word in patent_words):
        topics.add("patent")

    if any(word in query_lower for word in abs_words):
        topics.add("abs")

    if any(word in query_lower for word in ayurveda_words):
        topics.add("ayurveda")

    if any(word in query_lower for word in licensing_words):
        topics.add("licensing")

    if any(word in query_lower for word in international_words):
        topics.add("international")

    return topics


# ==========================================
# 5. TOKENIZE TEXT
# ==========================================

def tokenize(text):

    return set(
        re.findall(
            r"[a-zA-Z0-9]+",
            text.lower()
        )
    )


# ==========================================
# 6. KEYWORD SCORE
# ==========================================

def keyword_score(query, metadata, document):

    query_tokens = tokenize(query)

    title = metadata.get("title", "")
    tags = metadata.get("tags", "")

    searchable_text = (
        title
        + " "
        + tags
        + " "
        + document
    )

    document_tokens = tokenize(searchable_text)

    if not query_tokens:
        return 0

    overlap = query_tokens.intersection(
        document_tokens
    )

    return len(overlap) / len(query_tokens)


# ==========================================
# 7. TOPIC SCORE
# ==========================================

def topic_score(topics, metadata):

    if not topics:
        return 0

    domain = metadata.get(
        "domain",
        ""
    ).lower()

    record_type = metadata.get(
        "record_type",
        ""
    ).lower()

    title = metadata.get(
        "title",
        ""
    ).lower()

    score = 0

    for topic in topics:

        if topic == "patent":

            if domain == "law_regulation":
                score += 3

            if "patent" in title:
                score += 3

            if "legal" in record_type:
                score += 2

            if "decision" in record_type:
                score += 2


        elif topic == "abs":

            if "law" in domain:
                score += 3

            if "biodiversity" in title:
                score += 3

            if "abs" in title:
                score += 3


        elif topic == "ayurveda":

            if domain == "ayurveda":
                score += 3

            if record_type in [
                "ingredient",
                "classical_formulation",
                "dosage_form"
            ]:
                score += 2


        elif topic == "licensing":

            if "law" in domain:
                score += 3

            if (
                "licensing" in title
                or "drug" in title
                or "classification" in title
            ):
                score += 3


        elif topic == "international":

            if (
                "wipo" in title
                or "international" in title
                or "treaty" in title
            ):
                score += 3

    return score


# ==========================================
# 8. RETRIEVE CANDIDATES
# ==========================================

def retrieve_candidates(query):

    query_embedding = model.encode(
        [query]
    ).tolist()

    results = collection.query(

        query_embeddings=query_embedding,

        n_results=CANDIDATES_TO_RETRIEVE,

        include=[
            "documents",
            "metadatas",
            "distances"
        ]
    )

    return results


# ==========================================
# 9. RERANK RESULTS
# ==========================================

def rerank_results(query, results):

    topics = detect_topics(query)

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    ranked = []

    for i in range(len(documents)):

        metadata = metadatas[i]
        document = documents[i]
        distance = distances[i]

        # Convert distance into a rough similarity score.
        # Lower distance = better.
        semantic_score = 1 / (1 + distance)

        keyword = keyword_score(
            query,
            metadata,
            document
        )

        topic = topic_score(
            topics,
            metadata
        )

        # Combined score
        final_score = (
            semantic_score * 0.55
            + keyword * 0.25
            + topic * 0.20
        )

        ranked.append({

            "document": document,

            "metadata": metadata,

            "distance": distance,

            "semantic_score": semantic_score,

            "keyword_score": keyword,

            "topic_score": topic,

            "final_score": final_score
        })

    ranked.sort(
        key=lambda x: x["final_score"],
        reverse=True
    )

    return ranked[:FINAL_RESULTS], topics


# ==========================================
# 10. DISPLAY RESULTS
# ==========================================

def display_results(query):

    results = retrieve_candidates(query)

    ranked_results, topics = rerank_results(
        query,
        results
    )

    print("\n===================================")
    print("QUERY ANALYSIS")
    print("===================================")

    if topics:

        print(
            "Detected topics: "
            + ", ".join(sorted(topics))
        )

    else:

        print("Detected topics: general")


    print("\n===================================")
    print("RERANKED RETRIEVED KNOWLEDGE")
    print("===================================\n")


    for i, result in enumerate(
        ranked_results,
        start=1
    ):

        metadata = result["metadata"]

        print(
            f"RESULT {i}"
        )

        print(
            "-----------------------------------"
        )

        print(
            f"Record ID : "
            f"{metadata.get('record_id', '')}"
        )

        print(
            f"Domain    : "
            f"{metadata.get('domain', '')}"
        )

        print(
            f"Type      : "
            f"{metadata.get('record_type', '')}"
        )

        print(
            f"Title     : "
            f"{metadata.get('title', '')}"
        )

        print(
            f"Source    : "
            f"{metadata.get('source_note', '')}"
        )

        print(
            f"Confidence: "
            f"{metadata.get('confidence', '')}"
        )

        print(
            f"Semantic  : "
            f"{result['semantic_score']:.4f}"
        )

        print(
            f"Keyword   : "
            f"{result['keyword_score']:.4f}"
        )

        print(
            f"Topic     : "
            f"{result['topic_score']:.4f}"
        )

        print(
            f"Final     : "
            f"{result['final_score']:.4f}"
        )

        print("\nKnowledge:")

        print(
            result["document"]
        )

        print(
            "\n===================================\n"
        )

# ==========================================
# 11. REUSABLE RAG FUNCTION
# ==========================================

def retrieve_knowledge(query):
    """
    Reusable RAG retrieval function.

    Returns:
        ranked_results: list of retrieved knowledge records
        topics: detected query topics
    """

    if not query or not query.strip():
        return [], set()

    # Step 1: Retrieve candidate records
    candidates = retrieve_candidates(query)

    # Step 2: Rerank candidates
    ranked_results, topics = rerank_results(
        query,
        candidates
    )

    # Step 3: Return both
    return ranked_results, topics

# ==========================================
# 12. INTERACTIVE LOOP
# ==========================================

if __name__ == "__main__":

    while True:

        print("\n====================================")

        query = input(
            "Ask IP-SAKTI a question "
            "(type 'exit' to stop): "
        )

        if query.lower().strip() == "exit":

            print("Exiting RAG...")
            break

        if not query.strip():

            print("Please enter a question.")
            continue

        display_results(query)