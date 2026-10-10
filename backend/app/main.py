from fastapi import FastAPI, Header, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
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
from app.services.job_worker import job_worker


app = FastAPI(
    title="TensorForge Customer Support Ticket Classification API",
    version="2.1.0",
)


# ============================================================
# Constants
# ============================================================

SYNC_BATCH_MAX_BYTES = 5 * 1024 * 1024
ASYNC_BATCH_MAX_BYTES = 25 * 1024 * 1024

PROTECTED_PREFIXES = (
    "/predict",
    "/batch/jobs",
)


# ============================================================
# Services
# ============================================================

inference_service = InferenceService()


# ============================================================
# Helper: JSON error response
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
# Helper: protected routes
# ============================================================

def is_protected_path(path: str) -> bool:
    if path == "/predict":
        return True

    if path == "/predict/batch":
        return True

    if path == "/batch/jobs":
        return True

    if path.startswith("/batch/jobs/"):
        return True

    return False


# ============================================================
# Helper: content length
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
# Authentication + validation-order middleware
# ============================================================

@app.middleware("http")
async def api_middleware(request: Request, call_next):
    path = request.url.path

    if is_protected_path(path):

        # ----------------------------------------------------
        # 1. Authentication
        # MUST happen before body parsing / validation
        # ----------------------------------------------------
        if not verify_api_key_headers(request.headers):
            return error_response(
                401,
                "UNAUTHORIZED",
                "Missing or invalid API key.",
                headers={
                    "WWW-Authenticate": "Bearer",
                },
            )

        # ----------------------------------------------------
        # 2. Content-Type
        # ----------------------------------------------------
        if request.method in {"POST", "PUT", "PATCH"}:
            content_type = request.headers.get(
                "content-type",
                "",
            )

            if not content_type.lower().startswith(
                "application/json"
            ):
                return error_response(
                    415,
                    "UNSUPPORTED_MEDIA_TYPE",
                    "Content-Type must be application/json.",
                )

        # ----------------------------------------------------
        # 3. Request size
        # ----------------------------------------------------
        if request.method == "POST":
            content_length = get_content_length(request)

            if path == "/predict/batch":
                if content_length > SYNC_BATCH_MAX_BYTES:
                    return error_response(
                        413,
                        "PAYLOAD_TOO_LARGE",
                        "Request body exceeds the 5 MB limit.",
                    )

            elif path == "/batch/jobs":
                if content_length > ASYNC_BATCH_MAX_BYTES:
                    return error_response(
                        413,
                        "PAYLOAD_TOO_LARGE",
                        "Request body exceeds the 25 MB limit.",
                    )

    return await call_next(request)


# ============================================================
# Pydantic validation errors
# ============================================================

@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
):
    errors = exc.errors()

    # --------------------------------------------------------
    # Invalid JSON -> 400
    # --------------------------------------------------------
    for error in errors:
        if error.get("type") == "json_invalid":
            return error_response(
                400,
                "INVALID_JSON",
                "Request body contains invalid JSON.",
                issue="Request body contains invalid JSON.",
            )

    # --------------------------------------------------------
    # Validation error -> 422
    # --------------------------------------------------------
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
# FastAPI HTTPException handler
# ============================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(
    request: Request,
    exc: HTTPException,
):
    status = exc.status_code

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

    code = code_map.get(
        status,
        "HTTP_ERROR",
    )

    headers = {}

    if exc.headers:
        headers.update(exc.headers)

    return error_response(
        status,
        code,
        str(exc.detail),
        headers=headers or None,
    )


# ============================================================
# Unknown routes + unsupported methods
# ============================================================

@app.exception_handler(StarletteHTTPException)
async def starlette_http_exception_handler(
    request: Request,
    exc: StarletteHTTPException,
):
    # --------------------------------------------------------
    # Unknown route
    # --------------------------------------------------------
    if exc.status_code == 404:
        return error_response(
            404,
            "NOT_FOUND",
            "Route not found.",
        )

    # --------------------------------------------------------
    # Unsupported HTTP method
    # --------------------------------------------------------
    if exc.status_code == 405:
        headers = None

        if exc.headers and "Allow" in exc.headers:
            headers = {
                "Allow": exc.headers["Allow"],
            }

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

@app.get(
    "/health",
    response_model=HealthResponse,
)
def health():
    return HealthResponse(
        status="ok",
        model_version=inference_service.model_version,
        model_loaded=True,
    )


# ============================================================
# Single prediction
# ============================================================

@app.post(
    "/predict",
    response_model=PredictResponse,
)
def predict(request: PredictRequest):
    result = inference_service.predict_one(
        request
    )

    return result


# ============================================================
# Synchronous batch prediction
# ============================================================

@app.post(
    "/predict/batch",
    response_model=BatchResponse,
)
def predict_batch(
    request: BatchRequest,
):
    predictions = inference_service.predict_batch(
        request.tickets
    )

    return BatchResponse(
        predictions=predictions,
        meta={
            "count": len(predictions),
        },
    )


# ============================================================
# Async batch job creation
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
    # --------------------------------------------------------
    # Idempotency
    # --------------------------------------------------------
    if idempotency_key:
        existing_job = (
            job_manager.get_job_by_idempotency_key(
                idempotency_key
            )
        )

        if existing_job is not None:
            response.status_code = 202

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

    # --------------------------------------------------------
    # Capacity
    # Maximum:
    # 1 running + 3 queued = 4 active jobs
    # --------------------------------------------------------
    active_count = job_manager.count_active_jobs()

    if active_count >= 4:
        return error_response(
            429,
            "TOO_MANY_REQUESTS",
            "Batch job capacity is currently full.",
            headers={
                "Retry-After": "5",
            },
        )

    # --------------------------------------------------------
    # Create job
    # --------------------------------------------------------
    job = job_manager.create_job(
        tickets=request.tickets,
        idempotency_key=idempotency_key,
    )

    response.status_code = 202

    response.headers["Location"] = (
        f"/batch/jobs/{job['job_id']}"
    )

    response.headers["Retry-After"] = "2"

    # --------------------------------------------------------
    # Start background worker
    # --------------------------------------------------------
    job_worker.submit(
        job["job_id"]
    )

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
def get_batch_job_status(
    job_id: str,
    response: Response,
):
    job = job_manager.get_job(
        job_id
    )

    if job is None:

        if job_manager.is_expired(
            job_id
        ):
            raise HTTPException(
                status_code=410,
                detail="Batch job has expired.",
            )

        raise HTTPException(
            status_code=404,
            detail="Batch job not found.",
        )

    # --------------------------------------------------------
    # Retry-After while queued/running
    # --------------------------------------------------------
    if job["status"] in {
        "queued",
        "running",
    }:
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
    # --------------------------------------------------------
    # Pagination validation
    # --------------------------------------------------------
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

    # --------------------------------------------------------
    # Find job
    # --------------------------------------------------------
    job = job_manager.get_job(
        job_id
    )

    if job is None:

        if job_manager.is_expired(
            job_id
        ):
            raise HTTPException(
                status_code=410,
                detail="Batch job has expired.",
            )

        raise HTTPException(
            status_code=404,
            detail="Batch job not found.",
        )

    # --------------------------------------------------------
    # Results only available after success
    # --------------------------------------------------------
    if job["status"] != "succeeded":
        raise HTTPException(
            status_code=409,
            detail=(
                "Batch job has not completed "
                "successfully."
            ),
        )

    predictions = (
        job.get("predictions")
        or []
    )

    # --------------------------------------------------------
    # Pagination
    # --------------------------------------------------------
    page = predictions[
        offset : offset + limit
    ]

    next_offset = None

    if offset + limit < len(predictions):
        next_offset = offset + limit

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
# Delete / cancel batch job
# ============================================================

@app.delete(
    "/batch/jobs/{job_id}",
    status_code=204,
)
def delete_batch_job(
    job_id: str,
):
    job = job_manager.get_job(
        job_id
    )

    if job is None:

        if job_manager.is_expired(
            job_id
        ):
            raise HTTPException(
                status_code=410,
                detail="Batch job has expired.",
            )

        raise HTTPException(
            status_code=404,
            detail="Batch job not found.",
        )

    # --------------------------------------------------------
    # Queued / running -> cancel
    # --------------------------------------------------------
    if job["status"] in {
        "queued",
        "running",
    }:
        job_manager.update_job(
            job_id,
            status="cancelled",
            completed_at=job_manager._now(),
            error="Job cancelled by client.",
        )

        return Response(
            status_code=204
        )

    # --------------------------------------------------------
    # Finished -> discard
    # --------------------------------------------------------
    job_manager.delete_job(
        job_id
    )

    return Response(
        status_code=204
    )