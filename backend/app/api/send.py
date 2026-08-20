import base64
from email.message import EmailMessage

from fastapi import APIRouter, Depends, HTTPException
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Draft, Email

router = APIRouter(tags=["emails"])


class SendEmailRequest(BaseModel):
    draft_id: int | None = None
    body: str


@router.post("/{email_id}/send")
def send_email_reply(
    email_id: int, request: SendEmailRequest, db: Session = Depends(get_db)
):
    original_email = db.query(Email).filter(Email.id == email_id).first()
    if not original_email:
        raise HTTPException(status_code=404, detail="Original email not found")

    thread = original_email.thread
    account = thread.gmail_account

    # Rebuild credentials
    creds = Credentials(
        token=account.access_token,
        refresh_token=account.refresh_token,
        token_uri=account.token_uri,
        client_id=account.client_id,
        client_secret=account.client_secret,
    )

    try:
        service = build("gmail", "v1", credentials=creds)

        message = EmailMessage()
        message.set_content(request.body)

        # We reply to the original sender
        # If it was sent by us, maybe we are following up?
        # Typically we reply to the 'sender' of the incoming message.
        # It's safest to rely on the 'reply_to' if it exists, otherwise 'sender'.
        message["To"] = (
            original_email.reply_to
            if original_email.reply_to
            else original_email.sender
        )

        # Ensure subject has "Re: " if not already
        subject = original_email.subject or ""
        if not subject.lower().startswith("re:"):
            subject = f"Re: {subject}"
        message["Subject"] = subject

        # Important headers for threading
        if original_email.gmail_message_id:
            message["In-Reply-To"] = original_email.gmail_message_id

            # Combine existing references with the new message ID
            refs = original_email.references or ""
            new_refs = f"{refs} {original_email.gmail_message_id}".strip()
            message["References"] = new_refs

        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

        create_message = {"raw": encoded_message, "threadId": thread.gmail_thread_id}

        send_message = (
            service.users().messages().send(userId="me", body=create_message).execute()
        )

        if request.draft_id:
            draft = db.query(Draft).filter(Draft.id == request.draft_id).first()
            if draft:
                draft.status = "sent"
                db.commit()

        return {"message": "Email sent successfully", "id": send_message["id"]}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
