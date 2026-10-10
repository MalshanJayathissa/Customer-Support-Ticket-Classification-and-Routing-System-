from typing import Any, Literal

from pydantic import BaseModel, Field


Category = Literal[
    "payment_refund",
    "ride_trip_issue",
    "lost_item",
    "order_missing_wrong",
    "delivery_delay",
    "food_quality",
    "account_promo",
    "safety_conduct",
    "app_technical",
    "general_inquiry",
    "spam_irrelevant",
]

Team = Literal[
    "Payments & Refunds",
    "Ride Operations",
    "Lost & Found",
    "Food Operations",
    "Delivery Operations",
    "Restaurant Quality",
    "Account Services",
    "Trust & Safety",
    "Tech Support",
    "Front-line Support",
    "Auto-close / Spam Filter",
]


class PredictResponse(BaseModel):
    ticket_id: str | None = None
    category: Category
    secondary_category: Category | None
    team: Team
    is_urgent: bool
    confidence: float = Field(ge=0, le=1)
    model_version: str = Field(min_length=1)
    needs_human_review: bool | None = None


class BatchResponse(BaseModel):
    predictions: list[PredictResponse]
    meta: dict[str, Any] | None = None


class BatchJobStatusResponse(BaseModel):
    job_id: str
    status: Literal[
        "queued",
        "running",
        "succeeded",
        "failed",
        "cancelled",
    ]
    total: int
    processed: int
    created_at: str
    started_at: str | None = None
    completed_at: str | None = None
    model_version: str | None = None
    error: str | None = None


class BatchJobResultsResponse(BaseModel):
    job_id: str
    status: Literal["succeeded"]
    total: int
    offset: int
    limit: int
    next_offset: int | None
    predictions: list[PredictResponse]


class ErrorDetails(BaseModel):
    index: int | None = None
    field: str | None = None
    issue: str | None = None


class ErrorBody(BaseModel):
    code: str
    message: str
    details: ErrorDetails | None = None


class ErrorResponse(BaseModel):
    error: ErrorBody


class HealthResponse(BaseModel):
    status: Literal["ok", "loading"]
    model_version: str | None
    model_loaded: bool | None = None