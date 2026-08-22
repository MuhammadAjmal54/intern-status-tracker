# from datetime import date, datetime

# from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text
# from sqlalchemy.orm import Mapped, mapped_column

# from .database import Base


# class DailyStatus(Base):
#     __tablename__ = "daily_status"

#     id: Mapped[int] = mapped_column(
#         primary_key=True,
#         index=True
#     )

#     candidate_id: Mapped[int] = mapped_column(
#         ForeignKey("candidates.id"),
#         nullable=False,
#         index=True
#     )

#     status_date: Mapped[date] = mapped_column(
#         Date,
#         nullable=False
#     )

#     status: Mapped[str] = mapped_column(
#         String(50),
#         nullable=False
#     )

#     tasks_completed: Mapped[int] = mapped_column(
#         Integer,
#         default=0,
#         nullable=False
#     )

#     hours_worked: Mapped[int] = mapped_column(
#         Integer,
#         default=0,
#         nullable=False
#     )

#     remarks: Mapped[str | None] = mapped_column(
#         Text,
#         nullable=True
#     )

#     created_at: Mapped[datetime] = mapped_column(
#         DateTime,
#         default=datetime.utcnow,
#         nullable=False
#     )

#     updated_at: Mapped[datetime] = mapped_column(
#         DateTime,
#         default=datetime.utcnow,
#         onupdate=datetime.utcnow,
#         nullable=False
#     )