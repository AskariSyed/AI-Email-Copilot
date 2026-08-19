import os
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import Email, EmailThread, User, GmailAccount, Draft
from app.services.llm.generator import generate_email_draft
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

router = APIRouter()

class EmailResponse(BaseModel):
    id: int
    subject: Optional[str]
    sender: str
    timestamp: datetime
    snippet: Optional[str]
    direction: str

@router.get("/emails", response_model=List[EmailResponse])
def get_emails(db: Session = Depends(get_db)):
    # For MVP, just return recent emails (assuming user 1)
    emails = db.query(Email).order_by(Email.timestamp.desc()).limit(20).all()
    return emails

@router.get("/emails/{email_id}")
def get_email(email_id: int, db: Session = Depends(get_db)):
    email = db.query(Email).filter(Email.id == email_id).first()
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    return {
        "id": email.id,
        "subject": email.subject,
        "sender": email.sender,
        "timestamp": email.timestamp,
        "body": email.body,
        "cleaned_body": email.cleaned_body,
        "thread_id": email.thread_id
    }

class GenerateRequest(BaseModel):
    instructions: str = ""

@router.post("/emails/{email_id}/generate-reply")
def generate_reply(email_id: int, req: GenerateRequest, db: Session = Depends(get_db)):
    email = db.query(Email).filter(Email.id == email_id).first()
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
        
    user_id = 1 # hardcoded MVP user
    
    draft_result = generate_email_draft(
        db=db,
        user_id=user_id,
        incoming_email_text=email.cleaned_body,
        sender=email.sender,
        thread_id=email.thread_id,
        instructions=req.instructions
    )
    
    return draft_result
