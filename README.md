# AI-Powered CRM Data Entry Assistant

A Python-based prototype that uses the Gemini API to extract structured CRM information from sales conversations and identify records that require human review.

## 1. Problem Statement

Sales teams receive information through calls, emails and meeting notes. Manually entering company details, contact information, deal stages, follow-up dates and deal values into a CRM can be repetitive and error-prone.

This project aims to reduce manual data entry while ensuring uncertain updates are checked by a human.

## 2. Solution

The application:
1. Reads sales conversations from a CSV file.
2. Uses Gemini to extract relevant CRM information.
3. Validates the response using Python and Pydantic.
4. Checks extracted information against selected source evidence and business rules.
5. Updates matching CRM records when the required checks pass.
6. Sends uncertain records to a separate human-review CSV.

The prototype uses CSV files rather than connecting directly to a live CRM.

## 3. Technology Stack

- Python
- Gemini API (`google-genai`)
- Pandas
- Pydantic
- python-dotenv
- Pytest

## 4. Project Structure

```text
ai-crm-assistant/
├── data/
│   ├── sample_inputs.csv
│   ├── existing_crm.csv
│   └── ground_truth.csv
├── outputs/
│   ├── updated_crm.csv
│   ├── human_review.csv
│   ├── extraction_results.csv
│   ├── run_log.json
│   ├── evaluation_details.csv
│   └── evaluation_summary.json
├── src/
│   ├── main.py
│   ├── ai_extractor.py
│   ├── crm_processor.py
│   ├── validator.py
│   └── providers/
├── tests/
├── evaluate.py
├── requirements.txt
└── README.md
```

## 5. Setup

Create and activate a virtual environment:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-3.6-flash
```

Keep your API key private and do not commit `.env` to GitHub.

## 6. Run the Application

```powershell
python -m src.main
```

The application processes the records in `data/sample_inputs.csv`.

### Generated Outputs

| File | Purpose |
|---|---|
| `updated_crm.csv` | Existing CRM records with eligible updates |
| `human_review.csv` | Records requiring manual review |
| `extraction_results.csv` | Extracted information and review decisions |
| `run_log.json` | Processing and token-usage information |

## 7. Testing and Evaluation

Run the automated tests:

```powershell
python -m pytest -v
```

Latest recorded test result: **62 tests passed**.

Run the evaluation:

```powershell
python evaluate.py
```

### Latest Recorded Evaluation

The prototype was tested against 16 manually labelled sample conversations.

| Metric | Result |
|---|---:|
| Successful extractions | 16/16 |
| Company accuracy | 100% |
| Stage accuracy | 81.25% |
| Next-step-date accuracy | 93.75% |
| Deal-value accuracy | 100% |
| Human-review classification | 100% |

Three records were automatically applied to the existing CRM, while 13 were sent for human review.

These results measure agreement with the supplied ground truth on a small fictional dataset. They should not be treated as proof of production-level accuracy.

## 8. Important Safeguards

- Validates the Gemini response using Pydantic.
- Checks supporting evidence for selected extracted fields.
- Normalizes company names before matching.
- Flags explicitly unconfirmed budgets.
- Checks currency and deal-value changes.
- Sends uncertain or risky updates for human review.

## 9. Limitations

- Uses CSV files; no live CRM integration.
- Requires Gemini API access and available quota.
- Selected extracted fields are evidence-checked, not every field.
- Company matching uses normalization and exact matching, not fuzzy matching.
- The evaluation dataset is small and fictional.
- Human review is still necessary for uncertain updates.

## 10. Future Improvements

- Build a simple **Streamlit interface** to upload sales conversations, run extraction and review results.
- Expand testing with more varied sales conversations.
- Improve extraction accuracy and human-review handling.
- Explore integration with a CRM sandbox.

## 11. Sample Data

All included sample conversations and CRM records are fictional and created for testing.

## Author

**Soham Panjabi**

GitHub: https://github.com/sohampan24
