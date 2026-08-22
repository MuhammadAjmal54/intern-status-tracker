from datetime import date

from pydantic import BaseModel


# ============================================================
# Overall Statistics
# ============================================================

class StatisticsResponse(BaseModel):

    start_date: date | None
    end_date: date | None

    total_candidates: int
    active_candidates: int
    inactive_candidates: int

    total_status_records: int

    completed_statuses: int       # completion_percentage == 100
    in_progress_statuses: int     # 0 < completion_percentage < 100
    pending_statuses: int         # completion_percentage == 0
    blocked_statuses: int         # blockers non-empty

    average_completion_percentage: float


# ============================================================
# Candidate Performance
# ============================================================

class CandidatePerformance(BaseModel):

    candidate_id: int
    candidate_name: str

    total_status_days: int

    completed_days: int
    in_progress_days: int
    pending_days: int
    blocked_days: int

    average_completion_percentage: float

    rank: int


# ============================================================
# Candidate Performance Response
# ============================================================

class CandidatePerformanceResponse(BaseModel):

    start_date: date | None
    end_date: date | None

    total_candidates: int

    candidates: list[CandidatePerformance]