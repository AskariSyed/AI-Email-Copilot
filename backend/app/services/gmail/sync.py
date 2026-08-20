import base64
from datetime import datetime, timezone

import google.oauth2.credentials
from bs4 import BeautifulSoup
from googleapiclient.discovery import build
from sqlalchemy.orm import Session

from app.models import Email, EmailThread, GmailAccount


def get_gmail_service(account: GmailAccount):
    creds = google.oauth2.credentials.Credentials(
        account.access_token,
        refresh_token=account.refresh_token,
        token_uri=account.token_uri,
        client_id=account.client_id,
        client_secret=account.client_secret,
    )
    return build("gmail", "v1", credentials=creds)


def clean_html_body(html_content: str) -> str:
    soup = BeautifulSoup(html_content, "html.parser")
    # Remove script and style elements
    for script_or_style in soup(["script", "style"]):
        script_or_style.extract()
    text = soup.get_text(separator="\n")
    # Clean up empty lines
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    return "\n".join(chunk for chunk in chunks if chunk)


def extract_body(payload: dict) -> str:
    if "data" in payload.get("body", {}):
        return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8")
    if "parts" in payload:
        for part in payload["parts"]:
            if part["mimeType"] == "text/plain":
                return base64.urlsafe_b64decode(part["body"].get("data", "")).decode(
                    "utf-8"
                )
            elif part["mimeType"] == "text/html":
                html = base64.urlsafe_b64decode(part["body"].get("data", "")).decode(
                    "utf-8"
                )
                return clean_html_body(html)
            elif part["mimeType"] == "multipart/alternative":
                return extract_body(part)
    return ""


def sync_emails(db: Session, account_id: int, max_results: int = 50):
    account = db.query(GmailAccount).filter(GmailAccount.id == account_id).first()
    if not account:
        raise ValueError("Account not found")

    service = get_gmail_service(account)

    # Get user profile to get email address if missing
    if (
        not account.email_address
        or account.email_address == "linked_account@example.com"
    ):
        profile = service.users().getProfile(userId="me").execute()
        account.email_address = profile.get("emailAddress")
        db.commit()

    results = (
        service.users().messages().list(userId="me", maxResults=max_results).execute()
    )
    messages = results.get("messages", [])

    thread_cache = {}
    drafts_generated = 0

    for msg_meta in messages:
        msg_id = msg_meta["id"]
        thread_id = msg_meta["threadId"]

        # Check if email exists
        if db.query(Email).filter(Email.gmail_message_id == msg_id).first():
            continue

        # Ensure thread exists
        if thread_id in thread_cache:
            thread = thread_cache[thread_id]
        else:
            thread = (
                db.query(EmailThread)
                .filter(EmailThread.gmail_thread_id == thread_id)
                .first()
            )
            if not thread:
                import sqlalchemy

                try:
                    with db.begin_nested():
                        thread = EmailThread(
                            gmail_account_id=account.id, gmail_thread_id=thread_id
                        )
                        db.add(thread)
                        db.flush()
                except sqlalchemy.exc.IntegrityError:
                    # Caught a unique constraint violation, meaning it was just created concurrently
                    thread = (
                        db.query(EmailThread)
                        .filter(EmailThread.gmail_thread_id == thread_id)
                        .first()
                    )
            thread_cache[thread_id] = thread

        # Fetch full message
        msg = (
            service.users()
            .messages()
            .get(userId="me", id=msg_id, format="full")
            .execute()
        )

        headers = {h["name"].lower(): h["value"] for h in msg["payload"]["headers"]}
        sender = headers.get("from", "")
        subject = headers.get("subject", "")
        reply_to = headers.get("reply-to", None)
        references = headers.get("references", None)

        # Extract body
        raw_body = extract_body(msg["payload"])
        cleaned_body = (
            clean_html_body(raw_body) if "<html" in raw_body.lower() else raw_body
        )

        direction = "outgoing" if account.email_address in sender else "incoming"

        # Extract true timestamp from Gmail's internalDate (epoch in ms)
        internal_date = int(msg.get("internalDate", 0))
        if internal_date > 0:
            timestamp = datetime.fromtimestamp(internal_date / 1000.0, tz=timezone.utc)
        else:
            timestamp = datetime.now(timezone.utc)

        email_obj = Email(
            thread_id=thread.id,
            gmail_message_id=msg_id,
            sender=sender,
            recipients=headers.get("to", ""),
            cc=headers.get("cc", ""),
            bcc=headers.get("bcc", ""),
            subject=subject,
            timestamp=timestamp,
            labels=msg.get("labelIds", []),
            direction=direction,
            body=raw_body,
            cleaned_body=cleaned_body,
            snippet=msg.get("snippet", ""),
            reply_to=reply_to,
            references=references,
        )
        db.add(email_obj)
        db.flush()

        # Now chunk it and generate embeddings!
        from app.services.embeddings.manager import process_email_embeddings

        process_email_embeddings(db, email_obj)

        # Auto-Drafting Logic
        # Only auto-draft recent emails (last 24 hours) and limit to top 10 per sync to avoid rate limits
        from datetime import timedelta

        if (
            direction == "incoming"
            and "INBOX" in (email_obj.labels or [])
            and drafts_generated < 10
            and (datetime.now(timezone.utc) - timestamp < timedelta(days=1))
        ):
            drafts_generated += 1
            from app.core.database import SessionLocal
            from app.core.scheduler import scheduler
            from app.models import Draft
            from app.services.llm.generator import generate_email_draft

            def background_draft(email_id: int):
                bg_db = SessionLocal()
                try:
                    email = bg_db.query(Email).filter(Email.id == email_id).first()
                    if not email:
                        return

                    result = generate_email_draft(
                        db=bg_db,
                        user_id=1,
                        incoming_email_text=email.cleaned_body,
                        sender=email.sender,
                        thread_id=email.thread_id,
                        instructions="",
                    )

                    draft = Draft(
                        user_id=1,
                        original_email_id=email_id,
                        subject=f"Re: {email.subject}",
                        body=result["generated_body"],
                        status="generated",
                    )
                    bg_db.add(draft)
                    bg_db.commit()
                except Exception as e:
                    import logging

                    logging.error(f"Auto-drafting failed for email {email_id}: {e}")
                finally:
                    bg_db.close()

            if scheduler.running:
                scheduler.add_job(background_draft, args=[email_obj.id])

    account.last_synced_at = datetime.now(timezone.utc)
    db.commit()
    return {"message": f"Synced up to {max_results} messages successfully"}
