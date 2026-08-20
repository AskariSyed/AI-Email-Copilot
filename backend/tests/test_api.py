from datetime import datetime, timezone

from app.models import Draft, Email, EmailThread


def test_get_emails(client, db_session):
    # Seed some emails
    thread = EmailThread(gmail_account_id=1, gmail_thread_id="t123")
    db_session.add(thread)
    db_session.commit()

    email1 = Email(
        thread_id=thread.id,
        gmail_message_id="m1",
        sender="bob@example.com",
        timestamp=datetime.now(timezone.utc),
        labels=["INBOX"],
        direction="incoming",
        subject="Test 1",
        snippet="Snippet 1",
        body="Body 1",
        cleaned_body="Body 1",
    )
    email2 = Email(
        thread_id=thread.id,
        gmail_message_id="m2",
        sender="alice@example.com",
        timestamp=datetime.now(timezone.utc),
        labels=["SENT"],  # Not in INBOX
        direction="outgoing",
        subject="Test 2",
    )
    db_session.add_all([email1, email2])
    db_session.commit()

    response = client.get("/api/v1/emails?account_id=1")
    assert response.status_code == 200
    data = response.json()

    # Only email1 should be returned because it has "INBOX" label
    assert len(data) == 1
    assert data[0]["sender"] == "bob@example.com"
    assert data[0]["subject"] == "Test 1"


def test_get_email_detail(client, db_session):
    email = db_session.query(Email).filter(Email.gmail_message_id == "m1").first()

    response = client.get(f"/api/v1/emails/{email.id}")
    assert response.status_code == 200
    data = response.json()

    assert data["body"] == "Body 1"
    assert data["cleaned_body"] == "Body 1"
    assert data["thread_id"] == email.thread_id


def test_get_email_not_found(client):
    response = client.get("/api/v1/emails/99999")
    assert response.status_code == 404


def test_save_draft(client, db_session):
    email = db_session.query(Email).filter(Email.gmail_message_id == "m1").first()

    draft_data = {
        "original_email_id": email.id,
        "subject": "Re: Test 1",
        "body": "This is a test draft.",
        "status": "edited",
    }

    response = client.post("/api/v1/drafts", json=draft_data)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] is not None
    assert data["body"] == "This is a test draft."

    # Verify in DB
    draft = db_session.query(Draft).filter(Draft.id == data["id"]).first()
    assert draft is not None
    assert draft.body == "This is a test draft."
    assert draft.status == "edited"


def test_get_drafts(client, db_session):
    response = client.get("/api/v1/drafts")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["body"] == "This is a test draft."
