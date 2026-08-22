from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, case, func
from sqlalchemy.orm import Session

from .database import get_db
from . import models
from .statistics_schemas import (
    StatisticsResponse,
    CandidatePerformanceResponse,
)


router = APIRouter(
    prefix="/api",
    tags=["Statistics & Dashboard"],
)


# ============================================================
# Helper: Validate Date Range
# ============================================================

def validate_date_range(
    start_date: date | None,
    end_date: date | None,
):
    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=400,
            detail="start_date cannot be greater than end_date",
        )


# ============================================================
# Dashboard Summary
# GET /api/dashboard/summary?date=YYYY-MM-DD
# ============================================================

@router.get(
    "/dashboard/summary",
    summary="Get daily dashboard summary for candidates",
)
def get_dashboard_summary(
    date: date | None = Query(
        None,
        description="Date to filter (defaults to today)"
    ),
    db: Session = Depends(get_db),
):
    import datetime as _dt
    target_date = date or _dt.date.today()

    # 1. All active candidates
    active_candidates = (
        db.query(models.Candidate)
        .filter(models.Candidate.is_active.is_(True))
        .all()
    )
    total_active_candidates = len(active_candidates)

    # 2. Statuses for the selected date
    statuses_on_date = (
        db.query(models.DailyStatus)
        .filter(models.DailyStatus.status_date == target_date)
        .all()
    )
    status_map = {s.candidate_id: s for s in statuses_on_date}

    # 3. Latest status per active candidate (subquery approach)
    latest_date_subq = (
        db.query(
            models.DailyStatus.candidate_id,
            func.max(models.DailyStatus.status_date).label("latest_date"),
        )
        .group_by(models.DailyStatus.candidate_id)
        .subquery()
    )

    latest_statuses_rows = (
        db.query(models.DailyStatus)
        .join(
            latest_date_subq,
            and_(
                models.DailyStatus.candidate_id == latest_date_subq.c.candidate_id,
                models.DailyStatus.status_date  == latest_date_subq.c.latest_date,
            ),
        )
        .all()
    )
    latest_status_map = {s.candidate_id: s for s in latest_statuses_rows}

    # 4. Separate submitted vs missing
    submitted_candidates = []
    missing_candidates = []

    for candidate in active_candidates:
        latest = latest_status_map.get(candidate.id)
        candidate_data = {
            "id":             candidate.id,
            "full_name":      candidate.full_name,
            "email":          candidate.email,
            "training_track": candidate.training_track,
            "is_active":      candidate.is_active,
            "latest_status":  {
                "id":                    latest.id,
                "status_date":           str(latest.status_date),
                "work_completed":        latest.work_completed,
                "topics_learned":        latest.topics_learned,
                "blockers":              latest.blockers,
                "next_day_plan":         latest.next_day_plan,
                "completion_percentage": latest.completion_percentage,
            } if latest else None,
        }

        if candidate.id in status_map:
            submitted_candidates.append(candidate_data)
        else:
            missing_candidates.append(candidate_data)

    # 5. Sort submitted by completion % desc
    submitted_candidates.sort(
        key=lambda c: status_map[c["id"]].completion_percentage,
        reverse=True,
    )

    # 6. Average completion for the selected date
    if statuses_on_date:
        average_completion = round(
            sum(s.completion_percentage for s in statuses_on_date)
            / len(statuses_on_date),
            2,
        )
    else:
        average_completion = 0.0

    return {
        "summary_date":                str(target_date),
        "total_active_candidates":     total_active_candidates,
        "submitted_count":             len(submitted_candidates),
        "missing_count":               len(missing_candidates),
        "average_completion_percentage": average_completion,
        "submitted_candidates":        submitted_candidates,
        "missing_candidates":          missing_candidates,
    }


# ============================================================
# Overall Statistics
# GET /api/statistics
# ============================================================

@router.get(
    "/statistics",
    response_model=StatisticsResponse,
)
def get_statistics(
    start_date: date | None = None,
    end_date: date | None = None,
    db: Session = Depends(get_db),
):
    validate_date_range(start_date, end_date)

    total_candidates = db.query(func.count(models.Candidate.id)).scalar() or 0
    active_candidates = (
        db.query(func.count(models.Candidate.id))
        .filter(models.Candidate.is_active.is_(True))
        .scalar() or 0
    )
    inactive_candidates = (
        db.query(func.count(models.Candidate.id))
        .filter(models.Candidate.is_active.is_(False))
        .scalar() or 0
    )

    status_query = db.query(models.DailyStatus)
    if start_date:
        status_query = status_query.filter(models.DailyStatus.status_date >= start_date)
    if end_date:
        status_query = status_query.filter(models.DailyStatus.status_date <= end_date)

    total_status_records  = status_query.with_entities(func.count(models.DailyStatus.id)).scalar() or 0
    completed_statuses    = status_query.filter(models.DailyStatus.completion_percentage == 100).count()
    in_progress_statuses  = status_query.filter(
        models.DailyStatus.completion_percentage > 0,
        models.DailyStatus.completion_percentage < 100,
    ).count()
    pending_statuses  = status_query.filter(models.DailyStatus.completion_percentage == 0).count()
    blocked_statuses  = status_query.filter(
        models.DailyStatus.blockers.isnot(None),
        models.DailyStatus.blockers != "",
    ).count()

    avg_pct = status_query.with_entities(
        func.avg(models.DailyStatus.completion_percentage)
    ).scalar()
    average_completion_percentage = round(float(avg_pct) if avg_pct is not None else 0.0, 2)

    return {
        "start_date":                    start_date,
        "end_date":                      end_date,
        "total_candidates":              int(total_candidates),
        "active_candidates":             int(active_candidates),
        "inactive_candidates":           int(inactive_candidates),
        "total_status_records":          int(total_status_records),
        "completed_statuses":            int(completed_statuses),
        "in_progress_statuses":          int(in_progress_statuses),
        "pending_statuses":              int(pending_statuses),
        "blocked_statuses":              int(blocked_statuses),
        "average_completion_percentage": average_completion_percentage,
    }


# ============================================================
# Candidate Performance
# GET /api/statistics/candidates/performance
# ============================================================

@router.get(
    "/statistics/candidates/performance",
    response_model=CandidatePerformanceResponse,
)
def get_candidate_performance(
    start_date: date | None = None,
    end_date: date | None = None,
    db: Session = Depends(get_db),
):
    validate_date_range(start_date, end_date)

    # Build join conditions
    join_conditions = [models.Candidate.id == models.DailyStatus.candidate_id]
    if start_date:
        join_conditions.append(models.DailyStatus.status_date >= start_date)
    if end_date:
        join_conditions.append(models.DailyStatus.status_date <= end_date)

    # SQLAlchemy 2.x case() syntax: each when is a separate positional (condition, result) tuple
    completed_expr = func.coalesce(
        func.sum(
            case(
                (models.DailyStatus.completion_percentage == 100, 1),
                else_=0,
            )
        ),
        0,
    )

    in_progress_expr = func.coalesce(
        func.sum(
            case(
                (
                    and_(
                        models.DailyStatus.completion_percentage > 0,
                        models.DailyStatus.completion_percentage < 100,
                    ),
                    1,
                ),
                else_=0,
            )
        ),
        0,
    )

    pending_expr = func.coalesce(
        func.sum(
            case(
                (models.DailyStatus.completion_percentage == 0, 1),
                else_=0,
            )
        ),
        0,
    )

    blocked_expr = func.coalesce(
        func.sum(
            case(
                (
                    and_(
                        models.DailyStatus.blockers.isnot(None),
                        models.DailyStatus.blockers != "",
                    ),
                    1,
                ),
                else_=0,
            )
        ),
        0,
    )

    query = (
        db.query(
            models.Candidate.id.label("candidate_id"),
            models.Candidate.full_name.label("candidate_name"),
            func.count(models.DailyStatus.id).label("total_status_days"),
            completed_expr.label("completed_days"),
            in_progress_expr.label("in_progress_days"),
            pending_expr.label("pending_days"),
            blocked_expr.label("blocked_days"),
            func.coalesce(
                func.avg(models.DailyStatus.completion_percentage), 0
            ).label("average_completion_percentage"),
        )
        .outerjoin(models.DailyStatus, and_(*join_conditions))
        .group_by(models.Candidate.id, models.Candidate.full_name)
    )

    rows = query.all()

    performance = []
    for row in rows:
        performance.append({
            "candidate_id":                  row.candidate_id,
            "candidate_name":                row.candidate_name,
            "total_status_days":             int(row.total_status_days or 0),
            "completed_days":                int(row.completed_days or 0),
            "in_progress_days":              int(row.in_progress_days or 0),
            "pending_days":                  int(row.pending_days or 0),
            "blocked_days":                  int(row.blocked_days or 0),
            "average_completion_percentage": round(float(row.average_completion_percentage or 0), 2),
            "rank":                          0,
        })

    # Rank by average completion % desc
    performance.sort(key=lambda c: c["average_completion_percentage"], reverse=True)
    for rank, c in enumerate(performance, start=1):
        c["rank"] = rank

    return {
        "start_date":       start_date,
        "end_date":         end_date,
        "total_candidates": len(performance),
        "candidates":       performance,
    }
