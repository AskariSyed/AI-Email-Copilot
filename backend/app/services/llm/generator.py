from openai import OpenAI
from app.core.config import settings
from app.services.rag.retriever import retrieve_context
from sqlalchemy.orm import Session
from app.models import StyleProfile

client = OpenAI(api_key=settings.LLM_API_KEY)

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
    
    system_prompt = f"""
    You are an AI Email Copilot generating a draft reply on behalf of the user.
    Do NOT hallucinate facts, dates, names, or promises.
    
    User's Style Profile:
    {style_data}
    
    Context:
    Thread History: {context['thread_history']}
    Sender History: {context['sender_history']}
    Similar Emails: {context['similar_emails']}
    """
    
    user_prompt = f"""
    Incoming Email:
    {incoming_email_text}
    
    Specific Instructions:
    {instructions if instructions else 'Generate a polite and appropriate reply based on the context.'}
    """
    
    response = client.chat.completions.create(
        model=settings.LLM_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )
    
    return {
        "generated_body": response.choices[0].message.content,
        "context_used": {
            "thread_emails_count": len(context['thread_history']),
            "sender_emails_count": len(context['sender_history']),
            "similar_emails_count": len(context['similar_emails'])
        }
    }
