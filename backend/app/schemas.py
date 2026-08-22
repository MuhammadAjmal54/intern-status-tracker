from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class CandidateCreate(BaseModel):
    full_name: str
    email: str
    training_track: str
    is_active: bool = True


class CandidateUpdate(BaseModel):
    full_name: str
    email: str
    training_track: str
    is_active: bool


class CandidateResponse(BaseModel):
    id: int
    full_name: str
    email: str
    training_track: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )


class CandidateStatusResponse(BaseModel):
    id: int
    status_date: date

    work_completed: str
    topics_learned: str
    blockers: str | None
    next_day_plan: str
    completion_percentage: int

    model_config = ConfigDict(
        from_attributes=True
    )


class CandidateWithStatusesResponse(BaseModel):
    id: int
    full_name: str
    email: str
    training_track: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    statuses: list[CandidateStatusResponse] = []

    model_config = ConfigDict(
        from_attributes=True
    )