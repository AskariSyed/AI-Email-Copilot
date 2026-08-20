import json
import logging
from datetime import datetime, timezone

from openai import OpenAI
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import Email, StyleProfile, User

logger = logging.getLogger(__name__)

# Initialize client lazily or globally
try:
    client = OpenAI(api_key=settings.LLM_API_KEY, base_url=settings.LLM_BASE_URL)
except Exception as e:
    logger.warning(f"Failed to initialize OpenAI client for profiler: {e}")
    client = None


def infer_user_profile(db: Session, user_id: int):
    """
    Infers the user's communication style by analyzing their recent outgoing emails.
    Stores the result in StyleProfile.profile_data['inferred'].
    """
    if not client:
        raise ValueError("LLM client not configured. Cannot infer profile.")

    # Fetch user to ensure they exist
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValueError("User not found")

    # Fetch outgoing emails
    outgoing_emails = (
        db.query(Email)
        .filter(Email.direction == "outgoing")
        .order_by(desc(Email.timestamp))
        .limit(30)
        .all()
    )

    if len(outgoing_emails) < 2:
        raise ValueError(
            "Not enough outgoing emails to infer a profile. Need at least 2."
        )

    # Concatenate emails
    email_texts = "\n\n---\n\n".join(
        [e.cleaned_body for e in outgoing_emails if e.cleaned_body]
    )
    # Truncate to save tokens (approx 15k chars is safe for most models)
    email_texts = email_texts[:15000]

    prompt = f"""
    You are an expert communication analyst. Analyze the following outgoing emails sent by a user and infer their communication style.
    Do NOT include any private information, names, or specific email content in your output. Only abstract traits.
    
    Evaluate the following traits:
    - formality (e.g. "Highly formal", "Casual", "Professional but relaxed")
    - conciseness (e.g. "Very concise", "Verbose", "Balanced")
    - typical_response_length (e.g. "1-2 sentences", "Multiple paragraphs")
    - greeting_style (e.g. "Hi [Name],", "No greeting", "Dear [Name],")
    - closing_style (e.g. "Best,", "Thanks,", "Cheers,")
    - emoji_usage (e.g. "None", "Occasional smileys", "Frequent")
    - directness (e.g. "Direct and to the point", "Polite and conversational")
    - preferred_formatting (e.g. "Paragraphs", "Bullet points", "Single block of text")
    - tone (e.g. "Friendly", "Authoritative", "Neutral")
    
    Respond STRICTLY in JSON format with exactly these keys:
    {{
        "formality": "",
        "conciseness": "",
        "typical_response_length": "",
        "greeting_style": "",
        "closing_style": "",
        "emoji_usage": "",
        "directness": "",
        "preferred_formatting": "",
        "tone": ""
    }}
    
    Emails to analyze:
    {email_texts}
    """

    completion = client.chat.completions.create(
        model=settings.LLM_MODEL,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )

    inferred_data = json.loads(completion.choices[0].message.content)

    # Save to profile
    profile = db.query(StyleProfile).filter(StyleProfile.user_id == user_id).first()
    if not profile:
        profile = StyleProfile(user_id=user_id, profile_data={"manual": {}})
        db.add(profile)

    current_data = profile.profile_data or {"manual": {}}

    current_data["inferred"] = inferred_data
    current_data["last_inferred_at"] = datetime.now(timezone.utc).isoformat()
    current_data["emails_analyzed"] = len(outgoing_emails)

    # SQLAlchemy requires a new object assignment or flag_modified to detect JSON mutations
    profile.profile_data = current_data.copy()
    db.commit()

    return current_data
