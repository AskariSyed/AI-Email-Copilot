import base64
from unittest.mock import MagicMock, patch

from app.services.gmail.sync import clean_html_body, sync_emails


def test_clean_html_body():
    html = "<html><body><p>Hello  World</p><script>alert('bad');</script></body></html>"
    cleaned = clean_html_body(html)
    assert "Hello" in cleaned
    assert "World" in cleaned
    assert "script" not in cleaned
    assert "bad" not in cleaned


@patch("app.services.gmail.sync.get_gmail_service")
@patch("app.services.embeddings.manager.process_email_embeddings")
def test_sync_emails(mock_process, mock_get_service, db_session):
    # Mock Gmail API Service
    mock_service = MagicMock()
    mock_get_service.return_value = mock_service

    # Mock Profile
    mock_profile = MagicMock()
    mock_profile.execute.return_value = {"emailAddress": "test@example.com"}
    mock_service.users().getProfile.return_value = mock_profile

    # Mock message list
    mock_list = MagicMock()
    mock_list.execute.return_value = {
        "messages": [{"id": "msg1", "threadId": "thread1"}]
    }
    mock_service.users().messages().list.return_value = mock_list

    # Mock message payload
    mock_get = MagicMock()

    # Create fake base64 body
    fake_body = base64.urlsafe_b64encode(b"This is the email body").decode("utf-8")

    mock_get.execute.return_value = {
        "id": "msg1",
        "threadId": "thread1",
        "labelIds": ["INBOX"],
        "snippet": "Test snippet",
        "internalDate": "1672531200000",  # Jan 1 2023
        "payload": {
            "headers": [
                {"name": "From", "value": "sender@example.com"},
                {"name": "Subject", "value": "Test Subject"},
                {"name": "To", "value": "test@example.com"},
            ],
            "body": {"data": fake_body},
        },
    }
    mock_service.users().messages().get.return_value = mock_get

    # Execute sync
    result = sync_emails(db_session, 1, max_results=1)

    assert "Synced up to 1 messages" in result["message"]

    # Verify DB insertion
    from app.models import Email, EmailThread

    email = db_session.query(Email).filter(Email.gmail_message_id == "msg1").first()
    assert email is not None
    assert email.subject == "Test Subject"
    assert email.sender == "sender@example.com"
    assert email.direction == "incoming"
    assert email.body == "This is the email body"
    assert email.cleaned_body == "This is the email body"

    thread = (
        db_session.query(EmailThread)
        .filter(EmailThread.gmail_thread_id == "thread1")
        .first()
    )
    assert thread is not None
    assert email.thread_id == thread.id

    # Ensure embedding process was called
    mock_process.assert_called_once()
