**AI-Powered CRM Data Entry Assistant**

Assignment: Pick One, Prove It – Option A: CRM Data Entry\
Submitted by: Soham Panjabi\
Submitted on: 9 November 2026\

1. Introduction and Problem

Sales teams receive customer information through calls, emails and meetings. Important details such as company names, contact persons, deal stages, follow-up dates and budgets are often recorded in unstructured notes.

Entering this information into a CRM manually takes time. It can also lead to missing details, inconsistent company names and incorrect updates.

I built an AI-powered CRM Data Entry Assistant to help reduce this manual effort. The application reads customer conversations from a CSV file, extracts relevant CRM information using Google Gemini, and checks the extracted details before deciding whether they can be used to update the existing CRM data.

I selected Option A because it addresses a practical business problem and allowed me to demonstrate how AI can work alongside Python validation and human review.

2. What I Built

The application takes customer notes, emails and meeting transcripts as input and attempts to extract the following information:

- Company name
- Contact person
- Deal stage
- Next step
- Next-step date
- Deal value and currency
- Additional notes

It then checks the extracted information against the original conversation and applies business rules.

If the information passes the checks, the application can update the matching CRM record. If information is missing, uncertain or fails a business rule, the record is sent for human review instead.

The project uses 16 fictional sample customer records prepared for testing. They cover situations such as abbreviated notes, inconsistent company names, missing information, multiple speakers, changing customer decisions, unconfirmed budgets, different currencies and suspicious instructions within a message.

3. How the Application Works

The application follows five main steps.

Step 1 – Read the input

Python and Pandas read the customer conversations from data/sample_inputs.csv. The existing CRM records are loaded from data/existing_crm.csv.

Step 2 – Extract information using Gemini

The application sends each conversation to Google Gemini through its API. Gemini identifies the relevant CRM fields and returns the information in a structured JSON format.

Step 3 – Validate the response

Pydantic checks whether the response follows the expected structure and data types. Python validation functions check the extracted values against the original conversation and apply business rules.

For example, the application checks whether company and contact details are supported by the conversation, whether the deal stage is reasonable, and whether the currency has been explicitly mentioned.

Step 4 – Decide whether to update or review

The application checks whether the extracted information is suitable for an automatic update. Records that fail validation or trigger review rules are not automatically applied.

Step 5 – Save the results

The application saves the updated CRM data, records requiring human review, extraction results and execution logs in the outputs folder.

The complete workflow can be started using:

python -m src.main

4. What AI Handles and What Python Handles

I have kept the responsibilities separate rather than relying on AI for every decision.

Google Gemini: Understands unstructured conversations and extracts CRM fields.

Python: Processes records, matches companies and applies business rules.

Pandas: Reads and writes CSV files and manages tabular data.

Pydantic: Checks whether the AI response follows the expected structure.

Human reviewer: Checks records when information is incomplete, conflicting or uncertain.

This separation is important because an AI-generated response should not automatically be treated as correct CRM information.

5. Handling Difficult Inputs

I included different types of customer conversations to test how the application handles incomplete or difficult information.

Inconsistent company names: Normalises company names before matching, including differences in punctuation and common suffixes.

Missing information: Flags records when required information, such as a contact person, is missing.

Abbreviated notes: Uses Gemini to interpret short forms and extract the intended information.

Multiple speakers: Extracts information from meeting transcripts, although speaker attribution may still need human checking.

Changing customer decisions: Applies stage checks and review rules where a stage change may be unsafe.

Unconfirmed budget: Does not treat an explicitly unconfirmed amount as an approved deal value.

Different currencies: Checks whether the currency is stated rather than assuming that every amount is INR.

Suspicious instructions: Checks for certain prompt-injection phrases and flags suspicious records.

Invalid model response: Attempts one retry when the response is malformed and sends the record for review if it remains invalid.

These checks reduce some risks, but they do not guarantee that every extracted value will be correct.

6. Testing and Evaluation

I tested the application using 16 sample customer records. I also created a separate ground_truth.csv file containing the expected values for evaluation.

The evaluation script compares the extracted results against these expected values. The ground-truth file is used for testing and evaluation; it is not used by Gemini to extract information.

The latest evaluation produced the following results:

Field or check                  Correct results       Accuracy

Company name                    13 out of 16          81.25%\
Deal stage                      9 out of 16           56.25%\
Next-step date                  16 out of 16          100%\
Deal value                      11 out of 16          68.75%\
Human-review classification     3 out of 16           18.75%

All 16 records were processed successfully, with zero failed extractions and zero API failures.

The human-review classification results were 0 true positives, 3 true negatives, 13 false positives and 0 false negatives. This means the application flagged 13 records for review even though the expected classification did not require review for those records. The result is therefore too cautious and could create additional work for the sales team.

Deal-stage extraction also needs improvement, with an accuracy of 56.25%. Company-name matching and deal-value extraction need further refinement. Next-step date extraction performed best in this test, achieving 100% accuracy.

These results measure agreement with the expected values in the supplied test dataset. They do not independently prove that every extracted value is correct in real-world situations.

I also created automated tests for the extraction, validation and business-rule logic. The test suite passed 62 tests in the test run. The model responses in these unit tests were mocked, so this result verifies the application logic rather than the live Gemini service.

7. Risks and Safeguards

The biggest risk is an incorrect deal stage or deal value being written to the CRM. For example, incorrectly marking a deal as Won could give the sales team a misleading view of its pipeline.

I added safeguards to reduce this risk:

- Extracted values are checked against evidence from the original conversation.
- Deal stages are checked using predefined patterns and progression rules.
- Won and Lost stages require human review.
- Large changes in deal value are flagged.
- Missing contact details and unconfirmed budgets are flagged.
- Currency is not assumed when it is not explicitly stated.
- Certain suspicious instructions in customer messages are detected.
- Malformed model responses are retried once before being sent for review.

The current safeguards have limitations. For example, stage validation relies partly on predefined patterns and does not fully understand who said each statement in a meeting transcript. Speaker attribution and complex conversations therefore still need human verification.

The evaluation also shows that the current review logic flags too many records. This needs to be improved before the application is used with a real CRM.

8. Estimated Cost for 300 CRM Updates per Month

I used the token usage recorded during a 16-record application run to estimate the cost of processing 300 records.

The recorded usage for that run was:

Input tokens: 19,155\
Output tokens: 2,946\
Total tokens: 22,101\
Records processed: 16

Assuming a similar average token usage per record, processing 300 records would require approximately:

Input tokens: 359,156\
Output tokens: 55,238\
Total tokens: 414,394

Using the Gemini 3.6 Flash pricing listed for requests through 31 December 2026, the estimated model cost is approximately $0.48 per month. At the listed pricing from 1 January 2027, the estimate is approximately $0.95 per month.

These are estimates based on the recorded token usage and published API rates. Actual costs may vary depending on conversation length, retries and model usage.

The project also has a 14-second request interval, so processing 300 records sequentially could take around 70 minutes, excluding generation time and retries.

Pricing reference:\
[https://ai.google.dev/gemini-api/docs/pricing](https://ai.google.dev/gemini-api/docs/pricing)

9. What I Would Not Automate

I would not allow the application to make final decisions about whether a deal is Won or Lost, approve a customer's budget, change a deal value based on assumptions or resolve conflicting statements without human confirmation.

These decisions can affect sales forecasts, customer relationships and business reporting. The application should assist sales employees with data entry, not replace their judgement.

10. Limitations and Improvements

The prototype demonstrates the complete extraction and validation workflow, but the evaluation shows that there is room for improvement.

The current test dataset contains only 16 records. A larger and more varied dataset would help identify additional extraction problems.

My first priority would be to improve deal-stage extraction, company matching and deal-value accuracy. I would also refine the human-review rules so that records are flagged for the right reasons without sending too many unnecessary cases for review.

Speaker attribution in meeting transcripts needs stronger validation. The current stage checks rely partly on predefined patterns, so more context-aware checks would also be useful.

During development, I experienced Gemini API quota and temporary service errors. I added request delays and retries to make processing more reliable. The application still depends on the availability and usage limits of the external API.

Before using this application with a real CRM, I would test it on a larger set of reviewed conversations and measure its accuracy again.

11. Conclusion

This project helped me understand how an AI model can be combined with Python, data validation and business rules to solve a practical business problem.

The application can extract useful information from customer conversations and prepare it for CRM entry. At the same time, the evaluation shows that extraction accuracy and review decisions need further improvement.

My objective was to build a working assistant that demonstrates how AI can reduce repetitive data entry while keeping important business updates under human control.

Tools and Libraries Used

Python 3.14.7\
Google Gemini API\
Pandas\
Pydantic\
Pytest\
python-dotenv\
Ollama – tested as an alternative local model during development, but not used as the final extraction provider.\
Git and GitHub – [add repository link if applicable]\
ChatGPT and Claude – used for development guidance and documentation assistance.

Submission contents: Python source code, sample input data, existing CRM data, expected evaluation data, generated output files, automated tests, README instructions, written documentation and video link.

## 2. README.md – paste into your project

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

The model name can be changed through the environment variable if a different supported model is required.

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
