import json

from intake import collect_profile, classify
from rag import retrieve_knowledge


# ============================================================
# IP-SAKTI
# MAIN PIPELINE
# ============================================================


def build_pipeline_input(profile=None):

    print("\n")
    print("================================================")
    print("              IP-SAKTI PIPELINE")
    print("================================================")

    # --------------------------------------------------------
    # STEP 1: COLLECT FORMULATION INFORMATION
    # --------------------------------------------------------

    # If profile is supplied by the backend/frontend,
    # use it directly.
    #
    # Otherwise, collect it from terminal.
    if profile is None:
        profile = collect_profile()

    # --------------------------------------------------------
    # STEP 2: CLASSIFY FORMULATION
    # --------------------------------------------------------

    print("\nClassifying formulation...")

    classification = classify(profile)

    # --------------------------------------------------------
    # STEP 3: COMBINE EVERYTHING
    # --------------------------------------------------------

    pipeline_data = {

        "formulation_profile": profile,

        "classification": classification
    }

    return pipeline_data


# ============================================================
# CREATE RAG QUERY
# ============================================================

def create_rag_query(pipeline_data):

    profile = pipeline_data[
        "formulation_profile"
    ]

    classification = pipeline_data[
        "classification"
    ]

    formulation_name = profile[
        "formulation_name"
    ]

    applicant_type = profile[
        "applicant_type"
    ]

    delivery_form = profile[
        "target_delivery_form"
    ]

    # --------------------------------------------------------
    # INGREDIENT INFORMATION
    # --------------------------------------------------------

    ingredient_names = []

    for ingredient in profile[
        "ingredients"
    ]:

        botanical = ingredient[
            "botanical_name"
        ]

        common_name = ingredient[
            "sanskrit_name"
        ]

        ingredient_names.append(
            f"{common_name} ({botanical})"
        )

    ingredients_text = ", ".join(
        ingredient_names
    )

    # --------------------------------------------------------
    # CLASSIFICATION INFORMATION
    # --------------------------------------------------------

    regulatory = classification[
        "regulatory_classification"
    ]

    abs_result = classification[
        "abs_assessment"
    ]

    patent = classification[
        "patent_screening"
    ]

    # --------------------------------------------------------
    # BUILD RAG QUERY
    # --------------------------------------------------------

    query = f"""
Analyze the following Ayurveda formulation for IP,
traditional knowledge, biodiversity/ABS and regulatory
considerations.

Formulation:
{formulation_name}

Applicant:
{applicant_type}

Ingredients:
{ingredients_text}

Delivery form:
{delivery_form}

Regulatory classification from intake:
{regulatory["classification"]}

ABS assessment:
{abs_result["route"]}

Patent screening flag:
{patent["screening_flag"]}

Retrieve authoritative and relevant evidence about:

1. Ayurveda formulation identity
2. Classical formulation or traditional knowledge overlap
3. Patent and prior-art considerations
4. Section 3(e) and Section 3(p) where relevant
5. Biological Diversity / ABS requirements
6. Regulatory classification and licensing
7. Relevant official provisions and sources

Do not invent laws, sections, sources or citations.
If evidence is insufficient, explicitly state that
verification or human review is required.
"""

    return query.strip()


# ============================================================
# SAVE PIPELINE DATA
# ============================================================

def save_pipeline_data(data):

    filename = "pipeline_input.json"

    with open(
        filename,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            indent=4,
            ensure_ascii=False
        )

    print(
        f"\nPipeline input saved to: {filename}"
    )


# ============================================================
# RETRIEVE RAG KNOWLEDGE
# ============================================================

def retrieve_pipeline_knowledge(rag_query):

    print("\n")
    print("================================================")
    print("     RETRIEVING KNOWLEDGE FROM CHROMADB")
    print("================================================")

    retrieved_results, detected_topics = retrieve_knowledge(
        rag_query
    )

    print(
        f"\nDetected topics: {', '.join(detected_topics)}"
    )

    print(
        f"Retrieved {len(retrieved_results)} relevant records."
    )

    # --------------------------------------------------------
    # DISPLAY RESULTS IN TERMINAL
    # --------------------------------------------------------

    for i, result in enumerate(
        retrieved_results,
        start=1
    ):

        metadata = result.get(
            "metadata",
            {}
        )

        print("\n")
        print(f"RESULT {i}")
        print("----------------------------------------")

        print(
            "Record ID:",
            metadata.get(
                "record_id",
                "Unknown"
            )
        )

        print(
            "Domain:",
            metadata.get(
                "domain",
                "Unknown"
            )
        )

        print(
            "Type:",
            metadata.get(
                "record_type",
                "Unknown"
            )
        )

        print(
            "Title:",
            metadata.get(
                "title",
                "Unknown"
            )
        )

        print(
            "Source:",
            metadata.get(
                "source_note",
                "Source verification required"
            )
        )

        print("\nKnowledge:")

        print(
            result.get(
                "document",
                ""
            )
        )

    print("\n")
    print("================================================")
    print("       RAG RETRIEVAL COMPLETE")
    print("================================================")

    return retrieved_results, detected_topics


# ============================================================
# MAIN BACKEND-FRIENDLY PIPELINE
# ============================================================

def run_pipeline(profile):

    """
    Main function used by the FastAPI backend.

    Frontend
        ↓
    FastAPI
        ↓
    run_pipeline(profile)
        ↓
    classification
        ↓
    RAG query
        ↓
    ChromaDB
        ↓
    structured result
    """

    # --------------------------------------------------------
    # STEP 1 + 2
    # --------------------------------------------------------

    pipeline_data = build_pipeline_input(
        profile=profile
    )

    # --------------------------------------------------------
    # STEP 3: CREATE RAG QUERY
    # --------------------------------------------------------

    rag_query = create_rag_query(
        pipeline_data
    )

    # --------------------------------------------------------
    # STEP 4: RETRIEVE KNOWLEDGE
    # --------------------------------------------------------

    retrieved_results, detected_topics = (
        retrieve_pipeline_knowledge(
            rag_query
        )
    )

    # --------------------------------------------------------
    # STEP 5: PREPARE API RESPONSE
    # --------------------------------------------------------

    return {
        "formulation_profile": pipeline_data[
            "formulation_profile"
        ],

        "classification": pipeline_data[
            "classification"
        ],

        "rag_query": rag_query,

        "detected_topics": detected_topics,

        "retrieved_results": retrieved_results
    }


# ============================================================
# DISPLAY PIPELINE
# ============================================================

def display_pipeline(data, rag_query):

    print("\n")
    print("================================================")
    print("             PIPELINE DATA READY")
    print("================================================")

    print("\nFORMULATION")
    print("------------------------------------------")

    print(
        data["formulation_profile"]
        ["formulation_name"]
    )

    print("\nREGULATORY CLASSIFICATION")
    print("------------------------------------------")

    print(
        data["classification"]
        ["regulatory_classification"]
        ["classification"]
    )

    print("\nABS ROUTE")
    print("------------------------------------------")

    print(
        data["classification"]
        ["abs_assessment"]
        ["route"]
    )

    print("\nPATENT SCREENING")
    print("------------------------------------------")

    print(
        data["classification"]
        ["patent_screening"]
        ["screening_flag"]
    )

    print("\nRAG QUERY")
    print("------------------------------------------")

    print(rag_query)


# ============================================================
# TERMINAL TEST MODE
# ============================================================

if __name__ == "__main__":

    # --------------------------------------------------------
    # Collect profile from terminal
    # --------------------------------------------------------

    pipeline_data = build_pipeline_input()

    # --------------------------------------------------------
    # Create RAG query
    # --------------------------------------------------------

    rag_query = create_rag_query(
        pipeline_data
    )

    # --------------------------------------------------------
    # Save input
    # --------------------------------------------------------

    save_pipeline_data(
        pipeline_data
    )

    # --------------------------------------------------------
    # Display pipeline
    # --------------------------------------------------------

    display_pipeline(
        pipeline_data,
        rag_query
    )

    print("\n")
    print("================================================")
    print("PIPELINE STEP 1 COMPLETE")
    print("================================================")

    # --------------------------------------------------------
    # Retrieve knowledge
    # --------------------------------------------------------

    retrieve_pipeline_knowledge(
        rag_query
    )