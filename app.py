from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pipeline import run_pipeline
from gemini_service import generate_grounded_analysis

app = FastAPI(
    title="IP-SAKTI Sahayak API",
    description="AI-assisted IP, Ayurveda and regulatory decision-support backend",
    version="1.0.0"
)

# Allow frontend to communicate with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "project": "IP-SAKTI Sahayak",
        "status": "Backend running",
        "message": "IP-SAKTI API is working"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }



    # ============================================================
# ANALYZE FORMULATION
# ============================================================

from pydantic import BaseModel
from rag import retrieve_knowledge


class AnalysisRequest(BaseModel):
    formulation_text: str
    profile: dict | None = None

def convert_frontend_profile(frontend_profile):

    answers = frontend_profile.get(
        "intakeAnswers",
        {}
    )

    # --------------------------------------------------
    # USER ANSWERS
    # --------------------------------------------------

    applicant_type = answers.get(
        "applicant_type",
        "indian_startup_msme"
    )

    sourcing_method = answers.get(
        "sourcing_method",
        "unknown"
    )

    classical_answer = answers.get(
        "classical_formulation",
        "unsure"
    )

    modification = answers.get(
        "modification",
        "completely_novel_combination"
    )

    standardization = answers.get(
        "standardization",
        "raw_churna_powder"
    )

    target_market = answers.get(
        "target_market",
        "india"
    )

    # --------------------------------------------------
    # CLASSICAL FORMULATION
    # --------------------------------------------------

    is_classical = (
        classical_answer == "yes"
    )

    if is_classical:
        base_text_name = (
            "User-reported classical Ayurveda basis"
        )
    else:
        base_text_name = ""

    # --------------------------------------------------
    # INGREDIENT
    # --------------------------------------------------

    ingredient_text = frontend_profile.get(
        "ingredients",
        ""
    )

    ingredient = {
        "sanskrit_name": "Not provided",

        "botanical_name": ingredient_text,

        "plant_part": "Not provided",

        "sourcing_method": sourcing_method
    }

    # --------------------------------------------------
    # FINAL STRUCTURED PROFILE
    # --------------------------------------------------

    profile = {

        "formulation_name":
            frontend_profile.get(
                "name",
                frontend_profile.get(
                    "formulation_name",
                    ""
                )
            ),

        "applicant_type":
            applicant_type,

        "ingredients": [
            ingredient
        ],

        "classical_reference": {

            "is_based_on_classical_text":
                is_classical,

            "base_text_name":
                base_text_name,

            "degree_of_modification":
                modification
        },

        "standardization_level":
            standardization,

        "target_delivery_form":
            "capsule",

        "synergistic_data_provided":
            False,

        "foreign_shareholding":
            False,

        # Keep international market information
        # available for the later Gemini layer.
        "target_market":
            target_market
    }

    print(
        "\nCONVERTED INTAKE PROFILE:"
    )

    print(profile)

    return profile
@app.post("/analyze")
def analyze_formulation(request: AnalysisRequest):

    if not request.formulation_text.strip():
        return {
            "success": False,
            "message": "Formulation description is required."
        }

    print("\n========================================")
    print("IP-SAKTI ANALYSIS REQUEST")
    print("========================================")

    print("Formulation:", request.formulation_text)

    # Use structured frontend profile if provided
    gemini_analysis = None
    if request.profile:

        print("Structured profile received.")

        pipeline_profile = convert_frontend_profile(request.profile)
        pipeline_result = run_pipeline(pipeline_profile)




        retrieved_results = pipeline_result["retrieved_results"]
        detected_topics = pipeline_result["detected_topics"]

        gemini_analysis = generate_grounded_analysis(
        formulation_profile=pipeline_result["formulation_profile"],
        classification=pipeline_result["classification"],
        retrieved_results=retrieved_results
    )

    else:

        print("No structured profile received.")
        print("Using direct RAG search for MVP.")

        retrieved_results, detected_topics = retrieve_knowledge(
            request.formulation_text
        )

        pipeline_result = None

    sources = []

    for result in retrieved_results:

        metadata = result.get("metadata", {})

        sources.append({
            "record_id": metadata.get(
                "record_id",
                "Unknown"
            ),

            "domain": metadata.get(
                "domain",
                "Unknown"
            ),

            "type": metadata.get(
                "record_type",
                "Unknown"
            ),

            "title": metadata.get(
                "title",
                "Unknown"
            ),

            "source": metadata.get(
                "source_note",
                "Verification required"
            ),

            "knowledge": result.get(
                "document",
                ""
            )
        })

    print(
        f"Retrieved {len(sources)} evidence records."
    )

    return {
        "success": True,

        "query":
            request.formulation_text,

        "detected_topics":
            list(detected_topics),

        "retrieved_count":
            len(sources),

        "sources":
            sources,

        "pipeline":
            pipeline_result,
        "gemini_analysis": 
            gemini_analysis,
    }

    query = request.formulation_text.strip()

    if not query:
        return {
            "success": False,
            "message": "Formulation description is required."
        }

    print("\n========================================")
    print("IP-SAKTI BACKEND ANALYSIS")
    print("========================================")

    print("Query received:")
    print(query)

    # Retrieve evidence from ChromaDB
    retrieved_results, detected_topics = retrieve_knowledge(query)

    sources = []

    for result in retrieved_results:

        metadata = result.get(
            "metadata",
            {}
        )

        sources.append({
            "record_id": metadata.get(
                "record_id",
                "Unknown"
            ),

            "domain": metadata.get(
                "domain",
                "Unknown"
            ),

            "type": metadata.get(
                "record_type",
                "Unknown"
            ),

            "title": metadata.get(
                "title",
                "Unknown"
            ),

            "source": metadata.get(
                "source_note",
                "Verification required"
            ),

            "knowledge": result.get(
                "document",
                ""
            )
        })

    print(
        f"Retrieved {len(sources)} records."
    )

    return {
        "success": True,

        "query": query,

        "detected_topics": detected_topics,

        "retrieved_count": len(sources),

        "sources": sources
    }