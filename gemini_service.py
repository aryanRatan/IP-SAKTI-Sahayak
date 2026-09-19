import os
from google import genai
from google.genai import types
from dotenv import load_dotenv
from typer import prompt
from typer import prompt

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY is missing. Add it to your .env file."
    )

client = genai.Client(
    api_key=GEMINI_API_KEY,
    http_options=types.HttpOptions(
        timeout=60000
    )
)


MODEL_NAME = "gemini-3.5-flash-lite"


def generate_grounded_analysis(
    formulation_profile,
    classification,
    retrieved_results
):

    evidence_text = ""

    for index, result in enumerate(
        retrieved_results,
        start=1
    ):

        metadata = result.get(
            "metadata",
            {}
        )

        evidence_text += f"""

EVIDENCE {index}

Record ID:
{metadata.get("record_id", "Unknown")}

Domain:
{metadata.get("domain", "Unknown")}

Type:
{metadata.get("record_type", "Unknown")}

Title:
{metadata.get("title", "Unknown")}

Source:
{metadata.get("source_note", "Verification required")}

Content:
{result.get("document", "")}

----------------------------------------
"""

    prompt = f"""
You are IP-SAKTI Sahayak, an evidence-grounded
decision-support assistant for Ayurveda IP,
biodiversity and regulatory triage.

IMPORTANT RULES:

1. Use ONLY the supplied formulation profile,
classification results and retrieved evidence.

2. Do NOT invent laws, sections, rules, treaties,
citations, authorities or requirements.

3. Do NOT claim that an invention is legally
patentable or unpatentable.

4. Do NOT claim that ABS approval, a licence,
registration or certification is definitely required
unless the supplied evidence supports that conclusion.

5. Clearly distinguish:
   - evidence-supported facts
   - project screening flags
   - uncertainty
   - human-review requirements

6. If the evidence is insufficient, explicitly say:
   "Evidence insufficient — human verification required."

7. Every important legal/regulatory statement should
reference the relevant Evidence number.

8. This is decision support, NOT legal advice.

FORMULATION PROFILE:

{formulation_profile}


CLASSIFICATION:

{classification}


RETRIEVED EVIDENCE:

{evidence_text}


Produce a concise structured analysis with these sections:

1. FORMULATION SUMMARY

2. REGULATORY CLASSIFICATION
Explain the classification and cite Evidence numbers
where applicable.

3. TRADITIONAL KNOWLEDGE / PRIOR-ART SIGNAL
Explain whether the retrieved evidence indicates
a traditional-knowledge or prior-art issue.

4. ABS / BIODIVERSITY REVIEW
Explain the sourcing-related issue and uncertainty.

5. IP / PATENT SCREENING
Explain what technical feature should be investigated.
Do NOT declare patentability.

6. INTERNATIONAL MARKET
Explain that international requirements depend on
the selected destination market.

7. RECOMMENDED ACTION PLAN
Give 4-6 practical next steps in order.

8. CONFIDENCE AND HUMAN REVIEW
State what is well-supported and what requires
professional verification.

Use plain language suitable for a startup founder
or researcher.
"""

    try:
        import time
        start_time = time.time()
        print("GEMINI STARTED...")

        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        )
        print(f"GEMINI FINISHED IN {time.time() - start_time:.2f} seconds")

        return response.text

    except Exception as e:

        print("\nGEMINI ERROR:")
        print(e)

        return (
            "Gemini synthesis is temporarily unavailable. "
            "The RAG evidence and rule-based analysis are still available. "
            "Human verification is recommended."
        )