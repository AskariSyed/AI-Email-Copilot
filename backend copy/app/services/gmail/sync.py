from googleapiclient.discovery import build
import google.oauth2.credentials
from sqlalchemy.orm import Session
from app.models import GmailAccount, EmailThread, Email
from bs4 import BeautifulSoup
import base64
from datetime import datetime, timezone
import json

def get_gmail_service(account: GmailAccount):
    creds = google.oauth2.credentials.Credentials(
        account.access_token,
        refresh_token=account.refresh_token,
        token_uri=account.token_uri,
        client_id=account.client_id,
        client_secret=account.client_secret
    )
    return build('gmail', 'v1', credentials=creds)

def clean_html_body(html_content: str) -> str:
    soup = BeautifulSoup(html_content, "html.parser")
    # Remove script and style elements
    for script_or_style in soup(["script", "style"]):
        script_or_style.extract()
    text = soup.get_text(separator="\n")
    # Clean up empty lines
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    return '\n'.join(chunk for chunk in chunks if chunk)

def extract_body(payload: dict) -> str:
    if 'data' in payload.get('body', {}):
        return base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')
    if 'parts' in payload:
        for part in payload['parts']:
            if part['mimeType'] == 'text/plain':
                return base64.urlsafe_b64decode(part['body'].get('data', '')).decode('utf-8')
            elif part['mimeType'] == 'text/html':
                html = base64.urlsafe_b64decode(part['body'].get('data', '')).decode('utf-8')
                return clean_html_body(html)
            elif part['mimeType'] == 'multipart/alternative':
                return extract_body(part)
    return ""

def sync_emails(db: Session, account_id: int, max_results: int = 50):
    account = db.query(GmailAccount).filter(GmailAccount.id == account_id).first()
    if not account:
        raise ValueError("Account not found")
        
    service = get_gmail_service(account)
    
    # Get user profile to get email address if missing
    if not account.email_address or account.email_address == "linked_account@example.com":
        profile = service.users().getProfile(userId='me').execute()
        account.email_address = profile.get('emailAddress')
        db.commit()

    results = service.users().messages().list(userId='me', maxResults=max_results).execute()
    messages = results.get('messages', [])
    
    for msg_meta in messages:
        msg_id = msg_meta['id']
        thread_id = msg_meta['threadId']
        
        # Check if email exists
        if db.query(Email).filter(Email.gmail_message_id == msg_id).first():
            continue
            
        # Ensure thread exists
        thread = db.query(EmailThread).filter(EmailThread.gmail_thread_id == thread_id).first()
        if not thread:
            thread = EmailThread(gmail_account_id=account.id, gmail_thread_id=thread_id)
            db.add(thread)
            db.flush()
            
        # Fetch full message
        msg = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
        
        headers = {h['name'].lower(): h['value'] for h in msg['payload']['headers']}
        sender = headers.get('from', '')
        subject = headers.get('subject', '')
        date_str = headers.get('date', '')
        
        # Extract body
        raw_body = extract_body(msg['payload'])
        cleaned_body = clean_html_body(raw_body) if '<html' in raw_body.lower() else raw_body
        
        direction = "outgoing" if account.email_address in sender else "incoming"
        
        # Approximate timestamp parsing (in prod, use dateutil.parser)
        timestamp = datetime.now(timezone.utc)
        
        email_obj = Email(
            thread_id=thread.id,
            gmail_message_id=msg_id,
            sender=sender,
            recipients=headers.get('to', ''),
            cc=headers.get('cc', ''),
            bcc=headers.get('bcc', ''),
            subject=subject,
            timestamp=timestamp,
            labels=msg.get('labelIds', []),
            direction=direction,
            body=raw_body,
            cleaned_body=cleaned_body,
            snippet=msg.get('snippet', '')
        )
        db.add(email_obj)
        
    account.last_synced_at = datetime.now(timezone.utc)
    db.commit()
    return {"message": f"Synced up to {max_results} messages successfully"}
