from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .database import get_db
from . import models
from .status_schemas import (
    DailyStatusCreate,
    DailyStatusUpdate,
    DailyStatusResponse,
)


router = APIRouter(
    prefix="/api/statuses",
    tags=["Daily Status"]
)


# =========================
# Create Daily Status
# =========================

@router.post(
    "",
    response_model=DailyStatusResponse,
    status_code=201
)
def create_daily_status(
    status_data: DailyStatusCreate,
    db: Session = Depends(get_db)
):
    # Check candidate exists
    candidate = (
        db.query(models.Candidate)
        .filter(
            models.Candidate.id == status_data.candidate_id
        )
        .first()
    )

    if candidate is None:
        raise HTTPException(
            status_code=404,
            detail="Candidate not found"
        )

    # Check duplicate status
    existing_status = (
        db.query(models.DailyStatus)
        .filter(
            models.DailyStatus.candidate_id
            == status_data.candidate_id,
            models.DailyStatus.status_date
            == status_data.status_date
        )
        .first()
    )

    if existing_status:
        raise HTTPException(
            status_code=409,
            detail=(
                "Daily status already exists for this "
                "candidate on this date"
            )
        )

    # Create daily status
    new_status = models.DailyStatus(
        candidate_id=status_data.candidate_id,
        status_date=status_data.status_date,
        work_completed=status_data.work_completed,
        topics_learned=status_data.topics_learned,
        blockers=status_data.blockers,
        next_day_plan=status_data.next_day_plan,
        completion_percentage=status_data.completion_percentage,
    )

    db.add(new_status)

    try:
        db.commit()
        db.refresh(new_status)

    except IntegrityError:
        db.rollback()

        # Database-level unique constraint protection
        raise HTTPException(
            status_code=409,
            detail=(
                "Daily status already exists for this "
                "candidate on this date"
            )
        )

    return new_status


# =========================
# Get Daily Statuses
# =========================

@router.get(
    "",
    response_model=list[DailyStatusResponse]
)
def get_daily_statuses(
    candidate_id: int | None = Query(
        None,
        ge=1,
        description="Filter by candidate ID"
    ),

    status_date: date | None = Query(
        None,
        description="Filter by exact status date"
    ),

    date_from: date | None = Query(
        None,
        description="Get statuses from this date"
    ),

    date_to: date | None = Query(
        None,
        description="Get statuses up to this date"
    ),

    skip: int = Query(
        0,
        ge=0,
        description="Number of records to skip"
    ),

    limit: int = Query(
        100,
        ge=1,
        le=500,
        description="Maximum number of records"
    ),

    db: Session = Depends(get_db)
):
    # Validate date range
    if date_from is not None and date_to is not None:
        if date_from > date_to:
            raise HTTPException(
                status_code=400,
                detail="date_from cannot be greater than date_to"
            )

    query = db.query(models.DailyStatus)

    # Filter by candidate
    if candidate_id is not None:
        query = query.filter(
            models.DailyStatus.candidate_id == candidate_id
        )

    # Filter by exact date
    if status_date is not None:
        query = query.filter(
            models.DailyStatus.status_date == status_date
        )

    # Filter from date
    if date_from is not None:
        query = query.filter(
            models.DailyStatus.status_date >= date_from
        )

    # Filter to date
    if date_to is not None:
        query = query.filter(
            models.DailyStatus.status_date <= date_to
        )

    # Newest first + pagination
    statuses = (
        query
        .order_by(
            models.DailyStatus.status_date.desc(),
            models.DailyStatus.id.desc()
        )
        .offset(skip)
        .limit(limit)
        .all()
    )

    return statuses


# =========================
# Get Single Daily Status
# =========================

@router.get(
    "/{status_id}",
    response_model=DailyStatusResponse
)
def get_daily_status(
    status_id: int,
    db: Session = Depends(get_db)
):
    daily_status = (
        db.query(models.DailyStatus)
        .filter(
            models.DailyStatus.id == status_id
        )
        .first()
    )

    if daily_status is None:
        raise HTTPException(
            status_code=404,
            detail="Daily status not found"
        )

    return daily_status


# =========================
# Get Candidate Status History
# =========================

@router.get(
    "/candidate/{candidate_id}",
    response_model=list[DailyStatusResponse]
)
def get_candidate_statuses(
    candidate_id: int,

    skip: int = Query(
        0,
        ge=0,
        description="Number of records to skip"
    ),

    limit: int = Query(
        100,
        ge=1,
        le=500,
        description="Maximum number of records"
    ),

    db: Session = Depends(get_db)
):
    # Check candidate exists
    candidate = (
        db.query(models.Candidate)
        .filter(
            models.Candidate.id == candidate_id
        )
        .first()
    )

    if candidate is None:
        raise HTTPException(
            status_code=404,
            detail="Candidate not found"
        )

    # Get candidate status history
    statuses = (
        db.query(models.DailyStatus)
        .filter(
            models.DailyStatus.candidate_id == candidate_id
        )
        .order_by(
            models.DailyStatus.status_date.desc(),
            models.DailyStatus.id.desc()
        )
        .offset(skip)
        .limit(limit)
        .all()
    )

    return statuses


# =========================
# Update Daily Status
# =========================

@router.put(
    "/{status_id}",
    response_model=DailyStatusResponse
)
def update_daily_status(
    status_id: int,
    status_data: DailyStatusUpdate,
    db: Session = Depends(get_db)
):
    # Find existing status
    daily_status = (
        db.query(models.DailyStatus)
        .filter(
            models.DailyStatus.id == status_id
        )
        .first()
    )

    if daily_status is None:
        raise HTTPException(
            status_code=404,
            detail="Daily status not found"
        )

    # Check candidate exists
    candidate = (
        db.query(models.Candidate)
        .filter(
            models.Candidate.id == status_data.candidate_id
        )
        .first()
    )

    if candidate is None:
        raise HTTPException(
            status_code=404,
            detail="Candidate not found"
        )

    # Check duplicate candidate/date (excluding self)
    existing_status = (
        db.query(models.DailyStatus)
        .filter(
            models.DailyStatus.candidate_id
            == status_data.candidate_id,

            models.DailyStatus.status_date
            == status_data.status_date,

            models.DailyStatus.id != status_id
        )
        .first()
    )

    if existing_status:
        raise HTTPException(
            status_code=409,
            detail=(
                "Daily status already exists for this "
                "candidate on this date"
            )
        )

    # Update fields
    daily_status.candidate_id = status_data.candidate_id
    daily_status.status_date = status_data.status_date
    daily_status.work_completed = status_data.work_completed
    daily_status.topics_learned = status_data.topics_learned
    daily_status.blockers = status_data.blockers
    daily_status.next_day_plan = status_data.next_day_plan
    daily_status.completion_percentage = (
        status_data.completion_percentage
    )

    try:
        db.commit()
        db.refresh(daily_status)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail=(
                "Daily status already exists for this "
                "candidate on this date"
            )
        )

    return daily_status


# =========================
# Delete Daily Status
# =========================

@router.delete(
    "/{status_id}"
)
def delete_daily_status(
    status_id: int,
    db: Session = Depends(get_db)
):
    # Find existing status
    daily_status = (
        db.query(models.DailyStatus)
        .filter(
            models.DailyStatus.id == status_id
        )
        .first()
    )

    if daily_status is None:
        raise HTTPException(
            status_code=404,
            detail="Daily status not found"
        )

    db.delete(daily_status)

    try:
        db.commit()

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Unable to delete daily status"
        )

    return {
        "message": "Daily status deleted successfully"
    }