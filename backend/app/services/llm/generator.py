from openai import OpenAI
from app.core.config import settings
from app.services.rag.retriever import retrieve_context
from sqlalchemy.orm import Session
from app.models import StyleProfile

client = OpenAI(
    api_key=settings.LLM_API_KEY,
    base_url=settings.LLM_BASE_URL
)

def generate_email_draft(
    db: Session, 
    user_id: int, 
    incoming_email_text: str, 
    sender: str, 
    thread_id: int = None, 
    instructions: str = ""
):
    context = retrieve_context(db, incoming_email_text, sender, thread_id)
    
    style_profile_obj = db.query(StyleProfile).filter(StyleProfile.user_id == user_id).first()
    style_data = style_profile_obj.profile_data if style_profile_obj else {}
    
    # Truncate strings to prevent huge prompts exceeding token limits
    safe_thread_history = str(context['thread_history'])[:1500]
    safe_sender_history = str(context['sender_history'])[:1500]
    safe_similar = str(context['similar_emails'])[:1500]
    safe_incoming = incoming_email_text[:3000] if incoming_email_text else ""

    system_prompt = f"""
    You are an AI Email Copilot generating a draft reply on behalf of the user.
    Do NOT hallucinate facts, dates, names, or promises.
    
    User's Style Profile:
    {style_data}
    
    Context:
    Thread History: {safe_thread_history}
    Sender History: {safe_sender_history}
    Similar Emails: {safe_similar}
    """
    
    user_prompt = f"""
    Incoming Email:
    {safe_incoming}
    
    Specific Instructions:
    {instructions if instructions else 'Generate a polite and appropriate reply based on the context.'}
    """
    
    import time
    import random
    
    max_retries = 5
    response = None
    
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
            break
        except Exception as e:
            if "429" in str(e) or "rate_limit" in str(e).lower():
                if attempt < max_retries - 1:
                    sleep_time = (2 ** attempt) * 5 + random.uniform(1, 5) # 5s, 10s, 20s, 40s
                    print(f"Rate limited. Sleeping for {sleep_time:.2f} seconds before retry {attempt + 1}/{max_retries}...")
                    time.sleep(sleep_time)
                else:
                    raise e
            else:
                raise e
    
    return {
        "generated_body": response.choices[0].message.content,
        "context_used": {
            "thread_emails_count": len(context['thread_history']),
            "sender_emails_count": len(context['sender_history']),
            "similar_emails_count": len(context['similar_emails'])
        }
    }
