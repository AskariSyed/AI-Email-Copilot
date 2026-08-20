from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Draft

router = APIRouter()


class DraftResponse(BaseModel):
    id: int
    subject: str | None
    body: str
    status: str
    created_at: datetime
    original_email_id: int | None


class DraftCreate(BaseModel):
    subject: str | None = None
    body: str
    status: str = "generated"
    original_email_id: int | None = None


@router.get("", response_model=list[DraftResponse])
def get_drafts(db: Session = Depends(get_db)):
    user_id = 1
    drafts = (
        db.query(Draft)
        .filter(Draft.user_id == user_id)
        .order_by(Draft.created_at.desc())
        .all()
    )
    return drafts


@router.post("", response_model=DraftResponse)
def create_draft(draft_req: DraftCreate, db: Session = Depends(get_db)):
    user_id = 1
    draft = Draft(
        user_id=user_id,
        subject=draft_req.subject,
        body=draft_req.body,
        status=draft_req.status,
        original_email_id=draft_req.original_email_id,
    )
    db.add(draft)
    db.commit()
    db.refresh(draft)
    return draft
