from datetime import datetime
from sqlalchemy import DateTime, Integer, String, Text, Float, Boolean, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    source: Mapped[str] = mapped_column(String(100), default="web_search")
    campaign: Mapped[str] = mapped_column(String(50), index=True)
    url: Mapped[str | None] = mapped_column(Text, nullable=True)
    occupation: Mapped[str | None] = mapped_column(String(200), nullable=True)
    assignment_location: Mapped[str | None] = mapped_column(String(300), nullable=True)
    move_in: Mapped[str | None] = mapped_column(String(50), nullable=True)
    move_out: Mapped[str | None] = mapped_column(String(50), nullable=True)
    stay_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    budget: Mapped[float | None] = mapped_column(Float, nullable=True)
    reason_for_stay: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence: Mapped[str | None] = mapped_column(Text, nullable=True)
    score: Mapped[int] = mapped_column(Integer, default=0, index=True)
    classification: Mapped[str] = mapped_column(String(30), default="LOW")
    status: Mapped[str] = mapped_column(String(30), default="NEW", index=True)
    ai_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    approved_for_contact: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class SearchRun(Base):
    __tablename__ = "search_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    campaign: Mapped[str] = mapped_column(String(50), index=True)
    query: Mapped[str] = mapped_column(Text)
    results_found: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
