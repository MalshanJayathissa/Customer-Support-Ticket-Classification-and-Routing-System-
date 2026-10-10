# TensorForge 2.0: API Implementation and Integration Guide

## Customer Support Ticket Classification and Routing System

**Purpose:** Implement the API layer that integrates the existing ML pipeline and satisfies the TensorForge 2.0 MVP evaluation requirements.

**Priority:** Correctness, exact schema compliance, robustness, authentication, and reliable processing of batch jobs.

**Important:** This document describes the implementation requirements and recommended architecture. The official competition OpenAPI specification and JSON Schemas are authoritative for every request field, response field, enum, status code, and error format.

---

## 1. Project Overview

The project classifies customer-support tickets and predicts:

1. Primary ticket category.
2. Secondary category, when applicable.
3. Whether the ticket is urgent.

The ML pipeline has already been trained and saved. The API implementation must integrate those saved models rather than retrain them.

The system must expose six required endpoints:

| Method | Endpoint                       | Purpose                                                                            | Authentication |
| ------ | ------------------------------ | ---------------------------------------------------------------------------------- | -------------- |
| POST   | `/predict`                     | Predict one ticket                                                                 | Required       |
| POST   | `/predict/batch`               | Synchronous prediction for 1–100 tickets                                           | Required       |
| POST   | `/batch/jobs`                  | Submit a large asynchronous job containing more than 2,000 and up to 5,000 tickets | Required       |
| GET    | `/batch/jobs/{job_id}`         | Retrieve asynchronous job status                                                   | Required       |
| GET    | `/batch/jobs/{job_id}/results` | Retrieve completed job results                                                     | Required       |
| GET    | `/health`                      | Public health check                                                                | Not required   |

The judges will use automated requests and an API key to evaluate the hosted system. The implementation must not depend on assumptions about the judges' local Python environment or hardware.

## 2. Existing ML Pipeline

### 2.1 Primary classification model

* Model: XLM-RoBERTa Base with class-weighted training.
* Number of primary categories: 11.
* Input: ticket text, using the preprocessing and tokenization implemented in `src/inference/predictor.py`.
* Validation accuracy: 83.63%.
* Validation Macro-F1: 83.65%.
* Validation Weighted-F1: 83.93%.

These are validation results, not independent test-set results.

The primary categories are:

* `account_promo`
* `app_technical`
* `delivery_delay`
* `food_quality`
* `general_inquiry`
* `lost_item`
* `order_missing_wrong`
* `payment_refund`
* `ride_trip_issue`
* `safety_conduct`
* `spam_irrelevant`

The API must use the exact enum values defined in the official specification. Verify that the specification's category vocabulary matches the model labels before returning predictions.

### 2.2 Secondary-category models

Three saved scikit-learn pipelines are available:

* `secondary_presence_classifier.joblib`
* `secondary_category_classifier.joblib`
* `urgency_classifier.joblib`

Their roles are:

1. Predict whether a secondary category exists.
2. If one exists, predict its category.
3. Predict whether the ticket is urgent.

The existing predictor combines the subject, channel, language, and text for these scikit-learn models. The primary transformer model uses ticket text.

Use the existing `predictor.py` implementation instead of rebuilding the feature-processing logic independently in the API.

**Model limitation:** The secondary-category models were trained on a relatively small number of positive examples. Their outputs should be returned according to the official schema, but do not invent a secondary category or add hard-coded primary-to-secondary mappings.

### 2.3 Existing ML interface

The existing file is:

`src/inference/predictor.py`

It exposes `predict_one()` and `predict_batch()`.

Expected internal prediction fields include:

* `ticket_id`
* `category`
* `category_confidence`
* `secondary_category`
* `is_urgent`
* `urgency_score`

These are the current internal predictor fields. They are **not automatically the official API response schema**. Implement an explicit adapter between internal model results and the official API response.

The API must not expose extra fields simply because the ML predictor produces them. Return only the fields required by the official specification.

---

## 3. Responsibilities

### API implementation responsibilities

The API developer must implement:

* All six required endpoints.
* Request and response validation.
* API key authentication.
* Exact response serialization.
* Correct HTTP status codes and error structures.
* Synchronous batch processing.
* Asynchronous job creation, processing, status tracking, and result retrieval.
* Safe model loading and inference integration.
* Job failure handling and input validation.
* Offline-capable Docker packaging.
* Integration tests for the required endpoints.

### ML integration responsibilities

The existing ML pipeline provides:

* The saved primary classification model and tokenizer.
* The three saved scikit-learn pipelines.
* The unified prediction interface.
* Existing feature construction and inference behavior.

Avoid retraining, replacing, or independently preprocessing the models unless a verified defect requires a change.

---

## 4. Official Specification Is the Source of Truth

Before implementing endpoint logic, inspect the official OpenAPI document and associated JSON Schemas.

Record the following for every endpoint:

* Required request fields.
* Optional request fields.
* Field types and nullability.
* Allowed enum values.
* Whether unknown fields are rejected or ignored.
* Required response fields.
* Success status codes.
* Error status codes and exact error structures.
* Authentication header name and format.
* Rules for empty arrays and invalid ticket counts.
* Job status vocabulary and transitions.
* Result pagination or response-size constraints, if specified.

Do not assume that the API key header is named `X-API-Key` unless the official specification says so. Do not invent response envelopes, status strings, error messages, or HTTP status codes.

Create Pydantic request and response models or equivalent validators that follow the official schema exactly. Use the same schemas for tests wherever practical.

If a behavior is not specified, check the full competition documentation before choosing an implementation.

---

## 5. Endpoint Implementation Requirements

### 5.1 POST `/predict`

**Purpose:** Predict one support ticket.

Implementation steps:

1. Authenticate the request.
2. Validate the request against the official single-ticket schema.
3. Pass the ticket to `predict_one()`.
4. Map the internal result to the official response format.
5. Return the correct status code and JSON structure.

Test cases:

* Valid ticket.
* Missing required field.
* Invalid field type.
* Invalid enum value.
* Empty or whitespace-only text, according to the official rules.
* Invalid or missing API key.
* Unexpected internal model error.

Do not add confidence or urgency-score fields to the public response unless the specification explicitly requires them.

### 5.2 POST `/predict/batch`

**Purpose:** Synchronously predict between 1 and 100 tickets.

Implementation requirements:

* Authenticate the request.
* Validate the batch structure.
* Enforce the specified ticket-count limit.
* Preserve the association between each input ticket and its result.
* Process the tickets through the existing ML pipeline.
* Return the exact official batch response.
* Handle malformed tickets according to the specification.
* Avoid reloading the model for every ticket.

The current predictor processes tickets in chunks. Use that functionality where appropriate, but verify memory usage and output ordering.

Test batch sizes of 1, 2, 100, and invalid sizes such as 0 and 101. The exact error status and response body must come from the official specification.

### 5.3 POST `/batch/jobs`

**Purpose:** Submit a large asynchronous evaluation job.

The specified range is more than 2,000 tickets and up to 5,000 tickets per job.

Required workflow:

1. Authenticate the request.
2. Validate the payload and ticket count.
3. Create a unique job identifier.
4. Register the job and its initial status.
5. Enqueue the job for background processing.
6. Return the official job-creation response without waiting for every prediction to finish.
7. Process the tickets in manageable chunks.
8. Persist the results and update the job status.

Do not process a large job entirely inside the request handler if doing so prevents the endpoint from returning the required asynchronous response.

The specification describes an apparent gap between the synchronous range of 1–100 tickets and the asynchronous range of more than 2,000 tickets. Do not invent behavior for 101–2,000 tickets. Follow any additional rules in the full official documentation, and otherwise avoid assuming an undocumented policy.

#### Recommended job states

Use the exact state values defined by the official specification. Internally, a job lifecycle will typically need to distinguish:

* Queued.
* Running.
* Completed.
* Failed.

These are conceptual states, not guaranteed official enum strings.

A job should not be marked completed until its results have been persisted successfully. If processing fails, record the failure and ensure the status endpoint can report it according to the official error and job-status schemas.

#### Job storage

For a single-process MVP, a carefully managed in-memory job registry may be sufficient for basic development tests, but it is fragile because jobs and results disappear on restart.

Prefer persistent job/result storage if the deployment environment and deadline allow it. If using a database or file-backed store, ensure that job identifiers are unique and results remain associated with the correct job.

If the API uses multiple workers or replicas, do not rely on a process-local dictionary as the only job store. Different workers may not share it.

### 5.4 GET `/batch/jobs/{job_id}`

**Purpose:** Retrieve a job's current status.

Implementation requirements:

* Authenticate the request.
* Validate and look up the job identifier.
* Return the exact official job-status schema.
* Reflect the actual lifecycle state.
* Handle unknown job identifiers using the documented error response.
* Report processing failures consistently.

Do not report a job as completed simply because the background task was submitted. Completion must reflect successful processing and result persistence.

### 5.5 GET `/batch/jobs/{job_id}/results`

**Purpose:** Retrieve the results of a submitted job.

Implementation requirements:

* Authenticate the request.
* Verify that the job exists.
* Determine whether results are available.
* Return results in the exact official schema.
* Handle requests made before completion according to the specification.
* Handle failed jobs and unknown job identifiers correctly.
* Preserve input-to-output correspondence and result ordering if required.

Do not guess whether incomplete jobs should return an error, a pending response, or partial results. Use the official documentation.

### 5.6 GET `/health`

**Purpose:** Public health check.

Requirements:

* No API key required.
* Return the documented response schema and status code.
* Avoid exposing secrets, stack traces, internal filesystem paths, or sensitive configuration.

If the specification distinguishes basic process health from model readiness, implement that distinction. Otherwise, do not invent additional response fields.

---

## 6. Authentication and Security

All prediction and job endpoints must require the official API key authorization mechanism. `/health` must remain public.

Implementation requirements:

* Read the expected API key from an environment variable or deployment secret.
* Never hard-code the real key in source code.
* Never commit the key to Git.
* Never return the key in a response or log.
* Reject missing or invalid keys using the documented status code and error format.
* Apply authentication consistently to all five protected endpoints.
* Ensure error responses do not reveal secrets or sensitive internal details.

For local testing, use a dummy development key. The evaluation key should be injected through the deployment environment.

Example configuration:

```env
# Use a local placeholder for development only.
API_KEY=replace_with_local_development_key
```

Do not commit a populated secret file. Configure the actual key in the hosting environment or through the permitted Docker runtime configuration.

---

## 7. ML Integration

### 7.1 Load the models once

Instantiate the prediction pipeline during application startup or in a controlled lazy-loading mechanism.

Do not load XLM-RoBERTa or deserialize the scikit-learn pipelines on every HTTP request.

At startup:

1. Resolve the model paths.
2. Load the tokenizer and transformer from local files.
3. Load all three scikit-learn pipelines.
4. Put the transformer in evaluation mode.
5. Select CPU or GPU based on availability.
6. Fail clearly if a required model artifact is missing.

### 7.2 Model paths

The handoff archive currently uses the folder name:

`xlmr_primary_weighted_final/`

The existing predictor expects the primary model under:

`models/xlmr_primary_weighted/final/`

Make sure the files are extracted into the expected directory, or configure the predictor to use the extracted path. Do not leave this mismatch unresolved.

Expected model layout:

```text
models/
├── xlmr_primary_weighted/
│   └── final/
│       ├── config.json
│       ├── model.safetensors
│       ├── tokenizer.json
│       ├── tokenizer_config.json
│       └── training_args.bin
├── secondary_presence_classifier.joblib
├── secondary_category_classifier.joblib
└── urgency_classifier.joblib
```

The supplied handoff archive is intended to contain the required inference artifacts. Verify all files exist and load correctly after extraction.

### 7.3 CPU-only inference

A GPU is not required. PyTorch can execute the transformer on CPU.

The deployment must have enough RAM for the transformer, tokenizer, Python runtime, libraries, and inference tensors. Begin with small transformer batches and increase the size only after verifying memory use.

The evaluation does not score latency, so prioritize correctness and stability over aggressive concurrency or batching.

### 7.4 Local-only model loading

Load the transformer with local-only settings so missing files do not trigger an internet download attempt.

The model artifacts alone are not a complete executable environment. The image must include compatible versions of PyTorch, Transformers, scikit-learn, joblib, and the other required dependencies.

Do not use an online inference API or depend on downloading a model during evaluation.

---

## 8. Offline Docker Deployment

The final Docker image must contain everything needed to run inference without internet access at runtime.

Include:

* API source code.
* Python runtime.
* Compatible dependency versions.
* XLM-RoBERTa weights, configuration, and tokenizer.
* The three scikit-learn model files.
* Any runtime configuration that is safe to include.
* The correct startup command.

Do not include:

* Training datasets unless explicitly needed at runtime.
* Optimizer checkpoints.
* Unnecessary training checkpoints.
* Virtual environments copied from the developer's computer.
* Real API keys or other secrets.

### Docker verification

Build the image before evaluation. Then run it with networking disabled and provide the required API key through the allowed runtime configuration.

Verify that:

1. The application starts successfully.
2. All model files load without downloading anything.
3. `/health` works without authentication.
4. Authenticated prediction requests work.
5. Invalid API keys are rejected.
6. Synchronous batches work.
7. Asynchronous jobs can be submitted, processed, polled, and retrieved.
8. Missing model files or configuration produce clear startup failures.
9. The container uses the correct port and deployment settings.

Use the port and startup behavior required by the competition platform.

---

## 9. Error Handling and Robustness

The judges' tests are automated. Small schema differences can cause failures even when the predictions themselves are correct.

Validate and handle:

* Missing required fields.
* Invalid field types.
* Invalid category or channel enums.
* Invalid ticket counts.
* Empty or malformed payloads.
* Missing and invalid API keys.
* Unknown job identifiers.
* Job requests made before results are ready.
* Background processing failures.
* Missing model files.
* Unexpected inference exceptions.

For every case, follow the official error schema, status code, and response format. Do not return an arbitrary dictionary or a successful HTTP response containing an error message when the specification requires a proper error status.

Log diagnostic information without logging API keys or unnecessarily recording full customer-support text.

---

## 10. Testing Plan

Test the system from the perspective of an automated judge, not just through the interactive API documentation page.

### Single-ticket tests

* Valid ticket with ordinary text.
* Ticket with a missing subject if allowed.
* Sinhala, Tamil, Singlish, Tanglish, and mixed-language examples.
* Urgent ticket.
* Ticket with no secondary category.
* Invalid payload.
* Missing and incorrect API key.

### Synchronous batch tests

* 1 ticket.
* 2 tickets.
* 100 tickets.
* Empty batch.
* 101 tickets.
* Malformed ticket inside a batch.
* Repeated ticket identifiers if the specification permits them.

### Asynchronous batch tests

* 2,001 tickets.
* 3,000 tickets.
* 5,000 tickets.
* Invalid size above 5,000.
* Job status immediately after submission.
* Job status while processing.
* Results after completion.
* Results before completion.
* Unknown job identifier.
* Background job failure.
* Correct association between each input ticket and its output.

Test the precise boundary conditions specified by the official documentation. Do not assume that 101–2,000 tickets are valid for either batch endpoint.

### Authentication tests

* `/health` without a key.
* Each protected endpoint without a key.
* Each protected endpoint with an invalid key.
* Each protected endpoint with a valid key.

### Schema tests

For every endpoint, compare actual responses against the official schemas. Verify required fields, optional fields, null values, enums, status codes, and error structures.

### Docker tests

* Clean image build.
* Startup with model artifacts present.
* Startup with networking disabled.
* Prediction without internet access.
* Model-loading failure when a required artifact is absent.
* Full API smoke test inside the container.

---

## 11. Suggested Implementation Order

To reduce integration risk, implement in this order:

1. Read the official OpenAPI and JSON Schema definitions.
2. Set up the API project and configuration.
3. Load the saved models through `src/inference/predictor.py`.
4. Implement and test `/health`.
5. Implement authentication middleware or a reusable dependency.
6. Implement `/predict`.
7. Implement `/predict/batch`.
8. Implement job creation and background processing.
9. Implement job-status and job-results retrieval.
10. Add exact error handling and response validation.
11. Build the Docker image with all model artifacts.
12. Run the complete test suite, including offline tests.
13. Deploy the API and verify the hosted endpoints using the competition's evaluation configuration.

If time is limited, prioritize schema correctness and end-to-end functionality before optional optimizations.

---

## 12. Definition of Done

The API is ready for evaluation only when all of the following are verified:

* [ ] All six endpoints exist at the required paths and methods.
* [ ] `/health` is public.
* [ ] All prediction and job endpoints require valid API-key authorization.
* [ ] `/predict` matches the official request and response schemas.
* [ ] `/predict/batch` supports 1–100 tickets and enforces the documented limits.
* [ ] `/batch/jobs` correctly accepts valid large jobs of more than 2,000 and up to 5,000 tickets.
* [ ] Job status and result endpoints work correctly.
* [ ] Invalid inputs, invalid keys, unknown jobs, and processing failures follow the official error specification.
* [ ] The saved models load correctly from the expected paths.
* [ ] The API does not retrain the models or depend on online model downloads.
* [ ] The final Docker image contains all necessary artifacts and dependencies.
* [ ] The container works without internet access at runtime.
* [ ] End-to-end tests pass using the actual API request and response schemas.
* [ ] The hosted API is reachable and configured for the judges' evaluation.

## 13. Final Notes

The ML pipeline is already implemented. Your task is to make it accessible through a reliable, authenticated API that follows the official specification exactly.

Do not spend time retraining or replacing the models unless a verified issue requires it. The evaluation prioritizes correctness, schema compliance, and robustness rather than raw inference latency.

**Most important:** Obtain the official OpenAPI/JSON Schema document before finalizing endpoint behavior. This guide describes the work to implement, but it does not replace the official contract.

The completed system must run as a self-contained deployment, including the saved models and dependencies, and must not rely on the judges' computers having a GPU or an installed ML environment.
