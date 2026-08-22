from datetime import date
from pydantic import BaseModel


class CandidateSummaryResponse(BaseModel):
    candidate_id: int
    candidate_name: str

    start_date: date | None
    end_date: date | None

    total_status_days: int

    average_completion_percentage: float

    completed_days: int       # completion_percentage == 100
    in_progress_days: int     # 0 < completion_percentage < 100
    pending_days: int         # completion_percentage == 0
    blocked_days: int         # blockers field is non-empty