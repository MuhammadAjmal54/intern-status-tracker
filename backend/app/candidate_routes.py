from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .database import get_db
from . import models, schemas
from .summary_schemas import CandidateSummaryResponse


router = APIRouter(
    prefix="/api/candidates",
    tags=["Candidates"]
)


# =========================
# Get All Candidates
# =========================

@router.get(
    "",
    response_model=list[schemas.CandidateResponse]
)
def get_candidates(
    is_active: bool | None = Query(
        None,
        description="Filter by active/inactive status"
    ),
    skip: int = Query(
        0,
        ge=0,
        description="Number of candidates to skip"
    ),
    limit: int = Query(
        100,
        ge=1,
        le=500,
        description="Maximum number of candidates to return"
    ),
    db: Session = Depends(get_db)
):
    query = db.query(models.Candidate)

    if is_active is not None:
        query = query.filter(models.Candidate.is_active == is_active)

    candidates = (
        query
        .order_by(models.Candidate.id)
        .offset(skip)
        .limit(limit)
        .all()
    )

    return candidates


# =========================
# Get Candidate Summary
# =========================

@router.get(
    "/{candidate_id}/summary",
    response_model=CandidateSummaryResponse
)
def get_candidate_summary(
    candidate_id: int,
    start_date: date | None = None,
    end_date: date | None = None,
    db: Session = Depends(get_db)
):
    # =========================
    # Validate Date Range
    # =========================

    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=400,
            detail="start_date cannot be greater than end_date"
        )

    # =========================
    # Check Candidate Exists
    # =========================

    candidate = (
        db.query(models.Candidate)
        .filter(models.Candidate.id == candidate_id)
        .first()
    )

    if candidate is None:
        raise HTTPException(
            status_code=404,
            detail="Candidate not found"
        )

    # =========================
    # Status Query
    # =========================

    status_query = db.query(models.DailyStatus).filter(
        models.DailyStatus.candidate_id == candidate_id
    )

    if start_date is not None:
        status_query = status_query.filter(
            models.DailyStatus.status_date >= start_date
        )

    if end_date is not None:
        status_query = status_query.filter(
            models.DailyStatus.status_date <= end_date
        )

    # =========================
    # Status Counts (using real fields only)
    # =========================

    statuses = status_query.all()
    total_status_days = len(statuses)

    completed_days = sum(
        1 for s in statuses if s.completion_percentage == 100
    )
    in_progress_days = sum(
        1 for s in statuses
        if 0 < s.completion_percentage < 100
    )
    pending_days = sum(
        1 for s in statuses if s.completion_percentage == 0
    )
    blocked_days = sum(
        1 for s in statuses
        if s.blockers and s.blockers.strip()
    )

    if total_status_days > 0:
        average_completion_percentage = round(
            sum(s.completion_percentage for s in statuses)
            / total_status_days,
            2,
        )
    else:
        average_completion_percentage = 0.0

    # =========================
    # Response
    # =========================

    return {
        "candidate_id": candidate.id,
        "candidate_name": candidate.full_name,

        "start_date": start_date,
        "end_date": end_date,

        "total_status_days": total_status_days,
        "average_completion_percentage": average_completion_percentage,

        "completed_days": completed_days,
        "in_progress_days": in_progress_days,
        "pending_days": pending_days,
        "blocked_days": blocked_days,
    }


# =========================
# Get Single Candidate
# =========================

@router.get(
    "/{candidate_id}",
    response_model=schemas.CandidateWithStatusesResponse
)
def get_candidate(
    candidate_id: int,
    db: Session = Depends(get_db)
):
    candidate = (
        db.query(models.Candidate)
        .filter(models.Candidate.id == candidate_id)
        .first()
    )

    if candidate is None:
        raise HTTPException(
            status_code=404,
            detail="Candidate not found"
        )

    return candidate


# =========================
# Create Candidate
# =========================

@router.post(
    "",
    response_model=schemas.CandidateResponse,
    status_code=201
)
def create_candidate(
    candidate: schemas.CandidateCreate,
    db: Session = Depends(get_db)
):
    # Check duplicate email
    existing_candidate = (
        db.query(models.Candidate)
        .filter(models.Candidate.email == candidate.email)
        .first()
    )

    if existing_candidate:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    # Create candidate
    new_candidate = models.Candidate(
        full_name=candidate.full_name,
        email=candidate.email,
        training_track=candidate.training_track,
        is_active=candidate.is_active
    )

    db.add(new_candidate)

    try:
        db.commit()
        db.refresh(new_candidate)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=400,
            detail="Unable to create candidate"
        )

    return new_candidate


# =========================
# Update Candidate
# =========================

@router.put(
    "/{candidate_id}",
    response_model=schemas.CandidateResponse
)
def update_candidate(
    candidate_id: int,
    candidate_data: schemas.CandidateUpdate,
    db: Session = Depends(get_db)
):
    # Find candidate
    candidate = (
        db.query(models.Candidate)
        .filter(models.Candidate.id == candidate_id)
        .first()
    )

    if candidate is None:
        raise HTTPException(
            status_code=404,
            detail="Candidate not found"
        )

    # Check duplicate email
    existing_email = (
        db.query(models.Candidate)
        .filter(
            models.Candidate.email == candidate_data.email,
            models.Candidate.id != candidate_id
        )
        .first()
    )

    if existing_email:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    # Update candidate
    candidate.full_name = candidate_data.full_name
    candidate.email = candidate_data.email
    candidate.training_track = candidate_data.training_track
    candidate.is_active = candidate_data.is_active

    try:
        db.commit()
        db.refresh(candidate)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=400,
            detail="Unable to update candidate"
        )

    return candidate


# =========================
# Delete Candidate
# =========================

@router.delete("/{candidate_id}")
def delete_candidate(
    candidate_id: int,
    db: Session = Depends(get_db)
):
    # Find candidate
    candidate = (
        db.query(models.Candidate)
        .filter(models.Candidate.id == candidate_id)
        .first()
    )

    if candidate is None:
        raise HTTPException(
            status_code=404,
            detail="Candidate not found"
        )

    # Delete candidate
    db.delete(candidate)

    try:
        db.commit()

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=400,
            detail="Unable to delete candidate"
        )

    return {
        "message": "Candidate deleted successfully"
    }