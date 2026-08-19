from sqlalchemy.orm import Session
from sqlalchemy import select, or_, desc
from app.models import Email, EmailChunk, EmailThread
from app.services.embeddings.manager import embed_texts

def retrieve_context(db: Session, incoming_email_text: str, sender: str, thread_id: int = None, limit: int = 5):
    context_data = {
        "thread_history": [],
        "sender_history": [],
        "similar_emails": []
    }
    
    # 1. Thread History
    if thread_id:
        thread_emails = db.query(Email).filter(Email.thread_id == thread_id).order_by(Email.timestamp.asc()).all()
        context_data["thread_history"] = [
            f"From: {e.sender}\nDate: {e.timestamp}\n{e.cleaned_body}" for e in thread_emails
        ]
        
    # 2. Sender History
    if sender:
        sender_emails = db.query(Email).filter(
            or_(Email.sender.ilike(f"%{sender}%"), Email.recipients.ilike(f"%{sender}%"))
        ).order_by(desc(Email.timestamp)).limit(5).all()
        
        context_data["sender_history"] = [
            f"From: {e.sender}\nTo: {e.recipients}\nDate: {e.timestamp}\n{e.cleaned_body}" 
            for e in sender_emails if e.thread_id != thread_id
        ]
        
    # 3. Semantic Similar Emails
    if incoming_email_text:
        query_embedding = embed_texts([incoming_email_text])[0]
        
        # pgvector cosine distance: <-> 
        # For inner product: <#>
        # For L2 distance: <->
        results = db.query(EmailChunk).order_by(EmailChunk.embedding.cosine_distance(query_embedding)).limit(limit).all()
        
        for chunk in results:
            if chunk.email.thread_id != thread_id: # avoid duplicating thread history
                context_data["similar_emails"].append(
                    f"Subject: {chunk.email.subject}\nFrom: {chunk.email.sender}\nMatch: {chunk.text_content}"
                )
                
    return context_data
