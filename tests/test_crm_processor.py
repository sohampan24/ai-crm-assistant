
from src.crm_processor import (
    normalize_company,
    check_business_rules,
)


def make_crm_row(
    stage="New",
    deal_value="500000",
    contact="Rahul"
):
    return {
        "company": "ABC Limited",
        "contact": contact,
        "stage": stage,
        "deal_value": deal_value,
    }


def make_extracted_data(
    stage="Qualified",
    deal_value=500000,
    currency="INR",
    contact="Rahul"
):
    return {
        "company": "ABC Limited",
        "contact": contact,
        "stage": stage,
        "deal_value": deal_value,
        "currency": currency,
    }


# Company normalization tests

def test_normalize_company_removes_multiple_suffixes():
    assert normalize_company(
        "Acme Tools Pvt. Ltd."
    ) == "acme tools"


def test_normalize_company_matches_ltd_and_limited():
    assert normalize_company("ABC Ltd") == normalize_company(
        "ABC Limited"
    )


def test_normalize_company_joins_initials():
    assert normalize_company(
        "A.B.C. Limited"
    ) == "abc"


def test_normalize_company_does_not_remove_unrelated_word_ending():
    assert normalize_company("Unlimited Inc") == "unlimited"


def test_normalize_company_handles_empty_values():
    assert normalize_company("") == ""
    assert normalize_company(None) == ""


# Stage progression tests

def test_forward_stage_change_is_allowed():
    reasons = []

    result = check_business_rules(
        make_extracted_data(stage="Proposal"),
        make_crm_row(stage="Qualified"),
        reasons
    )

    assert result is False
    assert reasons == []


def test_backward_stage_change_requires_review():
    reasons = []

    result = check_business_rules(
        make_extracted_data(stage="Qualified"),
        make_crm_row(stage="Negotiation"),
        reasons
    )

    assert result is True
    assert "Stage moves backwards" in reasons


def test_won_stage_requires_human_review():
    reasons = []

    result = check_business_rules(
        make_extracted_data(stage="Won"),
        make_crm_row(stage="Negotiation"),
        reasons
    )

    assert result is True
    assert "Closing a deal requires human confirmation" in reasons


def test_lost_stage_requires_human_review():
    reasons = []

    result = check_business_rules(
        make_extracted_data(stage="Lost"),
        make_crm_row(stage="Negotiation"),
        reasons
    )

    assert result is True
    assert "Closing a deal requires human confirmation" in reasons


# Deal value tests

def test_deal_value_change_above_50_percent_requires_review():
    reasons = []

    result = check_business_rules(
        make_extracted_data(deal_value=800000),
        make_crm_row(deal_value="500000"),
        reasons
    )

    assert result is True
    assert "Deal value changed by more than 50%." in reasons


def test_deal_value_change_below_50_percent_is_allowed():
    reasons = []

    result = check_business_rules(
        make_extracted_data(deal_value=600000),
        make_crm_row(deal_value="500000"),
        reasons
    )

    assert result is False
    assert reasons == []


def test_deal_value_change_exactly_50_percent_is_allowed():
    reasons = []

    result = check_business_rules(
        make_extracted_data(deal_value=750000),
        make_crm_row(deal_value="500000"),
        reasons
    )

    assert result is False
    assert reasons == []


def test_deal_value_change_from_zero_requires_review():
    reasons = []

    result = check_business_rules(
        make_extracted_data(deal_value=100000),
        make_crm_row(deal_value="0"),
        reasons
    )

    assert result is True
    assert any(
        "changed from zero" in reason
        for reason in reasons
    )


# Contact and currency tests

def test_missing_contact_requires_review():
    reasons = []

    result = check_business_rules(
        make_extracted_data(contact=None),
        make_crm_row(),
        reasons
    )

    assert result is True
    assert "Contact name is missing." in reasons


def test_non_inr_currency_requires_review():
    reasons = []

    result = check_business_rules(
        make_extracted_data(currency="USD"),
        make_crm_row(),
        reasons
    )

    assert result is True
    assert any(
        "not INR" in reason
        for reason in reasons
    )


def test_missing_currency_with_deal_value_requires_review():
    reasons = []

    result = check_business_rules(
        make_extracted_data(currency=None),
        make_crm_row(),
        reasons
    )

    assert result is True
    assert "Deal currency is missing or unclear." in reasons
def test_missing_deal_value_and_currency_does_not_require_currency_review():
    reasons = []

    result = check_business_rules(
        make_extracted_data(
            deal_value=None,
            currency=None
        ),
        make_crm_row(),
        reasons
    )

    assert result is False
    assert reasons == []


def test_non_inr_currency_without_deal_value_does_not_require_currency_review():
    reasons = []

    result = check_business_rules(
        make_extracted_data(
            deal_value=None,
            currency="USD"
        ),
        make_crm_row(),
        reasons
    )

    assert result is False
    assert reasons == []

def test_unconfirmed_budget_requires_human_review():
    reasons = []

    result = check_business_rules(
        make_extracted_data(
            contact="Priya",
            stage=None,
            deal_value=None,
            currency=None
        ),
        make_crm_row(),
        reasons,
        source_text=(
            "Priya from Bright Solutions. "
            "Budget not confirmed. "
            "Asked for a demo."
        )
    )

    assert result is True
    assert "Deal budget is explicitly unconfirmed." in reasons


def test_approved_budget_does_not_trigger_unconfirmed_budget_rule():
    reasons = []

    result = check_business_rules(
        make_extracted_data(
            contact="Rahul",
            stage=None,
            deal_value=300000,
            currency="INR"
        ),
        make_crm_row(),
        reasons,
        source_text=(
            "Rahul from ABC Pvt Ltd. "
            "Our approved budget is Rs. 3 lakh."
        )
    )

    assert result is False
    assert "Deal budget is explicitly unconfirmed." not in reasons