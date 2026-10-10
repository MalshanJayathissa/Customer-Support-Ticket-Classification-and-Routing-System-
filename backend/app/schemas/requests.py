from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


Channel = Literal[
    "email",
    "chat",
    "call_transcript",
]


class PredictRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    ticket_id: str | None = Field(
        default=None,
        max_length=64,
    )

    channel: Channel

    subject: str = Field(
        default="",
        max_length=500,
    )

    text: str = Field(
        min_length=1,
        max_length=10_000,
    )

    @field_validator("text")
    @classmethod
    def text_must_contain_non_whitespace(
        cls,
        value: str,
    ) -> str:
        if not value.strip():
            raise ValueError(
                "Field 'text' must contain at least one "
                "non-whitespace character."
            )

        return value


class BatchRequest(BaseModel):
    tickets: list[PredictRequest] = Field(
        min_length=1,
        max_length=100,
    )

    @field_validator("tickets")
    @classmethod
    def validate_ticket_ids(
        cls,
        tickets: list[PredictRequest],
    ):
        seen: set[str] = set()

        for index, ticket in enumerate(tickets):
            if not ticket.ticket_id:
                raise ValueError(
                    f"tickets[{index}].ticket_id is required."
                )

            if ticket.ticket_id in seen:
                raise ValueError(
                    f"tickets[{index}].ticket_id is duplicated: "
                    f"{ticket.ticket_id}"
                )

            seen.add(ticket.ticket_id)

        return tickets


class BatchJobRequest(BaseModel):
    tickets: list[PredictRequest] = Field(
        min_length=1,
        max_length=5000,
    )

    @field_validator("tickets")
    @classmethod
    def validate_ticket_ids(
        cls,
        tickets: list[PredictRequest],
    ):
        seen: set[str] = set()

        for index, ticket in enumerate(tickets):
            if not ticket.ticket_id:
                raise ValueError(
                    f"tickets[{index}].ticket_id is required."
                )

            if ticket.ticket_id in seen:
                raise ValueError(
                    f"tickets[{index}].ticket_id is duplicated: "
                    f"{ticket.ticket_id}"
                )

            seen.add(ticket.ticket_id)

        return tickets