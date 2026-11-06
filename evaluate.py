
import json
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent

GROUND_TRUTH_FILE = PROJECT_ROOT / "data" / "ground_truth.csv"
EXTRACTION_FILE = PROJECT_ROOT / "outputs" / "extraction_results.csv"
OUTPUT_DIR = PROJECT_ROOT / "outputs"

FIELDS_TO_EVALUATE = [
    "company",
    "stage",
    "next_step_date",
    "deal_value",
]


def normalize_company(value):
    """Normalize company names for fair comparison."""

    if value is None or pd.isna(value):
        return ""

    import re

    value = str(value).strip().lower()
    value = re.sub(r"[^a-z0-9]", " ", value)

    words = value.split()

    suffixes = {
        "incorporated", "limited", "private",
        "inc", "ltd", "pvt", "llc",
        "co", "corp", "company"
    }

    while words and words[-1] in suffixes:
        words.pop()

    result = []
    initials = []

    for word in words:
        if len(word) == 1:
            initials.append(word)
        else:
            if initials:
                result.append("".join(initials))
                initials = []

            result.append(word)

    if initials:
        result.append("".join(initials))

    return " ".join(result)


def normalize_value(field, value):
    """Normalize values before comparing them."""

    if value is None or pd.isna(value) or str(value).strip() == "":
        return None

    if field == "company":
        return normalize_company(value)

    if field == "stage":
        return str(value).strip().casefold()

    if field == "next_step_date":
        parsed_date = pd.to_datetime(value, errors="coerce")

        if pd.isna(parsed_date):
            return None

        return parsed_date.strftime("%Y-%m-%d")

    if field == "deal_value":
        try:
            return round(float(str(value).replace(",", "")), 2)
        except (ValueError, TypeError):
            return None

    return str(value).strip()


def parse_boolean(value):
    """Convert a CSV boolean value into a Python boolean."""

    if isinstance(value, bool):
        return value

    return str(value).strip().lower() in ("true", "1", "yes")


def parse_extraction(value):
    """
    Parse the extracted JSON and identify failed API requests.

    Returns:
        extracted_data: Parsed dictionary or empty dictionary.
        failure_reason: Error message if extraction failed.
    """

    try:
        extracted_data = json.loads(value)

        if not isinstance(extracted_data, dict):
            return {}, "Invalid extraction: JSON is not an object."

    except (json.JSONDecodeError, TypeError, ValueError):
        return {}, "Invalid extraction: JSON could not be parsed."

    review_reasons = extracted_data.get("review_reasons", [])

    if isinstance(review_reasons, str):
        review_reasons = [review_reasons]

    if not isinstance(review_reasons, list):
        review_reasons = []

    # API failures are recorded in the extraction review reasons.
    for reason in review_reasons:
        if isinstance(reason, str) and reason.startswith("Extraction failed:"):
            return extracted_data, reason

    # An empty extraction is not a successful extraction.
    extracted_fields = [
        extracted_data.get(field)
        for field in FIELDS_TO_EVALUATE
    ]

    if not any(value is not None and str(value).strip() for value in extracted_fields):
        return extracted_data, "No CRM fields were extracted."

    return extracted_data, None


def main():

    if not GROUND_TRUTH_FILE.exists():
        raise FileNotFoundError(
            f"Ground truth file not found: {GROUND_TRUTH_FILE}"
        )

    if not EXTRACTION_FILE.exists():
        raise FileNotFoundError(
            "Extraction results not found. "
            "Run the CRM application first: python -m src.main"
        )

    ground_truth = pd.read_csv(
        GROUND_TRUTH_FILE,
        dtype=str
    ).fillna("")

    extraction_results = pd.read_csv(
        EXTRACTION_FILE,
        dtype=str
    ).fillna("")

    required_ground_truth = [
        "input_id",
        "company",
        "stage",
        "next_step_date",
        "deal_value",
        "should_be_reviewed",
    ]

    required_extraction = [
        "input_id",
        "extracted_data",
        "needs_review",
    ]

    for column in required_ground_truth:
        if column not in ground_truth.columns:
            raise ValueError(
                f"Missing ground-truth column: {column}"
            )

    for column in required_extraction:
        if column not in extraction_results.columns:
            raise ValueError(
                f"Missing extraction-results column: {column}"
            )

    if ground_truth["input_id"].duplicated().any():
        raise ValueError("Duplicate input IDs in ground_truth.csv")

    if extraction_results["input_id"].duplicated().any():
        raise ValueError(
            "Duplicate input IDs in extraction_results.csv"
        )

    # Match actual extraction results with expected answers.
    merged = ground_truth.merge(
        extraction_results,
        on="input_id",
        how="outer",
        indicator=True
    )

    if not (merged["_merge"] == "both").all():
        mismatches = merged.loc[
            merged["_merge"] != "both",
            ["input_id", "_merge"]
        ]

        raise ValueError(
            "Ground-truth and extraction input IDs do not match:\n"
            + mismatches.to_string(index=False)
        )

    detailed_results = []

    field_correct_counts = {
        field: 0 for field in FIELDS_TO_EVALUATE
    }

    successful_records = 0
    failed_records = 0
    api_failure_count = 0
    failure_details = []

    # Process each record individually.
    for _, row in merged.iterrows():

        actual, failure_reason = parse_extraction(
            row["extracted_data"]
        )

        extraction_success = failure_reason is None

        if extraction_success:
            successful_records += 1
        else:
            failed_records += 1

            if failure_reason.startswith("Extraction failed:"):
                api_failure_count += 1

            failure_details.append({
                "input_id": row["input_id"],
                "failure_reason": failure_reason
            })

        result = {
            "input_id": row["input_id"],
            "extraction_status": (
                "success" if extraction_success else "failed"
            ),
            "failure_reason": failure_reason or ""
        }

        # Evaluate fields only when extraction succeeded.
        for field in FIELDS_TO_EVALUATE:

            if extraction_success:

                expected_value = normalize_value(
                    field,
                    row[field]
                )

                actual_value = normalize_value(
                    field,
                    actual.get(field)
                )

                is_correct = expected_value == actual_value

                result[f"{field}_expected"] = expected_value
                result[f"{field}_actual"] = actual_value
                result[f"{field}_correct"] = is_correct

                if is_correct:
                    field_correct_counts[field] += 1

            else:
                # None means this field was not evaluated.
                result[f"{field}_expected"] = normalize_value(
                    field,
                    row[field]
                )

                result[f"{field}_actual"] = None
                result[f"{field}_correct"] = None

        # Evaluate review decisions only for successful extractions.
        if extraction_success:

            expected_review = parse_boolean(
                row["should_be_reviewed"]
            )

            actual_review = parse_boolean(
                row["needs_review"]
            )

            result["review_expected"] = expected_review
            result["review_actual"] = actual_review

            result["review_correct"] = (
                expected_review == actual_review
            )

        else:
            result["review_expected"] = None
            result["review_actual"] = None
            result["review_correct"] = None

        detailed_results.append(result)

    details_df = pd.DataFrame(detailed_results)

    if successful_records == 0:
        raise ValueError(
            "No successful extractions are available for evaluation."
        )

    # Display evaluation results.
    print("\n" + "=" * 55)
    print("           CRM EXTRACTION EVALUATION")
    print("=" * 55)

    print(f"\nTotal input records: {len(merged)}")
    print(f"Successful extractions: {successful_records}")
    print(f"Failed extractions: {failed_records}")
    print(f"API failures: {api_failure_count}")

    # Field accuracy uses only successful extractions.
    print("\nFIELD-BY-FIELD ACCURACY")

    field_metrics = {}

    for field in FIELDS_TO_EVALUATE:

        correct = field_correct_counts[field]

        accuracy = (
            correct / successful_records
        ) * 100

        field_metrics[field] = {
            "correct": correct,
            "total_successful_extractions": successful_records,
            "accuracy_percent": round(accuracy, 2)
        }

        print(
            f"{field}: {correct}/{successful_records} "
            f"({accuracy:.2f}%)"
        )

    # Calculate review classification only for successful records.
    successful_df = details_df[
        details_df["extraction_status"] == "success"
    ]

    true_positive = (
        (successful_df["review_expected"] == True)
        & (successful_df["review_actual"] == True)
    ).sum()

    true_negative = (
        (successful_df["review_expected"] == False)
        & (successful_df["review_actual"] == False)
    ).sum()

    false_positive = (
        (successful_df["review_expected"] == False)
        & (successful_df["review_actual"] == True)
    ).sum()

    false_negative = (
        (successful_df["review_expected"] == True)
        & (successful_df["review_actual"] == False)
    ).sum()

    review_correct = true_positive + true_negative

    review_accuracy = (
        review_correct / successful_records
    ) * 100

    review_metrics = {
        "true_positive": int(true_positive),
        "true_negative": int(true_negative),
        "false_positive": int(false_positive),
        "false_negative": int(false_negative),
        "total_successful_extractions": successful_records,
        "accuracy_percent": round(review_accuracy, 2)
    }

    print("\nHUMAN REVIEW CLASSIFICATION")

    print(
        f"Correct review decisions: "
        f"{review_correct}/{successful_records}"
    )

    print(f"Review accuracy: {review_accuracy:.2f}%")
    print(f"True positives: {true_positive}")
    print(f"True negatives: {true_negative}")
    print(f"False positives: {false_positive}")
    print(f"False negatives: {false_negative}")

    # Display API and extraction failures separately.
    print("\nEXTRACTION FAILURES")

    if failure_details:
        for failure in failure_details:
            print(
                f"{failure['input_id']}: "
                f"{failure['failure_reason']}"
            )
    else:
        print("No extraction failures.")

    # Save evaluation files.
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    details_path = OUTPUT_DIR / "evaluation_details.csv"

    details_df.to_csv(
        details_path,
        index=False
    )

    summary = {
        "total_input_records": len(merged),
        "successful_extractions": successful_records,
        "failed_extractions": failed_records,
        "api_failures": api_failure_count,
        "field_accuracy": field_metrics,
        "review_classification": review_metrics,
        "failure_details": failure_details,
        "note": (
            "Field accuracy and review classification are calculated "
            "only for successful extractions. API failures are reported "
            "separately and are not counted as field extraction errors. "
            "Results measure agreement with supplied ground truth, "
            "not independent proof of extraction quality."
        )
    }

    summary_path = OUTPUT_DIR / "evaluation_summary.json"

    with open(summary_path, "w", encoding="utf-8") as file:
        json.dump(summary, file, indent=4)

    print("\nEvaluation files saved:")
    print("outputs/evaluation_details.csv")
    print("outputs/evaluation_summary.json")


if __name__ == "__main__":
    main()
