from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import String, cast
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Email, EmailThread
from app.services.llm.generator import generate_email_draft

router = APIRouter()


class EmailResponse(BaseModel):
    id: int
    subject: str | None
    sender: str
    timestamp: datetime
    snippet: str | None
    direction: str


@router.get("", response_model=list[EmailResponse])
def get_emails(
    skip: int = 0,
    limit: int = 20,
    account_id: int | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(Email).join(EmailThread)
    if account_id:
        query = query.filter(EmailThread.gmail_account_id == account_id)

    emails = (
        query.filter(cast(Email.labels, String).ilike('%"INBOX"%'))
        .order_by(Email.timestamp.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return emails


@router.get("/{email_id}")
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
        "thread_id": email.thread_id,
    }


class GenerateRequest(BaseModel):
    instructions: str = ""


@router.post("/{email_id}/generate-reply")
def generate_reply(email_id: int, req: GenerateRequest, db: Session = Depends(get_db)):
    email = db.query(Email).filter(Email.id == email_id).first()
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")

    user_id = 1  # hardcoded MVP user

    draft_result = generate_email_draft(
        db=db,
        user_id=user_id,
        incoming_email_text=email.cleaned_body,
        sender=email.sender,
        thread_id=email.thread_id,
        instructions=req.instructions,
    )

    return draft_result
