
import pytest
from pydantic import ValidationError

from src.validator import validate_extraction


def valid_sample():
    return {
        "company": "ABC Limited",
        "contact": "Rahul",
        "stage": "Qualified",
        "next_step": "Arrange product demo",
        "next_step_date": None,
        "deal_value": 300000,
        "currency": "INR",
        "notes": "Customer interested in enterprise package",
        "needs_review": False,
        "review_reasons": [],
        "evidence": {
            "company": "ABC Limited",
            "contact": "Rahul",
            "stage": "Qualified",
            "next_step_date": None,
            "deal_value": "300000"
        }
    }


def test_valid_crm_data():
    sample = valid_sample()

    result = validate_extraction(sample)

    assert result.company == "ABC Limited"
    assert result.contact == "Rahul"
    assert result.stage == "Qualified"
    assert result.deal_value == 300000
    assert result.currency == "INR"


def test_negative_deal_value_is_rejected():
    sample = valid_sample()
    sample["deal_value"] = -5000

    with pytest.raises(ValidationError):
        validate_extraction(sample)


def test_invalid_stage_is_rejected():
    sample = valid_sample()
    sample["stage"] = "Interested"

    with pytest.raises(ValidationError):
        validate_extraction(sample)


def test_missing_evidence_is_rejected():
    sample = valid_sample()
    del sample["evidence"]

    with pytest.raises(ValidationError):
        validate_extraction(sample)


def test_unexpected_field_is_rejected():
    sample = valid_sample()
    sample["unexpected_field"] = "not allowed"

    with pytest.raises(ValidationError):
        validate_extraction(sample)


def test_currency_can_be_null():
    sample = valid_sample()
    sample["currency"] = None

    result = validate_extraction(sample)

    assert result.currency is None
