<<<<<<< HEAD

=======
>>>>>>> edd003d (Update project README)

# AI-Powered CRM Data Entry Assistant

A Python application that uses Google Gemini to extract CRM information from customer calls, emails and meeting notes. It validates the extracted information using Python business rules and separates accepted updates from records that need human review.

## 1. Problem Statement

Sales teams receive customer information in different formats, including call notes, emails and meeting transcripts. Manually entering this information into a CRM can take time and may lead to missing or inconsistent information.

This project demonstrates how an AI model can help extract structured CRM fields from unstructured customer conversations while using validation rules and human review to reduce the risk of incorrect updates.

## 2. Features

- Extracts company name, contact person, deal stage, next step, next-step date, deal value, currency and notes.
- Uses Google Gemini API for information extraction.
- Uses Pandas to read and write CSV files.
- Uses Pydantic to validate the expected response structure.
- Checks extracted information against evidence from the original conversation.
- Normalises company names before matching them with existing CRM records.
- Applies business rules for deal stages, missing information, currency and deal values.
- Detects certain suspicious instructions in customer messages.
- Retries once when Gemini returns malformed JSON.
- Separates accepted CRM updates from records requiring human review.
- Saves extraction results, evaluation results and execution logs.

## 3. Technology Stack

Python – Main application logic\
Google Gemini API – Information extraction\
Pandas – CSV processing\
Pydantic – Structured response validation\
Pytest – Automated testing\
python-dotenv – Environment variable management

Ollama was also tested during development as an alternative local model, but Google Gemini is the final extraction provider used by the application.

## 4. Project Structure

```
ai-crm-assistant/
│
├── data/
│   ├── sample_inputs.csv
│   ├── existing_crm.csv
│   └── ground_truth.csv
│
├── outputs/
│   ├── updated_crm.csv
│   ├── human_review.csv
│   ├── extraction_results.csv
│   ├── run_log.json
│   ├── evaluation_summary.json
│   └── evaluation_details.csv
│
├── src/
│   ├── main.py
│   ├── ai_extractor.py
│   ├── crm_processor.py
│   ├── validator.py
│   │
│   └── providers/
│       ├── gemini_provider.py
│       └── ollama_provider.py
│
├── tests/
│
├── evaluate.py
├── requirements.txt
├── .env
├── .gitignore
└── README.md
```

The `.env` file contains the API key and must not be committed to GitHub. The `.gitignore` file excludes it from version control.

## 5. Setup Instructions

### Prerequisites

- Python 3.14.7 or a compatible Python version.
- A Google Gemini API key.
- Internet access for Gemini API requests.

### Step 1 – Open the project folder

```
cd path\to\ai-crm-assistant
```

### Step 2 – Create a virtual environment

```
python -m venv .venv
```

Activate it:

```
.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, run:

```
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Then activate the environment again.

### Step 3 – Install dependencies

```
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4 – Configure the Gemini API key

Create a `.env` file in the project root:

```
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-3.6-flash
```

Replace the placeholder with your own API key. Do not share or upload the `.env` file.



## 6. Running the Application

Make sure the virtual environment is activated and the `.env` file is configured.

Run:

```
python -m src.main
```

The application reads the input and existing CRM CSV files, processes the customer conversations and saves the results in the `outputs/` folder.

The current main entry point processes the full input file.

## 7. Understanding the Output Files

`updated_crm.csv` – Existing CRM data with accepted updates applied.

`human_review.csv` – Records that require a person to check before updating.

`extraction_results.csv` – Extracted information returned by the AI model.

`run_log.json` – Execution information, including record and token usage details.

`evaluation_summary.json` – Overall extraction and review-classification metrics.

`evaluation_details.csv` – Field-level comparison between extracted values and expected values.

The application does not directly connect to a live CRM system. It produces CSV files that can be reviewed before any real CRM update is made.

## 8. Evaluation

The project includes `data/ground_truth.csv`, which contains the expected values for the sample records.

The evaluation script compares the extracted results against this file. Ground truth is used only for evaluation; it is not provided to Gemini during extraction.

Run the evaluation after running the application:

```
python evaluate.py
```

The latest recorded evaluation on the 16 sample records was:

| Metric                               | Result |
| ------------------------------------ | ------ |
| Input records                        | 16     |
| Successful extractions               | 16     |
| Failed extractions                   | 0      |
| API failures                         | 0      |
| Company accuracy                     | 81.25% |
| Stage accuracy                       | 56.25% |
| Next-step date accuracy              | 100%   |
| Deal-value accuracy                  | 68.75% |
| Human-review classification accuracy | 18.75% |

These figures measure agreement with the supplied expected values. They are not a guarantee of performance on real customer data.

The review-classification result also indicates that the current rules flag too many records for review and need improvement.

## 9. Running Automated Tests

Run the test suite using:

```
python -m pytest -q
```

The recorded test run passed 62 tests.

The unit tests use mocked model responses for testing application logic. They do not make live Gemini API calls or independently measure live model accuracy.

## 10. Validation and Safety Checks

The application uses several checks before accepting CRM updates:

- Company and contact information is checked against the original conversation.
- Extracted values are checked for supporting evidence.
- Deal-stage progression is checked using predefined rules.
- Won and Lost stages require human review.
- Large deal-value changes are flagged.
- Missing contact information is flagged.
- Unconfirmed budgets are not treated as approved values.
- Currency is not assumed when it is missing.
- Certain suspicious instructions are detected.
- Invalid JSON responses are retried once before being sent for review.

These checks reduce some risks but cannot guarantee that every extraction is correct.

## 11. Known Limitations

- The sample dataset contains only 16 fictional records and is not large enough to establish production-level accuracy.
- Deal-stage extraction needs improvement.
- Company matching and deal-value extraction are not consistently accurate.
- The current review rules flag too many records, creating unnecessary manual work.
- Speaker attribution in meeting transcripts is limited.
- Prompt-injection detection checks for selected phrases and is not comprehensive.
- Relative dates can be difficult to interpret when the conversation is vague.
- The application depends on Gemini API availability, quota and rate limits.
- The application generates CSV outputs; it does not update a live CRM system.

## 12. Possible Improvements

The next improvements should focus on the problems identified during evaluation:

1. Improve deal-stage extraction and validation, especially when a conversation contains changing customer decisions.
2. Improve company matching and deal-value extraction using more varied test examples.
3. Refine human-review rules to reduce unnecessary review flags without allowing uncertain updates.
4. Improve speaker attribution for meeting transcripts.
5. Expand the test dataset and evaluate performance using additional reviewed examples.

## 13. Sample Data and Assumptions

The 16 customer conversations included in `data/sample_inputs.csv` are fictional examples prepared for testing.

The existing CRM data is provided separately in `data/existing_crm.csv`. Expected values are stored in `data/ground_truth.csv` and used by the evaluation script.

The prototype assumes that the input conversations are provided as CSV records and that the existing CRM data is available in the expected CSV format.

No live customer CRM data is used by this demonstration.

## 14. Author

Soham Panjabi

AI-Powered CRM Data Entry Assistant 
