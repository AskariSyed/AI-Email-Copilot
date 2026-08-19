from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import Draft
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

router = APIRouter()

class DraftResponse(BaseModel):
    id: int
    subject: Optional[str]
    body: str
    status: str
    created_at: datetime
    original_email_id: Optional[int]

class DraftCreate(BaseModel):
    subject: Optional[str] = None
    body: str
    status: str = "generated"
    original_email_id: Optional[int] = None

@router.get("", response_model=List[DraftResponse])
def get_drafts(db: Session = Depends(get_db)):
    user_id = 1
    drafts = db.query(Draft).filter(Draft.user_id == user_id).order_by(Draft.created_at.desc()).all()
    return drafts

@router.post("", response_model=DraftResponse)
def create_draft(draft_req: DraftCreate, db: Session = Depends(get_db)):
    user_id = 1
    draft = Draft(
        user_id=user_id,
        subject=draft_req.subject,
        body=draft_req.body,
        status=draft_req.status,
        original_email_id=draft_req.original_email_id
    )
    db.add(draft)
    db.commit()
    db.refresh(draft)
    return draft
