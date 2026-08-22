from datetime import datetime, date

from sqlalchemy import (
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Date,
    Text,
    Integer,
    Float,
    UniqueConstraint,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from .database import Base


class Candidate(Base):
    __tablename__ = "candidates"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    full_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True
    )

    training_track: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    statuses: Mapped[list["DailyStatus"]] = relationship(
        "DailyStatus",
        back_populates="candidate",
        cascade="all, delete-orphan"
    )


class DailyStatus(Base):
    __tablename__ = "daily_status"

    __table_args__ = (
        UniqueConstraint(
            "candidate_id",
            "status_date",
            name="uq_candidate_status_date"
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    candidate_id: Mapped[int] = mapped_column(
        ForeignKey(
            "candidates.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    status_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True
    )

    work_completed: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    topics_learned: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    blockers: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    next_day_plan: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    completion_percentage: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    candidate: Mapped["Candidate"] = relationship(
        back_populates="statuses"
    )

