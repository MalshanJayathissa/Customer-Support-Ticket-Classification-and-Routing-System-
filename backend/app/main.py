import json
import re

from fastapi import (
    FastAPI,
    Header,
    HTTPException,
    Query,
    Request,
    Response,
)
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
    JobError,
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
    """Build and cache the OpenAPI document."""
    if app.openapi_schema:
        return app.openapi_schema

    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    schema.setdefault("components", {}).setdefault(
        "securitySchemes", {}
    )["APIKeyHeader"] = {
        "type": "apiKey",
        "in": "header",
        "name": "X-API-Key",
        "description": "Enter the API key configured in the backend .env file.",
    }

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

# Share one model instance between synchronous and background predictions.
inference_service = InferenceService()
job_worker = JobWorker(inference_service)


# ============================================================
# Standard JSON errors
# ============================================================

def error_response(
    status_code: int,
    code: str,
    message: str,
    *,
    index: int | None = None,
    field: str | None = None,
    issue: str | None = None,
    details: list[dict] | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    """Return errors in the API contract's standard format."""
    body = {
        "error": {
            "code": code.lower(),
            "message": message,
        }
    }

    # Convert a single detail into the required details array.
    if details is None and any(
        value is not None for value in (index, field, issue)
    ):
        detail = {}

        if index is not None:
            detail["index"] = index
        if field is not None:
            detail["field"] = field
        if issue is not None:
            detail["issue"] = issue

        details = [detail]

    if details:
        body["error"]["details"] = details

    return JSONResponse(
        status_code=status_code,
        content=body,
        headers=headers,
    )


# ============================================================
# Protected routes and request size
# ============================================================

def is_protected_path(path: str) -> bool:
    return (
        path in {"/predict", "/predict/batch", "/batch/jobs"}
        or path.startswith("/batch/jobs/")
    )


def get_content_length(request: Request) -> int | None:
    """Return Content-Length, or None if missing or invalid."""
    value = request.headers.get("content-length")

    if value is None:
        return None

    try:
        length = int(value)
        return length if length >= 0 else None
    except ValueError:
        return None


# ============================================================
# Authentication, content type, and body-size middleware
# IMPORTANT: Register this middleware BEFORE request_id_middleware.
# ============================================================

@app.middleware("http")
async def api_middleware(request: Request, call_next):
    path = request.url.path

    if not is_protected_path(path):
        return await call_next(request)

    # Authenticate before reading or processing protected request bodies.
    if not verify_api_key_headers(request.headers):
        return error_response(
            401,
            "unauthorized",
            "Missing or invalid API key.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Protected requests with bodies must use JSON.
    if request.method in {"POST", "PUT", "PATCH"}:
        content_type = request.headers.get("content-type", "")

        if not content_type.lower().startswith("application/json"):
            return error_response(
                415,
                "unsupported_media_type",
                "Content-Type must be application/json.",
            )

    # Apply size limits to synchronous and asynchronous batch submissions.
    if request.method == "POST" and path in {
        "/predict/batch",
        "/batch/jobs",
    }:
        body_limit = (
            SYNC_BATCH_MAX_BYTES
            if path == "/predict/batch"
            else ASYNC_BATCH_MAX_BYTES
        )
        limit_mb = body_limit // (1024 * 1024)

        # Reject oversized requests before reading the body.
        content_length = get_content_length(request)

        if content_length is not None and content_length > body_limit:
            return error_response(
                413,
                "payload_too_large",
                f"Request body exceeds the {limit_mb} MB limit.",
            )

        # Enforce the limit while reading, even without Content-Length.
        body_chunks = []
        body_size = 0

        while True:
            message = await request.receive()

            if message["type"] == "http.disconnect":
                return error_response(
                    400,
                    "request_disconnected",
                    "Client disconnected before sending the complete body.",
                )

            if message["type"] != "http.request":
                continue

            chunk = message.get("body", b"")
            body_size += len(chunk)

            if body_size > body_limit:
                return error_response(
                    413,
                    "payload_too_large",
                    f"Request body exceeds the {limit_mb} MB limit.",
                )

            body_chunks.append(chunk)

            if not message.get("more_body", False):
                break

        # Replay the consumed body so FastAPI can parse the JSON normally.
        body = b"".join(body_chunks)
        body_sent = False

        async def replay_body():
            nonlocal body_sent

            if body_sent:
                return {
                    "type": "http.request",
                    "body": b"",
                    "more_body": False,
                }

            body_sent = True
            return {
                "type": "http.request",
                "body": body,
                "more_body": False,
            }

        request._receive = replay_body

    return await call_next(request)


# ============================================================
# Request ID middleware
# IMPORTANT: Register this AFTER api_middleware.
# Starlette makes this the outer middleware, so early errors receive
# the X-Request-ID header too.
# ============================================================

@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    """Echo a supplied request ID on successful and error responses."""
    request_id = request.headers.get("X-Request-ID")
    response = await call_next(request)

    if request_id:
        response.headers["X-Request-ID"] = request_id

    return response


# ============================================================
# Request validation errors
# ============================================================

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
):
    details = []

    for error in exc.errors():
        location = list(error.get("loc", ()))
        message = str(error.get("msg", "Invalid value"))

        # Remove the request-body prefix from the validation location.
        if location and location[0] == "body":
            location = location[1:]

        # Recover individual ticket indexes from the duplicate-ID validator.
        if "Duplicate ticket_id values at:" in message:
            matches = re.findall(
                r"tickets\[(\d+)\]\.ticket_id",
                message,
            )

            for index_text in matches:
                details.append({
                    "index": int(index_text),
                    "field": "ticket_id",
                    "issue": "Duplicate ticket_id value.",
                })

            continue

        # Build the field path for ordinary validation errors.
        index = None

        if len(location) >= 2 and location[0] == "tickets":
            if isinstance(location[1], int):
                index = location[1]
                field = ".".join(str(part) for part in location[2:])
            else:
                field = ".".join(str(part) for part in location)
        else:
            field = ".".join(str(part) for part in location) or "request"

        detail = {
            "field": field,
            "issue": message,
        }

        if index is not None:
            detail["index"] = index

        details.append(detail)

    return error_response(
        status_code=422,
        code="validation_error",
        message="Request failed validation.",
        details=details,
    )


# ============================================================
# HTTP exceptions
# ============================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(
    request: Request,
    exc: HTTPException,
):
    code_map = {
        400: "bad_request",
        401: "unauthorized",
        404: "not_found",
        409: "conflict",
        410: "gone",
        413: "payload_too_large",
        415: "unsupported_media_type",
        422: "validation_error",
        429: "too_many_requests",
    }

    return error_response(
        exc.status_code,
        code_map.get(exc.status_code, "http_error"),
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
            "not_found",
            "Route not found.",
        )

    if exc.status_code == 405:
        headers = None

        if exc.headers and "Allow" in exc.headers:
            headers = {"Allow": exc.headers["Allow"]}

        return error_response(
            405,
            "method_not_allowed",
            "HTTP method is not allowed for this route.",
            headers=headers,
        )

    return error_response(
        exc.status_code,
        "http_error",
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
# Shared job status response helper
# ============================================================

def build_job_status(job: dict) -> BatchJobStatusResponse:
    """Map internal job fields to the public status schema."""
    error = job.get("error")

    if error is not None and not isinstance(error, dict):
        error = {
            "code": "job_failed",
            "message": str(error),
        }

    return BatchJobStatusResponse(
        job_id=job["job_id"],
        status=job["status"],
        total=job["total"],
        processed=job["processed"],
        created_at=job["created_at"],
        started_at=job.get("started_at"),
        finished_at=job.get("finished_at"),
        expires_at=job.get("expires_at"),
        model_version=(
            job.get("model_version") or inference_service.model_version
        ),
        error=JobError(**error) if error else None,
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
    # Reuse a job when its idempotency key is repeated.
    if idempotency_key:
        existing_job = job_manager.get_job_by_idempotency_key(
            idempotency_key
        )

        if existing_job is not None:
            response.headers["Location"] = (
                f"/batch/jobs/{existing_job['job_id']}"
            )
            response.headers["Retry-After"] = "2"
            return build_job_status(existing_job)

    # Reject new jobs when the active-job capacity is full.
    if job_manager.count_active_jobs() >= job_manager.MAX_ACTIVE_JOBS:
        return error_response(
            429,
            "too_many_requests",
            "Batch job capacity is currently full.",
            headers={"Retry-After": "5"},
        )

    job = job_manager.create_job(
        tickets=request.tickets,
        idempotency_key=idempotency_key,
    )

    # Record the model version before background processing starts.
    job_manager.update_job(
        job["job_id"],
        model_version=inference_service.model_version,
    )

    job = job_manager.get_job(job["job_id"])

    response.headers["Location"] = f"/batch/jobs/{job['job_id']}"
    response.headers["Retry-After"] = "2"

    job_worker.submit(job["job_id"])

    return build_job_status(job)


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

    return build_job_status(job)


# ============================================================
# Batch job results
# ============================================================

@app.get(
    "/batch/jobs/{job_id}/results",
    response_model=BatchJobResultsResponse,
)
def get_batch_job_results(
    job_id: str,
    offset: int = Query(default=0, ge=0),
    limit: int | None = Query(default=None, ge=1, le=5000),
):
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

    if job["status"] != "succeeded":
        raise HTTPException(
            status_code=409,
            detail="Batch job has not completed successfully.",
        )

    predictions = job.get("predictions") or []
    total = len(predictions)

    # Without a limit, return all results.
    effective_limit = total if limit is None else limit
    page = predictions[offset:offset + effective_limit]

    next_offset = (
        offset + len(page)
        if offset + len(page) < total
        else None
    )

    return BatchJobResultsResponse(
        job_id=job["job_id"],
        status="succeeded",
        total=total,
        offset=offset,
        limit=effective_limit,
        next_offset=next_offset,
        model_version=(
            job.get("model_version") or inference_service.model_version
        ),
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
            error=None,
        )
        return Response(status_code=204)

    # Completed, failed, or already-cancelled jobs can be deleted.
    job_manager.delete_job(job_id)
    return Response(status_code=204)