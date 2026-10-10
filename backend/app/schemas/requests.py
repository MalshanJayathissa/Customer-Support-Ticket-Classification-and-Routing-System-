from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


Channel = Literal[
    "email",
    "chat",
    "call_transcript",
]


class PredictRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    # Optional for /predict. Explicit null is rejected because the type is str.
    ticket_id: str = Field(default=None, max_length=64)

    channel: Channel
    subject: str = Field(default="", max_length=500)
    text: str = Field(min_length=1, max_length=10_000)

    @field_validator("text")
    @classmethod
    def text_must_contain_non_whitespace(cls, value: str) -> str:
        if not value.strip():
            raise ValueError(
                "Text must contain at least one non-whitespace character."
            )
        return value


class BatchTicketRequest(PredictRequest):
    # Required for every ticket in either batch endpoint.
    ticket_id: str = Field(min_length=1, max_length=64)


class BatchRequest(BaseModel):
    tickets: list[BatchTicketRequest] = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def ticket_ids_must_be_unique(self):
        seen: set[str] = set()
        duplicates: list[str] = []

        for index, ticket in enumerate(self.tickets):
            if ticket.ticket_id in seen:
                duplicates.append(f"tickets[{index}].ticket_id")
            seen.add(ticket.ticket_id)

        if duplicates:
            raise ValueError(
                "Duplicate ticket_id values at: " + ", ".join(duplicates)
            )

        return self


class BatchJobRequest(BaseModel):
    tickets: list[BatchTicketRequest] = Field(min_length=1, max_length=5000)

    @model_validator(mode="after")
    def ticket_ids_must_be_unique(self):
        seen: set[str] = set()
        duplicates: list[str] = []

        for index, ticket in enumerate(self.tickets):
            if ticket.ticket_id in seen:
                duplicates.append(f"tickets[{index}].ticket_id")
            seen.add(ticket.ticket_id)

        if duplicates:
            raise ValueError(
                "Duplicate ticket_id values at: " + ", ".join(duplicates)
            )

        return self
