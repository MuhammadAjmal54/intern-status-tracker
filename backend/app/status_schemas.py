from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class DailyStatusCreate(BaseModel):
    candidate_id: int = Field(gt=0)

    status_date: date

    work_completed: str = Field(
        min_length=1,
        max_length=5000
    )

    topics_learned: str = Field(
        min_length=1,
        max_length=5000
    )

    blockers: str | None = Field(
        default=None,
        max_length=5000
    )

    next_day_plan: str = Field(
        min_length=1,
        max_length=5000
    )

    completion_percentage: int = Field(
        ge=0,
        le=100
    )


class DailyStatusUpdate(BaseModel):
    candidate_id: int = Field(gt=0)

    status_date: date

    work_completed: str = Field(
        min_length=1,
        max_length=5000
    )

    topics_learned: str = Field(
        min_length=1,
        max_length=5000
    )

    blockers: str | None = Field(
        default=None,
        max_length=5000
    )

    next_day_plan: str = Field(
        min_length=1,
        max_length=5000
    )

    completion_percentage: int = Field(
        ge=0,
        le=100
    )


class DailyStatusResponse(BaseModel):
    id: int

    candidate_id: int

    status_date: date

    work_completed: str

    topics_learned: str

    blockers: str | None

    next_day_plan: str

    completion_percentage: int

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )