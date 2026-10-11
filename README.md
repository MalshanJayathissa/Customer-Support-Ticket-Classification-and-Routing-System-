# Customer Support Ticket Classification and Routing System

**TensorForge 2.0 — Phase 2**

An end-to-end machine learning system that classifies customer support tickets, predicts urgency, and automatically routes requests to appropriate support teams.

## Technology Stack

- **Frontend:** React, Vite, Recharts
- **Backend:** Python, FastAPI, Pydantic
- **Primary ML Model:** XLM-RoBERTa
- **Additional Models:** Secondary-category and urgency classifiers
- **Asynchronous Processing:** Background workers with SQLite job tracking
- **Containerization:** Docker

## Features

- Single-ticket classification and automated routing
- Synchronous batch predictions for 1–100 tickets
- Asynchronous batch processing for large evaluation datasets
- Job status polling and paginated results
- API-key authentication
- Interactive frontend dashboard
- CSV upload and prediction-result export

## Project Structure

```text
backend/
  app/
  models/
  Dockerfile
  requirements.txt

frontend/
  src/
  package.json
  vite.config.js
```

## Run the Backend

The trained model artifacts must be placed in `backend/models/` before starting the application.

```powershell
cd backend
pip install -r requirements.txt
$env:API_KEY="local-test-key"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/docs` for interactive API documentation.

## Run the Frontend

```powershell
cd frontend
npm install
$env:API_KEY="local-test-key"
npm run dev
```

Open `http://localhost:5173`.

For local development, the Vite proxy forwards API requests to FastAPI.

## API Endpoints

| Endpoint | Purpose |
|---|---|
| `GET /health` | Public health check |
| `POST /predict` | Single-ticket prediction |
| `POST /predict/batch` | Synchronous batch prediction |
| `POST /batch/jobs` | Submit an asynchronous job |
| `GET /batch/jobs/{job_id}` | Retrieve job status |
| `GET /batch/jobs/{job_id}/results` | Retrieve paginated results |

Protected endpoints require a valid API key configured through the `API_KEY` environment variable.

## Docker

From the `backend` directory:

```powershell
docker build -t tensorforge-api:latest .
docker run -p 8000:8000 -e API_KEY=local-test-key tensorforge-api:latest
```

The Docker image must contain the trained models and all inference dependencies.

## Model Artifacts

Trained model weights are excluded from Git because of their size. They must be provided separately and extracted into `backend/models/` before local execution or Docker builds.

**Model artifact download:** Add your team's verified artifact download link here.

## Verification

Local verification has included successful single-ticket predictions, a 100-ticket synchronous batch, a 3,000-ticket asynchronous batch, and 13 passing authorization test cases.

These tests establish local functionality; they do not replace complete validation against the organizer's official OpenAPI and JSON Schemas.

## Security

Do not commit `.env` files, API keys, local SQLite data, or sensitive customer-support data.

The API key must be supplied through an environment variable or deployment secret.
Api key is secretly kept inside a env file and use it through key pass.
use API key and command to run the docker

## License and Acknowledgments

Developed as a three-member team project for TensorForge 2.0 Phase 2.
