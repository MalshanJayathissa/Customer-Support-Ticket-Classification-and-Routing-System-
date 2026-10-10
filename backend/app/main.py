
from fastapi import FastAPI, Header, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.auth import verify_api_key_headers
from app.schemas.requests import (
    BatchJobRequest,
    BatchRequest,
    PredictRequest,
)
from app.schemas.responses import (
    BatchJobResultsResponse,
    BatchJobStatusResponse,
    BatchResponse,
    HealthResponse,
    PredictResponse,
)
from app.services.inference import InferenceService
from app.services.job_manager import job_manager
from app.services.job_worker import JobWorker


app = FastAPI(
    title="TensorForge Customer Support Ticket Classification API",
    version="2.1.0",
)


# ============================================================
# Constants
# ============================================================

SYNC_BATCH_MAX_BYTES = 5 * 1024 * 1024
ASYNC_BATCH_MAX_BYTES = 25 * 1024 * 1024


# ============================================================
# Swagger authentication configuration
# ============================================================

def custom_openapi():
    # Reuse the generated schema after the first request.
    if app.openapi_schema:
        return app.openapi_schema

    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    # Register the API key as an HTTP header in Swagger.
    schema.setdefault("components", {}).setdefault(
        "securitySchemes", {}
    )["APIKeyHeader"] = {
        "type": "apiKey",
        "in": "header",
        "name": "X-API-Key",
        "description": "Enter the API key configured in your backend .env file.",
    }

    # Require authentication only for protected endpoints.
    protected_operations = {
        ("/predict", "post"),
        ("/predict/batch", "post"),
        ("/batch/jobs", "post"),
        ("/batch/jobs/{job_id}", "get"),
        ("/batch/jobs/{job_id}", "delete"),
        ("/batch/jobs/{job_id}/results", "get"),
    }

    for path, method in protected_operations:
        operation = schema.get("paths", {}).get(path, {}).get(method)

        if operation is not None:
            operation["security"] = [{"APIKeyHeader": []}]

    app.openapi_schema = schema
    return app.openapi_schema


app.openapi = custom_openapi


# ============================================================
# Services
# ============================================================

# Load one model instance and share it with the background worker.
inference_service = InferenceService()
job_worker = JobWorker(inference_service)


# ============================================================
# JSON error response
# ============================================================

def error_response(
    status_code: int,
    code: str,
    message: str,
    *,
    index: int | None = None,
    field: str | None = None,
    issue: str | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    body = {
        "error": {
            "code": code,
            "message": message,
        }
    }

    details = {}

    if index is not None:
        details["index"] = index

    if field is not None:
        details["field"] = field

    if issue is not None:
        details["issue"] = issue

    if details:
        body["error"]["details"] = details

    return JSONResponse(
        status_code=status_code,
        content=body,
        headers=headers,
    )


# ============================================================
# Protected routes
# ============================================================

def is_protected_path(path: str) -> bool:
    return (
        path == "/predict"
        or path == "/predict/batch"
        or path == "/batch/jobs"
        or path.startswith("/batch/jobs/")
    )


# ============================================================
# Request content length
# ============================================================

def get_content_length(request: Request) -> int:
    value = request.headers.get("content-length")

    if not value:
        return 0

    try:
        return int(value)
    except ValueError:
        return 0


# ============================================================
# Authentication, content type, and request size
# ============================================================

@app.middleware("http")
async def api_middleware(request: Request, call_next):
    path = request.url.path

    if is_protected_path(path):
        # Validate the API key before processing protected requests.
        if not verify_api_key_headers(request.headers):
            return error_response(
                401,
                "UNAUTHORIZED",
                "Missing or invalid API key.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Require JSON for requests that submit a body.
        if request.method in {"POST", "PUT", "PATCH"}:
            content_type = request.headers.get("content-type", "")

            if not content_type.lower().startswith("application/json"):
                return error_response(
                    415,
                    "UNSUPPORTED_MEDIA_TYPE",
                    "Content-Type must be application/json.",
                )

        # Enforce request-size limits using Content-Length.
        if request.method == "POST":
            content_length = get_content_length(request)

            if (
                path == "/predict/batch"
                and content_length > SYNC_BATCH_MAX_BYTES
            ):
                return error_response(
                    413,
                    "PAYLOAD_TOO_LARGE",
                    "Request body exceeds the 5 MB limit.",
                )

            if (
                path == "/batch/jobs"
                and content_length > ASYNC_BATCH_MAX_BYTES
            ):
                return error_response(
                    413,
                    "PAYLOAD_TOO_LARGE",
                    "Request body exceeds the 25 MB limit.",
                )

    return await call_next(request)


# ============================================================
# Request validation errors
# ============================================================

@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
):
    errors = exc.errors()

    # Return HTTP 400 for malformed JSON.
    for error in errors:
        if error.get("type") == "json_invalid":
            return error_response(
                400,
                "INVALID_JSON",
                "Request body contains invalid JSON.",
                issue="Request body contains invalid JSON.",
            )

    # Return HTTP 422 for other validation failures.
    index = None
    field = None
    issue = "Request validation failed."

    if errors:
        first_error = errors[0]
        location = first_error.get("loc", ())
        message = first_error.get("msg")

        if location:
            field_parts = []

            for item in location:
                if isinstance(item, int):
                    index = item
                else:
                    field_parts.append(str(item))

            if field_parts:
                field = ".".join(field_parts)

        if message:
            issue = message

    return error_response(
        422,
        "VALIDATION_ERROR",
        "Request validation failed.",
        index=index,
        field=field,
        issue=issue,
    )


# ============================================================
# HTTP exception handler
# ============================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(
    request: Request,
    exc: HTTPException,
):
    code_map = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        404: "NOT_FOUND",
        409: "CONFLICT",
        410: "GONE",
        413: "PAYLOAD_TOO_LARGE",
        415: "UNSUPPORTED_MEDIA_TYPE",
        422: "VALIDATION_ERROR",
        429: "TOO_MANY_REQUESTS",
    }

    return error_response(
        exc.status_code,
        code_map.get(exc.status_code, "HTTP_ERROR"),
        str(exc.detail),
        headers=exc.headers,
    )


# ============================================================
# Unknown routes and unsupported methods
# ============================================================

@app.exception_handler(StarletteHTTPException)
async def starlette_http_exception_handler(
    request: Request,
    exc: StarletteHTTPException,
):
    if exc.status_code == 404:
        return error_response(
            404,
            "NOT_FOUND",
            "Route not found.",
        )

    if exc.status_code == 405:
        headers = None

        if exc.headers and "Allow" in exc.headers:
            headers = {"Allow": exc.headers["Allow"]}

        return error_response(
            405,
            "METHOD_NOT_ALLOWED",
            "HTTP method is not allowed for this route.",
            headers=headers,
        )

    return error_response(
        exc.status_code,
        "HTTP_ERROR",
        str(exc.detail),
        headers=exc.headers,
    )


# ============================================================
# Health
# ============================================================

@app.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(
        status="ok",
        model_version=inference_service.model_version,
        model_loaded=True,
    )


# ============================================================
# Single prediction
# ============================================================

@app.post("/predict", response_model=PredictResponse)
def predict(request: PredictRequest):
    return inference_service.predict_one(request)


# ============================================================
# Synchronous batch prediction
# ============================================================

@app.post("/predict/batch", response_model=BatchResponse)
def predict_batch(request: BatchRequest):
    predictions = inference_service.predict_batch(request.tickets)

    return BatchResponse(
        predictions=predictions,
        meta={"count": len(predictions)},
    )


# ============================================================
# Create asynchronous batch job
# ============================================================

@app.post(
    "/batch/jobs",
    response_model=BatchJobStatusResponse,
    status_code=202,
)
def create_batch_job(
    request: BatchJobRequest,
    response: Response,
    idempotency_key: str | None = Header(
        default=None,
        alias="Idempotency-Key",
    ),
):
    # Return the existing job when the idempotency key is reused.
    if idempotency_key:
        existing_job = job_manager.get_job_by_idempotency_key(
            idempotency_key
        )

        if existing_job is not None:
            response.headers["Location"] = (
                f"/batch/jobs/{existing_job['job_id']}"
            )
            response.headers["Retry-After"] = "2"

            return BatchJobStatusResponse(
                job_id=existing_job["job_id"],
                status=existing_job["status"],
                total=existing_job["total"],
                processed=existing_job["processed"],
                created_at=existing_job["created_at"],
                started_at=existing_job["started_at"],
                completed_at=existing_job["completed_at"],
                model_version=existing_job["model_version"],
                error=existing_job["error"],
            )

    # Enforce the active-job capacity limit.
    if job_manager.count_active_jobs() >= job_manager.MAX_ACTIVE_JOBS:
        return error_response(
            429,
            "TOO_MANY_REQUESTS",
            "Batch job capacity is currently full.",
            headers={"Retry-After": "5"},
        )

    # Create a new queued job.
    job = job_manager.create_job(
        tickets=request.tickets,
        idempotency_key=idempotency_key,
    )

    # Store the model version before processing starts.
    job_manager.update_job(
        job["job_id"],
        model_version=inference_service.model_version,
    )

    job = job_manager.get_job(job["job_id"])

    response.headers["Location"] = f"/batch/jobs/{job['job_id']}"
    response.headers["Retry-After"] = "2"

    # Start background processing.
    job_worker.submit(job["job_id"])

    return BatchJobStatusResponse(
        job_id=job["job_id"],
        status=job["status"],
        total=job["total"],
        processed=job["processed"],
        created_at=job["created_at"],
        started_at=job["started_at"],
        completed_at=job["completed_at"],
        model_version=job["model_version"],
        error=job["error"],
    )


# ============================================================
# Batch job status
# ============================================================

@app.get(
    "/batch/jobs/{job_id}",
    response_model=BatchJobStatusResponse,
)
def get_batch_job_status(job_id: str, response: Response):
    job = job_manager.get_job(job_id)

    if job is None:
        if job_manager.is_expired(job_id):
            raise HTTPException(
                status_code=410,
                detail="Batch job has expired.",
            )

        raise HTTPException(
            status_code=404,
            detail="Batch job not found.",
        )

    if job["status"] in {"queued", "running"}:
        response.headers["Retry-After"] = "2"

    return BatchJobStatusResponse(
        job_id=job["job_id"],
        status=job["status"],
        total=job["total"],
        processed=job["processed"],
        created_at=job["created_at"],
        started_at=job["started_at"],
        completed_at=job["completed_at"],
        model_version=job["model_version"],
        error=job["error"],
    )


# ============================================================
# Batch job results
# ============================================================

@app.get(
    "/batch/jobs/{job_id}/results",
    response_model=BatchJobResultsResponse,
)
def get_batch_job_results(
    job_id: str,
    offset: int = 0,
    limit: int = 100,
):
    if offset < 0:
        raise HTTPException(
            status_code=422,
            detail="offset must be >= 0.",
        )

    if limit < 1 or limit > 100:
        raise HTTPException(
            status_code=422,
            detail="limit must be between 1 and 100.",
        )

    job = job_manager.get_job(job_id)

    if job is None:
        if job_manager.is_expired(job_id):
            raise HTTPException(
                status_code=410,
                detail="Batch job has expired.",
            )

        raise HTTPException(
            status_code=404,
            detail="Batch job not found.",
        )

    # Return HTTP 409 until the job completes successfully.
    if job["status"] != "succeeded":
        raise HTTPException(
            status_code=409,
            detail="Batch job has not completed successfully.",
        )

    predictions = job.get("predictions") or []
    page = predictions[offset:offset + limit]

    next_offset = (
        offset + limit
        if offset + limit < len(predictions)
        else None
    )

    return BatchJobResultsResponse(
        job_id=job["job_id"],
        status="succeeded",
        total=len(predictions),
        offset=offset,
        limit=limit,
        next_offset=next_offset,
        predictions=page,
    )


# ============================================================
# Delete or cancel batch job
# ============================================================

@app.delete("/batch/jobs/{job_id}", status_code=204)
def delete_batch_job(job_id: str):
    job = job_manager.get_job(job_id)

    if job is None:
        if job_manager.is_expired(job_id):
            raise HTTPException(
                status_code=410,
                detail="Batch job has expired.",
            )

        raise HTTPException(
            status_code=404,
            detail="Batch job not found.",
        )

    if job["status"] in {"queued", "running"}:
        job_manager.update_job(
            job_id,
            status="cancelled",
            completed_at=job_manager._now(),
            error="Job cancelled by client.",
        )
        return Response(status_code=204)

    # Delete a completed or failed job.
    job_manager.delete_job(job_id)
    return Response(status_code=204)
