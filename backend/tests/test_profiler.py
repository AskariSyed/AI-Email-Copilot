from unittest.mock import MagicMock, patch

from app.services.llm.profiler import infer_user_profile


def test_effective_profile_merging():
    # Simulate the logic in generator.py
    style_data = {
        "inferred": {"formality": "Casual", "greeting_style": "Hey,"},
        "manual": {"formality": "Highly Professional", "instructions": "Be brief."},
    }

    inferred = style_data.get("inferred", {})
    manual = style_data.get("manual", {})

    effective_profile = {**inferred, **manual}

    # Manual should override inferred
    assert effective_profile["formality"] == "Highly Professional"
    assert effective_profile["greeting_style"] == "Hey,"
    assert effective_profile["instructions"] == "Be brief."


def test_effective_profile_legacy():
    # Simulate a user who only has the old flat JSON format
    style_data = {"instructions": "legacy instructions"}

    inferred = style_data.get("inferred", {})
    manual = style_data.get("manual", {})

    if "inferred" not in style_data and "manual" not in style_data:
        manual = style_data

    effective_profile = {**inferred, **manual}
    assert effective_profile["instructions"] == "legacy instructions"


@patch("app.services.llm.profiler.client")
def test_infer_user_profile(mock_client):
    # Mocking the DB and OpenAI response
    mock_db = MagicMock()

    # Mock user query
    mock_user = MagicMock()
    mock_user.id = 1
    mock_db.query().filter().first.side_effect = [
        mock_user,  # User query
        None,  # StyleProfile query (simulate no existing profile)
    ]

    # Mock emails query
    mock_email1 = MagicMock()
    mock_email1.cleaned_body = "Hi, let's meet tomorrow. Best, User."
    mock_email2 = MagicMock()
    mock_email2.cleaned_body = "Sounds good. Best, User."
    mock_db.query().filter().order_by().limit().all.return_value = [
        mock_email1,
        mock_email2,
    ]

    # Mock OpenAI response
    mock_response = MagicMock()
    mock_response.choices[
        0
    ].message.content = '{"formality": "Casual", "tone": "Friendly"}'
    mock_client.chat.completions.create.return_value = mock_response

    result = infer_user_profile(mock_db, 1)

    assert "inferred" in result
    assert result["inferred"]["formality"] == "Casual"
    assert result["inferred"]["tone"] == "Friendly"
    assert result["emails_analyzed"] == 2
    assert "last_inferred_at" in result
