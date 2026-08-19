from openai import OpenAI
from sqlalchemy.orm import Session
from app.models import Email, EmailChunk
from app.core.config import settings

client = OpenAI(api_key=settings.EMBEDDING_API_KEY)

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 100) -> list[str]:
    chunks = []
    if not text:
        return chunks
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end])
        start += (chunk_size - overlap)
    return chunks

def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    response = client.embeddings.create(
        input=texts,
        model=settings.EMBEDDING_MODEL
    )
    return [data.embedding for data in response.data]

def process_email_embeddings(db: Session, email: Email):
    # Skip if already chunked
    if db.query(EmailChunk).filter(EmailChunk.email_id == email.id).first():
        return
        
    text_to_embed = f"Subject: {email.subject}\nFrom: {email.sender}\nTo: {email.recipients}\n\n{email.cleaned_body}"
    chunks = chunk_text(text_to_embed)
    
    if not chunks:
        return
        
    embeddings = embed_texts(chunks)
    
    for i, (chunk_text_content, embedding) in enumerate(zip(chunks, embeddings)):
        db_chunk = EmailChunk(
            email_id=email.id,
            chunk_index=i,
            text_content=chunk_text_content,
            embedding=embedding
        )
        db.add(db_chunk)
    
    db.commit()

def process_unembedded_emails(db: Session):
    # Find emails without chunks
    unembedded = db.query(Email).outerjoin(EmailChunk).filter(EmailChunk.id == None).limit(50).all()
    for email in unembedded:
        try:
            process_email_embeddings(db, email)
        except Exception as e:
            print(f"Error embedding email {email.id}: {e}")
            db.rollback()
