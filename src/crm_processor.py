
import json
import re
from pathlib import Path

import pandas as pd

from src.ai_extractor import extract_crm_data
from src.providers.gemini_provider import (
    TOKEN_USAGE,
    INPUT_COST_PER_MILLION_TOKENS,
    OUTPUT_COST_PER_MILLION_TOKENS,
    calculate_estimated_cost,
    reset_token_usage,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = PROJECT_ROOT / "data" / "sample_inputs.csv"
CRM_FILE = PROJECT_ROOT / "data" / "existing_crm.csv"
OUTPUT_DIR = PROJECT_ROOT / "outputs"

# Stage order used to detect backward movement.
STAGE_ORDER = {
    "New": 0,
    "Qualified": 1,
    "Proposal": 2,
    "Negotiation": 3,
    "Won": 4,
    "Lost": 5,
}

# Legal suffixes removed from the end of company names.
COMPANY_SUFFIXES = {
    "incorporated",
    "limited",
    "private",
    "inc",
    "ltd",
    "pvt",
    "llc",
    "co",
    "corp",
    "company",
}

# These columns must exist in the input CRM file.
REQUIRED_CRM_COLUMNS = [
    "company",
    "contact",
    "stage",
    "owner",
    "next_step",
    "next_step_date",
    "deal_value",
    "notes",
]


def normalize_company(name):
    """
    Normalize company names for exact matching.

    Lowercase the name, replace punctuation with spaces,
    remove repeated legal suffixes from the end, and join
    consecutive single-letter initials.

    Examples:
        ABC Ltd -> abc
        ABC Limited -> abc
        A.B.C. Limited -> abc
        Acme Tools Pvt. Ltd. -> acme tools
    """

    if not isinstance(name, str) or not name.strip():
        return ""

    name = name.lower()

    # Replace punctuation and other non-alphanumeric characters.
    name = re.sub(r"[^a-z0-9]", " ", name)

    words = name.split()

    # Remove legal suffixes repeatedly from the end.
    while words and words[-1] in COMPANY_SUFFIXES:
        words.pop()

    # Join consecutive single-letter initials.
    # This allows A.B.C. to match ABC.
    normalized_words = []
    initials = []

    for word in words:

        if len(word) == 1:
            initials.append(word)

        else:
            if initials:
                normalized_words.append("".join(initials))
                initials = []

            normalized_words.append(word)

    if initials:
        normalized_words.append("".join(initials))

    return " ".join(normalized_words)


def add_reason(reasons, message):
    """Add a review reason only if it is not already present."""

    if message not in reasons:
        reasons.append(message)


def get_numeric_value(value):
    """Convert a value to a non-negative number, if possible."""

    if value is None or str(value).strip() == "":
        return None

    try:
        number = float(str(value).replace(",", ""))

        if number < 0:
            return None

        return number

    except (TypeError, ValueError):
        return None



def safe_number(value):
    """Convert a value to float safely; return None if conversion fails."""
    if value is None:
        return None

    try:
        return float(str(value).replace(",", "").strip())
    except (ValueError, TypeError):
        return None


def check_business_rules(extracted, crm_row, reasons, source_text=None):
    """
    Apply Python-side safeguards before a CRM update.

    Returns True when the record must go for human review.
    """

    stage = extracted.get("stage")
    contact = extracted.get("contact")
    deal_value = extracted.get("deal_value")
    currency = extracted.get("currency")

    # 1. Explicitly unconfirmed budgets require human review.
    original_source = str(source_text or "").casefold()

    unconfirmed_budget_phrases = [
        "budget not confirmed",
        "budget is not confirmed",
        "budget not yet confirmed",
        "budget is not yet confirmed",
        "budget hasn't been confirmed",
        "budget has not been confirmed",
        "budget is yet to be confirmed",
    ]

    if any(phrase in original_source for phrase in unconfirmed_budget_phrases):
        add_reason(reasons, "Deal budget is explicitly unconfirmed.")

    # 2. Contact must be present.
    if not isinstance(contact, str) or not contact.strip():
        add_reason(reasons, "Contact name is missing.")

    # 3. Won and Lost stages require human confirmation.
    if stage in ("Won", "Lost"):
        add_reason(reasons, "Closing a deal requires human confirmation")

    # 4. Backward stage movement requires review.
    existing_stage = str(crm_row.get("stage", "")).strip()

    if (
        stage in STAGE_ORDER
        and existing_stage in STAGE_ORDER
        and STAGE_ORDER[stage] < STAGE_ORDER[existing_stage]
    ):
        add_reason(reasons, "Stage moves backwards")

    # 5. Deal currency must be INR when a value is provided.
    if deal_value is not None:
        if not currency:
            add_reason(reasons, "Deal currency is missing or unclear.")
        elif str(currency).strip().upper() != "INR":
            add_reason(reasons, "Deal currency is not INR.")

    # 6. Large deal value changes require review.
    existing_value = safe_number(crm_row.get("deal_value"))

    if deal_value is not None and existing_value is not None:
        if existing_value == 0 and deal_value != 0:
            add_reason(reasons, "Deal value changed from zero.")
        elif existing_value != 0:
            percentage_change = (
                abs(deal_value - existing_value) / abs(existing_value)
            ) * 100

            if percentage_change > 50:
                add_reason(
                    reasons,
                    "Deal value changed by more than 50%."
                )

    return bool(reasons)


def save_run_log(number_of_records):
    """Save accumulated token usage and estimated cost."""

    total_tokens = (
        TOKEN_USAGE["input_tokens"]
        + TOKEN_USAGE["output_tokens"]
    )

    total_cost = calculate_estimated_cost()

    cost_per_record = (
        total_cost / number_of_records
        if number_of_records > 0
        else 0
    )

    run_log = {
        "number_of_records": number_of_records,
        "input_tokens": TOKEN_USAGE["input_tokens"],
        "output_tokens": TOKEN_USAGE["output_tokens"],
        "total_tokens": total_tokens,
        "estimated_total_cost": total_cost,
        "estimated_cost_per_record": cost_per_record,
        "pricing": {
            "input_cost_per_million_tokens":
                INPUT_COST_PER_MILLION_TOKENS,
            "output_cost_per_million_tokens":
                OUTPUT_COST_PER_MILLION_TOKENS,
        },
        "pricing_note": (
            "Estimated cost based on editable pricing constants. "
            "A value of zero means pricing has not been configured."
        ),
    }

    with open(
        OUTPUT_DIR / "run_log.json",
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(run_log, file, indent=4)

    print("\nToken usage:")
    print(f"Input tokens: {TOKEN_USAGE['input_tokens']}")
    print(f"Output tokens: {TOKEN_USAGE['output_tokens']}")
    print(f"Total tokens: {total_tokens}")

    print(f"Estimated total cost: {total_cost:.6f}")
    print(f"Estimated cost per record: {cost_per_record:.6f}")


def process_crm_files(limit=None):
    """
    Process sales notes and create:
    1. Updated CRM CSV
    2. Human review CSV
    3. Token and cost run log
    4. Extraction results CSV for evaluation

    Inputs are processed chronologically, oldest to newest.
    Uncertain records are sent for human review.
    """

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Reset token counters before starting this run.
    reset_token_usage()

    # Load input records as strings.
    inputs = pd.read_csv(
        INPUT_FILE,
        dtype=str
    ).fillna("")

    # Load existing CRM records as strings.
    crm = pd.read_csv(
        CRM_FILE,
        dtype=str
    ).fillna("")

    # Check required CRM columns before processing.
    missing_columns = [
        column
        for column in REQUIRED_CRM_COLUMNS
        if column not in crm.columns
    ]

    if missing_columns:
        raise ValueError(
            "The existing_crm.csv file is missing required "
            f"columns: {', '.join(missing_columns)}. "
            f"Available columns: {', '.join(crm.columns)}"
        )

    # Currency is a new output field.
    # Add it if the original CRM file does not have it.
    if "currency" not in crm.columns:
        crm["currency"] = ""

    # Check required input columns.
    required_input_columns = [
        "input_id",
        "source_date",
        "source_text"
    ]

    missing_input_columns = [
        column
        for column in required_input_columns
        if column not in inputs.columns
    ]

    if missing_input_columns:
        raise ValueError(
            "The sample_inputs.csv file is missing required "
            f"columns: {', '.join(missing_input_columns)}"
        )

    # Parse dates for chronological processing.
    inputs["source_date"] = pd.to_datetime(
        inputs["source_date"],
        errors="coerce"
    )

    # Process records from oldest to newest.
    inputs = inputs.sort_values(
        by=["source_date", "input_id"],
        na_position="last"
    ).reset_index(drop=True)

    # Limit API calls when testing.
    if limit is not None:
        inputs = inputs.head(limit)

    review_records = []

    extraction_records = []

    for _, row in inputs.iterrows():

        input_id = row["input_id"]
        source_text = row["source_text"]
        source_date = row["source_date"]

        print(f"\nProcessing {input_id}...")

        source_date_text = (
            source_date.strftime("%Y-%m-%d")
            if pd.notna(source_date)
            else ""
        )

        try:
            extracted = extract_crm_data(
                source_text=source_text,
                source_date=source_date_text
            )

        except Exception as error:
            extracted = {
                "needs_review": True,
                "review_reasons": [
                    f"Extraction failed: {error}"
                ],
            }

        reasons = list(
            extracted.get("review_reasons") or []
        )

        # Ensure a model review flag always has an explanation.
        if extracted.get("needs_review") and not reasons:
            add_reason(
                reasons,
                "Model flagged for review without explanation"
            )

        company = extracted.get("company")

        normalized_name = normalize_company(company)

        matches = []

        if normalized_name:
            matches = crm.index[
                crm["company"].apply(normalize_company)
                == normalized_name
            ].tolist()

        # Require one exact normalized company match.
        if not company:
            add_reason(reasons, "Company name is missing.")

        elif len(matches) == 0:
            add_reason(
                reasons,
                "No existing CRM company match. "
                "New lead requires review."
            )

        elif len(matches) > 1:
            add_reason(
                reasons,
                "Multiple CRM company matches found."
            )

        # A valid source date is required for chronological updates.
        if not source_date_text:
            add_reason(
                reasons,
                "Source date is missing or invalid."
            )

        # Only apply business rules when exactly one company matches.
        if len(matches) == 1:
            crm_index = matches[0]
            crm_row = crm.loc[crm_index]

            check_business_rules(
            extracted,
            crm_row,
            reasons,
            source_text
            )
                # Save every extraction for later evaluation.
        # Record the final review decision after Python safeguards.
        extraction_records.append({
            "input_id": input_id,
            "extracted_data": json.dumps(
                extracted,
                default=str
            ),
            "needs_review": bool(reasons),
            "review_reasons": " | ".join(reasons)
        })
        # Any review reason prevents automatic CRM updates.
        if reasons:

            review_records.append({
                "input_id": input_id,
                "company": company or "",
                "contact": extracted.get("contact") or "",
                "review_reasons": " | ".join(reasons),
                "source_text": source_text,
                "extracted_data": json.dumps(
                    extracted,
                    default=str
                )
            })

            print(f"{input_id} sent for human review.")
            continue

        # A single reliable company match is available here.
        crm_index = matches[0]

        # Update only fields containing extracted values.
        fields = [
            "contact",
            "stage",
            "next_step",
            "next_step_date",
            "deal_value",
            "currency",
            "notes"
        ]

        for field in fields:

            value = extracted.get(field)

            if value is None or value == "":
                continue

            if field == "notes":

                old_notes = str(
                    crm.at[crm_index, field]
                ).strip()

                if value not in old_notes:

                    crm.at[crm_index, field] = (
                        old_notes + "; " + value
                        if old_notes
                        else value
                    )

            else:
                crm.at[crm_index, field] = str(value)

        print(f"{input_id} updated successfully.")

    # Save the updated CRM.
    crm.to_csv(
        OUTPUT_DIR / "updated_crm.csv",
        index=False
    )

    # Save records requiring human review.
    review_columns = [
        "input_id",
        "company",
        "contact",
        "review_reasons",
        "source_text",
        "extracted_data"
    ]

    review_df = pd.DataFrame(
        review_records,
        columns=review_columns
    )

    review_df.to_csv(
        OUTPUT_DIR / "human_review.csv",
        index=False
    )
        # Save all extraction results for evaluation.
    extraction_df = pd.DataFrame(
        extraction_records,
        columns=[
            "input_id",
            "extracted_data",
            "needs_review",
            "review_reasons"
        ]
    )

    extraction_df.to_csv(
        OUTPUT_DIR / "extraction_results.csv",
        index=False
    )

    # Save token usage and estimated cost.
    save_run_log(len(inputs))

    print("\nProcessing completed.")
    print(f"CRM records: {len(crm)}")
    print(f"Input records processed: {len(inputs)}")
    print(f"Records requiring review: {len(review_df)}")

    print("\nOutput files:")
    print("outputs/updated_crm.csv")
    print("outputs/human_review.csv")
    print("outputs/extraction_results.csv")
    print("outputs/run_log.json")


if __name__ == "__main__":
    process_crm_files(limit=None)
