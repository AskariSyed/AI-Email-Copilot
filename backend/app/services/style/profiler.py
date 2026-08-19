from openai import OpenAI
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models import StyleProfile, User, Email
import json

client = OpenAI(api_key=settings.LLM_API_KEY)

def generate_style_profile(db: Session, user_id: int):
    # Fetch some recent sent emails to analyze
    sent_emails = db.query(Email).filter(
        Email.direction == "outgoing"
    ).order_by(Email.timestamp.desc()).limit(20).all()
    
    if not sent_emails:
        return {"message": "Not enough sent emails to build a style profile."}
        
    email_texts = "\n---\n".join([e.cleaned_body for e in sent_emails if e.cleaned_body])
    
    prompt = f"""
    Analyze the following sent emails and generate a JSON style profile describing the author's writing style.
    Include fields for:
    - formality: (e.g. professional, casual, mixed)
    - verbosity: (e.g. concise, detailed)
    - greeting_style: (e.g. how they usually start emails)
    - closing_style: (e.g. how they usually end emails)
    - tone: (e.g. friendly, direct, polite)
    - uses_bullets: (boolean)
    
    Emails:
    {email_texts}
    """
    
    response = client.chat.completions.create(
        model=settings.LLM_MODEL,
        messages=[{"role": "user", "content": prompt}],
        response_format={ "type": "json_object" }
    )
    
    try:
        profile_data = json.loads(response.choices[0].message.content)
    except Exception:
        profile_data = {"error": "Failed to parse profile"}
        
    profile = db.query(StyleProfile).filter(StyleProfile.user_id == user_id).first()
    if not profile:
        profile = StyleProfile(user_id=user_id, profile_data=profile_data)
        db.add(profile)
    else:
        profile.profile_data = profile_data
        
    db.commit()
    return profile_data
