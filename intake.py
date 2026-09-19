import json


# ============================================================
# IP-SAKTI SAHAYAK
# FORMULATION INTAKE + CLASSIFICATION ENGINE
# ============================================================


# ============================================================
# 1. OPTIONS
# ============================================================

APPLICANT_TYPES = {
    "1": "indian_individual_vaidya",
    "2": "indian_startup_msme",
    "3": "indian_academic_researcher",
    "4": "foreign_entity_or_multinational"
}


SOURCING_METHODS = {
    "1": "wild_collected",
    "2": "cultivated_farmed",
    "3": "imported",
    "4": "unknown"
}


MODIFICATION_TYPES = {
    "1": "unmodified_exact_recipe",
    "2": "minor_excipient_change",
    "3": "added_new_herbs",
    "4": "extracted_active_fractions",
    "5": "completely_novel_combination"
}


STANDARDIZATION_TYPES = {
    "1": "raw_churna_powder",
    "2": "aqueous_extract_kwath",
    "3": "hydroalcoholic_extract",
    "4": "quantitatively_standardized_marker_extract"
}


# ============================================================
# 2. HELPER FUNCTIONS
# ============================================================

def ask_choice(question, choices):

    print("\n" + question)

    for key, value in choices.items():
        print(f"{key}. {value}")

    while True:

        answer = input("\nEnter choice: ").strip()

        if answer in choices:
            return choices[answer]

        print("Invalid choice. Please enter one of the numbers above.")


def ask_yes_no(question):

    while True:

        answer = input(
            f"\n{question} (yes/no): "
        ).strip().lower()

        if answer in ["yes", "y"]:

            return True

        if answer in ["no", "n"]:

            return False

        print("Please enter yes or no.")


def ask_non_empty(question):

    while True:

        answer = input(
            f"\n{question}: "
        ).strip()

        if answer:

            return answer

        print("This field cannot be empty.")


# ============================================================
# 3. INGREDIENT INTAKE
# ============================================================

def collect_ingredient(number):

    print("\n------------------------------------------")

    print(f"INGREDIENT {number}")

    print("------------------------------------------")


    sanskrit_name = ask_non_empty(
        "Sanskrit name"
    )


    botanical_name = ask_non_empty(
        "Botanical name"
    )


    plant_part = ask_non_empty(
        "Plant part used"
    )


    sourcing_method = ask_choice(
        "How is this ingredient sourced?",
        SOURCING_METHODS
    )


    return {

        "sanskrit_name": sanskrit_name,

        "botanical_name": botanical_name,

        "plant_part": plant_part,

        "sourcing_method": sourcing_method
    }


# ============================================================
# 4. FORMULATION INTAKE
# ============================================================

def collect_profile():

    print("\n")
    print("================================================")
    print("              IP-SAKTI SAHAYAK")
    print("          FORMULATION INTAKE SYSTEM")
    print("================================================")


    # --------------------------------------------------------
    # FORMULATION NAME
    # --------------------------------------------------------

    formulation_name = ask_non_empty(
        "Formulation name"
    )


    # --------------------------------------------------------
    # APPLICANT
    # --------------------------------------------------------

    applicant_type = ask_choice(
        "Who is the applicant?",
        APPLICANT_TYPES
    )


    # --------------------------------------------------------
    # INGREDIENT COUNT
    # --------------------------------------------------------

    while True:

        try:

            ingredient_count = int(
                input(
                    "\nHow many ingredients? "
                ).strip()
            )

            if ingredient_count > 0:

                break

            print(
                "Enter a number greater than 0."
            )

        except ValueError:

            print(
                "Please enter a valid number."
            )


    # --------------------------------------------------------
    # INGREDIENTS
    # --------------------------------------------------------

    ingredients = []


    for number in range(
        1,
        ingredient_count + 1
    ):

        ingredient = collect_ingredient(
            number
        )

        ingredients.append(
            ingredient
        )


    # --------------------------------------------------------
    # CLASSICAL REFERENCE
    # --------------------------------------------------------

    is_classical = ask_yes_no(
        "Is the formulation based on a classical Ayurveda text?"
    )


    base_text_name = ""


    if is_classical:

        base_text_name = ask_non_empty(
            "Name of classical text/reference"
        )


    # --------------------------------------------------------
    # DEGREE OF MODIFICATION
    # --------------------------------------------------------

    modification = ask_choice(
        "What is the degree of modification?",
        MODIFICATION_TYPES
    )


    # --------------------------------------------------------
    # STANDARDIZATION
    # --------------------------------------------------------

    standardization = ask_choice(
        "What is the standardization level?",
        STANDARDIZATION_TYPES
    )


    # --------------------------------------------------------
    # DELIVERY FORM
    # --------------------------------------------------------

    target_delivery_form = ask_non_empty(
        "Target delivery form "
        "(capsule/churna/tablet/etc.)"
    )


    # --------------------------------------------------------
    # SYNERGISTIC DATA
    # --------------------------------------------------------

    synergistic_data = ask_yes_no(
        "Is synergistic data/evidence available?"
    )


    # --------------------------------------------------------
    # FOREIGN SHAREHOLDING
    # --------------------------------------------------------

    foreign_shareholding = False


    if applicant_type == "indian_startup_msme":

        foreign_shareholding = ask_yes_no(
            "Does the applicant have foreign shareholding?"
        )


    # --------------------------------------------------------
    # STRUCTURED PROFILE
    # --------------------------------------------------------

    profile = {

        "formulation_name":
            formulation_name,

        "applicant_type":
            applicant_type,

        "ingredients":
            ingredients,

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
            target_delivery_form,

        "synergistic_data_provided":
            synergistic_data,

        "foreign_shareholding":
            foreign_shareholding
    }


    return profile


# ============================================================
# 5. REGULATORY CLASSIFICATION
# ============================================================

def classify_regulatory_route(profile):

    classical = profile[
        "classical_reference"
    ]


    modification = classical[
        "degree_of_modification"
    ]


    standardization = profile[
        "standardization_level"
    ]


    # --------------------------------------------------------
    # CLASSICAL ASU
    # --------------------------------------------------------

    if modification == "unmodified_exact_recipe":

        return {

            "classification":
                "Classical ASU Drug",

            "basis":
                "Unmodified exact classical recipe",

            "reference":
                "Rule 158-B",

            "confidence":
                "source-derived project rule; verify applicable provision"
        }


    # --------------------------------------------------------
    # PHYTOPHARMACEUTICAL
    # --------------------------------------------------------

    if (

        standardization
        == "quantitatively_standardized_marker_extract"

        and modification in [

            "extracted_active_fractions",

            "completely_novel_combination"
        ]

    ):

        return {

            "classification":
                "Phytopharmaceutical Drug",

            "basis":
                "Quantitatively standardized marker extract with specified modification",

            "reference":
                "CDSCO Rule 2(bb) / New Drugs Rules 2019",

            "confidence":
                "source-derived project rule; verify applicable provision"
        }


    # --------------------------------------------------------
    # P&P
    # --------------------------------------------------------

    return {

        "classification":
            "Patent & Proprietary (P&P) ASU Medicine",

        "basis":
            "Does not satisfy the supplied Classical or Phytopharmaceutical branches",

        "reference":
            "Section 3(h), Act 1940",

        "confidence":
            "source-derived project rule; verify applicable provision"
    }


# ============================================================
# 6. ABS ASSESSMENT
# ============================================================

def assess_abs(profile):

    applicant = profile[
        "applicant_type"
    ]


    foreign_shareholding = profile[
        "foreign_shareholding"
    ]


    ingredients = profile[
        "ingredients"
    ]


    sourcing_methods = [

        ingredient["sourcing_method"]

        for ingredient in ingredients
    ]


    # --------------------------------------------------------
    # FOREIGN ENTITY / FOREIGN SHAREHOLDING
    # --------------------------------------------------------

    if (

        applicant
        == "foreign_entity_or_multinational"

        or foreign_shareholding
    ):

        return {

            "route":
                "NBA route / ABS assessment",

            "trigger":
                "Foreign entity or foreign shareholding",

            "reference":
                "BDA Sections 3 and 6",

            "status":
                "Requires verification"
        }


    # --------------------------------------------------------
    # WILD-COLLECTED RESOURCE
    # --------------------------------------------------------

    if (

        "wild_collected"
        in sourcing_methods

        and applicant in [

            "indian_startup_msme",

            "indian_individual_vaidya"
        ]

    ):

        return {

            "route":
                "SBB notification / ABS compliance assessment",

            "trigger":
                "Wild-collected biological resource",

            "reference":
                "BDA Section 7",

            "status":
                "Requires verification"
        }


    # --------------------------------------------------------
    # ALL CULTIVATED
    # --------------------------------------------------------

    if (

        len(sourcing_methods) > 0

        and all(

            method == "cultivated_farmed"

            for method in sourcing_methods
        )

    ):

        return {

            "route":
                "Cultivated-resource branch",

            "trigger":
                "All ingredients marked cultivated",

            "reference":
                "Supplied project ABS decision logic",

            "status":
                "Verify applicable exemption/requirements"
        }


    # --------------------------------------------------------
    # UNKNOWN / MIXED
    # --------------------------------------------------------

    return {

        "route":
            "ABS applicability requires review",

        "trigger":
            "Sourcing information is incomplete or mixed",

        "reference":
            "Biodiversity/ABS decision logic",

        "status":
            "Human review recommended"
    }


# ============================================================
# 7. PATENT SCREENING
# ============================================================

def screen_patent(profile):

    classical = profile[
        "classical_reference"
    ]


    is_classical = classical[
        "is_based_on_classical_text"
    ]


    modification = classical[
        "degree_of_modification"
    ]


    synergistic_data = profile[
        "synergistic_data_provided"
    ]


    standardization = profile[
        "standardization_level"
    ]


    # --------------------------------------------------------
    # TRADITIONAL KNOWLEDGE / CLASSICAL OVERLAP
    # --------------------------------------------------------

    if (

        is_classical

        and modification in [

            "unmodified_exact_recipe",

            "minor_excipient_change"
        ]

    ):

        return {

            "screening_flag":
                "HIGH RISK / REQUIRES REVIEW",

            "reason":
                "Potential traditional-knowledge or known-formulation overlap",

            "reference":
                "Section 3(p)",

            "action":
                "Perform detailed prior-art and traditional-knowledge screening"
        }


    # --------------------------------------------------------
    # MERE ADMIXTURE SCREEN
    # --------------------------------------------------------

    if (

        modification
        == "added_new_herbs"

        and not synergistic_data

    ):

        return {

            "screening_flag":
                "HIGH RISK / REQUIRES REVIEW",

            "reason":
                "Potential mere-admixture issue",

            "reference":
                "Section 3(e)",

            "action":
                "Assess evidence and applicable patent requirements"
        }


    # --------------------------------------------------------
    # STANDARDIZED EXTRACT
    # --------------------------------------------------------

    if (

        standardization
        == "quantitatively_standardized_marker_extract"

        and synergistic_data

    ):

        return {

            "screening_flag":
                "POTENTIALLY RELEVANT FOR FURTHER PATENT ASSESSMENT",

            "reason":
                "Standardized marker extract with synergistic evidence",

            "reference":
                "Supplied project screening logic",

            "action":
                "Perform full patentability and prior-art assessment"
        }


    # --------------------------------------------------------
    # DEFAULT
    # --------------------------------------------------------

    return {

        "screening_flag":
            "FURTHER ASSESSMENT REQUIRED",

        "reason":
            "Available intake information does not resolve patent screening",

        "reference":
            "Supplied project screening logic",

        "action":
            "Retrieve relevant legal and prior-art evidence"
    }


# ============================================================
# 8. OVERALL CLASSIFICATION
# ============================================================

def classify(profile):

    regulatory = classify_regulatory_route(
        profile
    )


    abs_result = assess_abs(
        profile
    )


    patent = screen_patent(
        profile
    )


    return {

        "regulatory_classification":
            regulatory,

        "abs_assessment":
            abs_result,

        "patent_screening":
            patent
    }


# ============================================================
# 9. DISPLAY RESULT
# ============================================================

def display_result(
    profile,
    classification
):

    print("\n")
    print("================================================")
    print("              IP-SAKTI TRIAGE RESULT")
    print("================================================")


    # --------------------------------------------------------
    # FORMULATION
    # --------------------------------------------------------

    print("\nFORMULATION")
    print("------------------------------------------")


    print(
        "Name:",
        profile["formulation_name"]
    )


    print(
        "Applicant:",
        profile["applicant_type"]
    )


    print(
        "Delivery form:",
        profile["target_delivery_form"]
    )

    # INGREDIENTS

    print("\nINGREDIENTS")
    print("------------------------------------------")


    for ingredient in profile[
        "ingredients"
    ]:

        print(
            f"- {ingredient['sanskrit_name']} "
            f"({ingredient['botanical_name']})"
        )


        print(
            f"  Plant part: "
            f"{ingredient['plant_part']}"
        )


        print(
            f"  Sourcing: "
            f"{ingredient['sourcing_method']}"
        )

    # REGULATORY
    print("\nREGULATORY CLASSIFICATION")
    print("------------------------------------------")


    regulatory = classification[
        "regulatory_classification"
    ]


    print(
        "Classification:",
        regulatory["classification"]
    )


    print(
        "Basis:",
        regulatory["basis"]
    )


    print(
        "Reference:",
        regulatory["reference"]
    )

    # ABS

    print("\nABS ASSESSMENT")
    print("------------------------------------------")


    abs_result = classification[
        "abs_assessment"
    ]


    print(
        "Route:",
        abs_result["route"]
    )


    print(
        "Trigger:",
        abs_result["trigger"]
    )


    print(
        "Reference:",
        abs_result["reference"]
    )


    print(
        "Status:",
        abs_result["status"]
    )
    # PATENT
    print("\nPATENT SCREENING")
    print("------------------------------------------")


    patent = classification[
        "patent_screening"
    ]


    print(
        "Flag:",
        patent["screening_flag"]
    )


    print(
        "Reason:",
        patent["reason"]
    )


    print(
        "Reference:",
        patent["reference"]
    )


    print(
        "Action:",
        patent["action"]
    )
    # DISCLAIMER
    print("\n================================================")

    print(
        "MVP decision-support result."
    )

    print(
        "Verify applicable laws, rules and"
    )

    print(
        "official sources before filing,"
    )

    print(
        "licensing or regulatory action."
    )

    print("================================================")



# 10. MAIN PROGRAM


if __name__ == "__main__":

    print("\nStarting IP-SAKTI Intake...\n")


    # Collect user information

    profile = collect_profile()


    # Run classification

    print("\nClassifying formulation...")


    classification = classify(
        profile
    )


    # Display human-readable result

    display_result(
        profile,
        classification
    )

    # OUTPUT JSON

    print("\n\nSTRUCTURED JSON")

    print("------------------------------------------")


    output = {

        "formulation_profile":
            profile,

        "classification":
            classification
    }


    print(
        json.dumps(
            output,
            indent=4,
            ensure_ascii=False
        )
    )