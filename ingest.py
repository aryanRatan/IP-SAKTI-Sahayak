import json
import os

import chromadb
from sentence_transformers import SentenceTransformer


# ==========================================
# 1. SETTINGS
# ==========================================

DATA_FILE = "data/IP-SAKTI_Master_RAG_KnowledgeBase_v1.jsonl"

CHROMA_FOLDER = "chroma_db"

COLLECTION_NAME = "ip_sakti_knowledge_v1"

MODEL_NAME = "all-MiniLM-L6-v2"


# ==========================================
# 2. CHECK FILE
# ==========================================

if not os.path.exists(DATA_FILE):

    print("ERROR: JSONL file not found!")
    print(f"Expected: {DATA_FILE}")
    exit()


# ==========================================
# 3. LOAD EMBEDDING MODEL
# ==========================================

print("Loading embedding model...")

model = SentenceTransformer(MODEL_NAME)

print("Embedding model loaded!")


# ==========================================
# 4. READ JSONL
# ==========================================

print("\nReading knowledge base...")

records = []

with open(
    DATA_FILE,
    "r",
    encoding="utf-8"
) as file:

    for line_number, line in enumerate(
        file,
        start=1
    ):

        line = line.strip()

        if not line:
            continue

        try:

            record = json.loads(line)

            records.append(record)

        except json.JSONDecodeError:

            print(
                f"WARNING: Invalid JSON "
                f"at line {line_number}"
            )


print(
    f"Total records found: {len(records)}"
)


# ==========================================
# 5. SELECT RECORDS
# ==========================================

records_to_embed = [

    record

    for record in records

    if record.get("embed") is True
]


print(
    f"Records selected for embedding: "
    f"{len(records_to_embed)}"
)


# ==========================================
# 6. PREPARE EMBEDDING TEXT
# ==========================================

embedding_texts = []


for record in records_to_embed:

    title = record.get(
        "title",
        ""
    )

    retrieval_text = record.get(
        "retrieval_text",
        ""
    )

    tags = record.get(
        "tags",
        []
    )

    if isinstance(tags, list):

        tags_text = " ".join(
            str(tag)
            for tag in tags
        )

    else:

        tags_text = str(tags)


    text = f"""
Title:
{title}

Knowledge:
{retrieval_text}

Keywords:
{tags_text}
""".strip()


    embedding_texts.append(text)


# ==========================================
# 7. CREATE EMBEDDINGS
# ==========================================

print("\nCreating embeddings...")

embeddings = model.encode(
    embedding_texts,
    show_progress_bar=True
).tolist()

print("Embeddings created!")


# ==========================================
# 8. CONNECT TO CHROMADB
# ==========================================

print("\nConnecting to ChromaDB...")

client = chromadb.PersistentClient(
    path=CHROMA_FOLDER
)


# ==========================================
# 9. CREATE COLLECTION
# ==========================================

collection = client.get_or_create_collection(
    name=COLLECTION_NAME
)

print(
    f"Collection ready: {COLLECTION_NAME}"
)


# ==========================================
# 10. PREPARE CHROMADB DATA
# ==========================================

ids = []

documents = []

metadatas = []


for record in records_to_embed:

    # --------------------------------------
    # Basic fields
    # --------------------------------------

    record_id = record.get(
        "record_id",
        "unknown"
    )

    domain = record.get(
        "domain",
        "unknown"
    )

    record_type = record.get(
        "record_type",
        "unknown"
    )

    title = record.get(
        "title",
        ""
    )

    retrieval_role = record.get(
        "retrieval_role",
        ""
    )


    # --------------------------------------
    # Main knowledge
    # --------------------------------------

    retrieval_text = record.get(
        "retrieval_text",
        ""
    )


    # --------------------------------------
    # Tags
    # --------------------------------------

    tags = record.get(
        "tags",
        []
    )

    if isinstance(tags, list):

        tags_text = ", ".join(
            str(tag)
            for tag in tags
        )

    else:

        tags_text = str(tags)


    # --------------------------------------
    # Nested metadata
    # --------------------------------------

    record_metadata = record.get(
        "metadata",
        {}
    )


    if not isinstance(
        record_metadata,
        dict
    ):

        record_metadata = {}


    confidence = record_metadata.get(
        "confidence",
        ""
    )

    source_note = record_metadata.get(
        "source_note",
        ""
    )

    provision_location = record_metadata.get(
        "provision_location",
        ""
    )

    verification_status = record_metadata.get(
        "verification_status",
        ""
    )


    # --------------------------------------
    # Add ID
    # --------------------------------------

    ids.append(record_id)


    # --------------------------------------
    # Add document
    # --------------------------------------

    documents.append(
        retrieval_text
    )


    # --------------------------------------
    # Add metadata
    # --------------------------------------

    metadatas.append({

        "record_id": record_id,

        "domain": domain,

        "record_type": record_type,

        "retrieval_role": retrieval_role,

        "title": title,

        "tags": tags_text,

        "confidence": str(
            confidence
        ),

        "source_note": str(
            source_note
        ),

        "provision_location": str(
            provision_location
        ),

        "verification_status": str(
            verification_status
        ),

        "jurisdiction": str(
            record.get(
                "jurisdiction",
                ""
            )
        ),

        "language": str(
            record.get(
                "language",
                ""
            )
        ),

        "schema_version": str(
            record.get(
                "schema_version",
                ""
            )
        ),

        "dataset": str(
            record.get(
                "dataset",
                ""
            )
        )
    })


# ==========================================
# 11. SAFETY CHECK
# ==========================================

print("\nChecking data lengths...")

print(f"IDs        : {len(ids)}")

print(f"Documents  : {len(documents)}")

print(f"Embeddings : {len(embeddings)}")

print(f"Metadatas  : {len(metadatas)}")


if not (
    len(ids)
    == len(documents)
    == len(embeddings)
    == len(metadatas)
):

    print(
        "\nERROR: Data lengths do not match!"
    )

    exit()


print("All lengths match!")


# ==========================================
# 12. STORE IN CHROMADB
# ==========================================

print("\nStoring records in ChromaDB...")


collection.upsert(

    ids=ids,

    documents=documents,

    embeddings=embeddings,

    metadatas=metadatas
)


# ==========================================
# 13. VERIFY
# ==========================================

total = collection.count()


print("\n==========================================")

print(
    "       IP-SAKTI RAG INGESTION DONE"
)

print("==========================================")

print(
    f"JSONL records found : {len(records)}"
)

print(
    f"Records embedded    : "
    f"{len(records_to_embed)}"
)

print(
    f"ChromaDB records    : {total}"
)

print("==========================================")