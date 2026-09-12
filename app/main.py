from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from sqlalchemy.orm import Session

from .agent import run_campaign
from .config import settings
from .db import SessionLocal, init_db
from .models import Lead
from .schemas import AgentRunRequest, LeadOut

@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Agent A — Demand discovery and lead generation for a Dallas furnished rental.",
    lifespan=lifespan,
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def require_agent_key(x_agent_key: str | None):
    if not x_agent_key or x_agent_key != settings.agent_api_key:
        raise HTTPException(status_code=401, detail="Invalid agent key")


@app.get("/health")
def health():
    return {"status": "ok", "service": settings.app_name}


@app.get("/property")
def property_profile():
    from .property import PROPERTY
    return PROPERTY


@app.post("/agent/run")
async def agent_run(
    request: AgentRunRequest,
    x_agent_key: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    require_agent_key(x_agent_key)
    return await run_campaign(
        db=db,
        campaign=request.campaign,
        max_queries=request.max_queries,
    )


@app.get("/leads", response_model=list[LeadOut])
def list_leads(
    classification: str | None = Query(default=None),
    lead_type: str | None = Query(default=None),
    campaign: str | None = Query(default=None),
    status: str | None = Query(default=None),
    min_score: int | None = Query(default=None, ge=0, le=100),
    x_agent_key: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    require_agent_key(x_agent_key)

    query = db.query(Lead)
    if classification:
        query = query.filter(Lead.classification == classification)
    if lead_type:
        query = query.filter(Lead.lead_type == lead_type)
    if campaign:
        query = query.filter(Lead.campaign == campaign)
    if status:
        query = query.filter(Lead.status == status)
    if min_score is not None:
        query = query.filter(Lead.score >= min_score)

    return query.order_by(Lead.score.desc(), Lead.created_at.desc()).limit(200).all()


@app.get("/leads/hot", response_model=list[LeadOut])
def hot_leads(
    x_agent_key: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    require_agent_key(x_agent_key)
    return (
        db.query(Lead)
        .filter(Lead.score >= 90)
        .order_by(Lead.score.desc(), Lead.created_at.desc())
        .limit(100)
        .all()
    )


@app.post("/leads/{lead_id}/approve")
def approve_lead(
    lead_id: int,
    x_agent_key: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    require_agent_key(x_agent_key)
    lead = db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    lead.approved_for_contact = True
    lead.status = "CONTACTED"
    db.commit()
    return {"id": lead.id, "approved_for_contact": True, "status": lead.status}
