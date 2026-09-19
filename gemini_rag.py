import os
import re

import chromadb
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
from google import genai


# ==========================================
# 1. LOAD ENVIRONMENT VARIABLES
# ==========================================

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    print("ERROR: GEMINI_API_KEY not found!")
    print("Please check your .env file.")
    exit()


# ==========================================
# 2. GEMINI CLIENT
# ==========================================

client = genai.Client(
    api_key=API_KEY
)

GEMINI_MODEL = "gemini-2.5-flash"


# ==========================================
# 3. CHROMADB SETTINGS
# ==========================================

CHROMA_FOLDER = "chroma_db"

COLLECTION_NAME = "ip_sakti_knowledge_v1"

EMBEDDING_MODEL = "all-MiniLM-L6-v2"


# ==========================================
# 4. LOAD EMBEDDING MODEL
# ==========================================

print("Loading embedding model...")

embedding_model = SentenceTransformer(
    EMBEDDING_MODEL
)

print("Embedding model loaded!")


# ==========================================
# 5. CONNECT TO CHROMADB
# ==========================================

print("Connecting to ChromaDB...")

chroma_client = chromadb.PersistentClient(
    path=CHROMA_FOLDER
)

collection = chroma_client.get_collection(
    name=COLLECTION_NAME
)

print(
    f"Knowledge base loaded: "
    f"{collection.count()} records"
)


# ==========================================
# 6. TOPIC DETECTION
# ==========================================

def detect_topics(query):

    query_lower = query.lower()

    topics = set()

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
        "intellectual property"
    ]

    abs_words = [
        "abs",
        "access and benefit sharing",
        "benefit sharing",
        "biodiversity",
        "biological resource",
        "wild collected",
        "nba"
    ]

    ayurveda_words = [
        "ayurveda",
        "ayurvedic",
        "formulation",
        "ingredient",
        "herb",
        "churna",
        "extract",
        "ashwagandha",
        "guduchi",
        "chyawanprash"
    ]

    licensing_words = [
        "license",
        "licensing",
        "licence",
        "drug",
        "drugs and cosmetics",
        "regulatory",
        "regulation",
        "classical",
        "p&p",
        "phytopharmaceutical"
    ]

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

    if any(
        word in query_lower
        for word in patent_words
    ):
        topics.add("patent")

    if any(
        word in query_lower
        for word in abs_words
    ):
        topics.add("abs")

    if any(
        word in query_lower
        for word in ayurveda_words
    ):
        topics.add("ayurveda")

    if any(
        word in query_lower
        for word in licensing_words
    ):
        topics.add("licensing")

    if any(
        word in query_lower
        for word in international_words
    ):
        topics.add("international")

    return topics


# ==========================================
# 7. TOKENIZER
# ==========================================

def tokenize(text):

    return set(
        re.findall(
            r"[a-zA-Z0-9]+",
            text.lower()
        )
    )


# ==========================================
# 8. KEYWORD SCORE
# ==========================================

def keyword_score(
    query,
    metadata,
    document
):

    query_tokens = tokenize(query)

    title = metadata.get(
        "title",
        ""
    )

    tags = metadata.get(
        "tags",
        ""
    )

    searchable_text = (
        title
        + " "
        + tags
        + " "
        + document
    )

    document_tokens = tokenize(
        searchable_text
    )

    if not query_tokens:
        return 0

    overlap = query_tokens.intersection(
        document_tokens
    )

    return (
        len(overlap)
        / len(query_tokens)
    )


# ==========================================
# 9. TOPIC SCORE
# ==========================================

def topic_score(
    topics,
    metadata
):

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

            if "decision" in record_type:
                score += 2

            if "legal" in record_type:
                score += 2


        elif topic == "abs":

            if domain == "law_regulation":
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

            if domain == "law_regulation":
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
# 10. RETRIEVE KNOWLEDGE
# ==========================================

def retrieve_knowledge(
    query,
    number_of_results=5
):

    # --------------------------------------
    # Convert question into embedding
    # --------------------------------------

    query_embedding = embedding_model.encode(
        [query]
    ).tolist()


    # --------------------------------------
    # Retrieve candidates
    # --------------------------------------

    results = collection.query(

        query_embeddings=query_embedding,

        n_results=20,

        include=[
            "documents",
            "metadatas",
            "distances"
        ]
    )


    documents = results["documents"][0]

    metadatas = results["metadatas"][0]

    distances = results["distances"][0]


    topics = detect_topics(query)


    ranked = []


    # --------------------------------------
    # Rerank
    # --------------------------------------

    for i in range(len(documents)):

        document = documents[i]

        metadata = metadatas[i]

        distance = distances[i]


        semantic_score = (
            1 / (1 + distance)
        )


        kw_score = keyword_score(
            query,
            metadata,
            document
        )


        tp_score = topic_score(
            topics,
            metadata
        )


        final_score = (
            semantic_score * 0.55
            + kw_score * 0.25
            + tp_score * 0.20
        )


        ranked.append({

            "document": document,

            "metadata": metadata,

            "distance": distance,

            "score": final_score
        })


    ranked.sort(
        key=lambda x: x["score"],
        reverse=True
    )


    return ranked[:number_of_results]


# ==========================================
# 11. BUILD EVIDENCE
# ==========================================

def build_evidence(results):

    evidence = []


    for i, result in enumerate(
        results,
        start=1
    ):

        metadata = result["metadata"]

        document = result["document"]


        evidence.append(
            f"""
EVIDENCE {i}

Record ID:
{metadata.get("record_id", "Unknown")}

Domain:
{metadata.get("domain", "Unknown")}

Record Type:
{metadata.get("record_type", "Unknown")}

Title:
{metadata.get("title", "Unknown")}

Source:
{metadata.get("source_note", "Source not specified")}

Provision / Location:
{metadata.get("provision_location", "Not specified")}

Confidence:
{metadata.get("confidence", "Not specified")}

Knowledge:
{document}
"""
        )


    return "\n".join(evidence)


# ==========================================
# 12. GENERATE GEMINI ANSWER
# ==========================================

def generate_answer(
    question,
    evidence
):

    prompt = f"""
You are IP-SAKTI Sahayak, an AI assistant
for Intellectual Property, Ayurveda,
traditional knowledge, biodiversity/ABS,
and regulatory guidance.

Your job is to answer the user's question
using ONLY the evidence supplied below.

USER QUESTION:
{question}


RETRIEVED EVIDENCE:
{evidence}


IMPORTANT RULES:

1. Use the retrieved evidence as the
   primary knowledge source.

2. Do NOT invent facts, laws, sections,
   rules, authorities, sources, or dates.

3. For legal or regulatory information,
   clearly distinguish:
   - documented evidence
   - inference
   - uncertainty

4. Do NOT give a definitive legal
   determination such as:
   "This is patentable"
   or
   "This cannot be patented."

5. Instead describe relevant checks,
   risks, requirements, or considerations.

6. Cite the relevant Record ID in the answer.

7. Mention the source when source
   information is available.

8. If the evidence is insufficient,
   explicitly say:
   "The available knowledge base does not
   contain sufficient evidence to answer
   this confidently."

9. If evidence conflicts or is uncertain,
   mention that and recommend human
   professional review.

10. Do not claim access to restricted
    systems such as TKDL unless the
    retrieved evidence explicitly supports
    such access.

11. Keep the answer structured and easy
    to understand.

ANSWER FORMAT:

### Answer

Give a concise answer.

### Relevant Evidence

List the important retrieved records.

### What You Should Check

Give practical next checks based only
on the evidence.

### Confidence

State whether the answer has:
High / Medium / Low confidence.

Explain why.

### Sources

List Record IDs and available source
information.


Now answer the user's question.
"""


    response = client.models.generate_content(

        model=GEMINI_MODEL,

        contents=prompt

    )


    return response.text


# ==========================================
# 13. MAIN PROGRAM
# ==========================================

print("\n======================================")

print("       IP-SAKTI GEMINI RAG")

print("======================================")


while True:

    question = input(
        "\nAsk IP-SAKTI "
        "(type 'exit' to stop): "
    )


    if question.lower().strip() == "exit":

        print("Goodbye!")

        break


    if not question.strip():

        print("Please enter a question.")

        continue


    print("\nRetrieving knowledge...")


    results = retrieve_knowledge(
        question
    )


    evidence = build_evidence(
        results
    )


    print("\nGenerating answer...")


    try:

        answer = generate_answer(
            question,
            evidence
        )


        print(
            "\n======================================"
        )

        print("              IP-SAKTI")

        print(
            "======================================\n"
        )

        print(answer)


        print(
            "\n======================================"
        )


    except Exception as error:

        print("\nERROR while generating answer:")

        print(error)