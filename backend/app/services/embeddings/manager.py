import time

from sentence_transformers import SentenceTransformer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import get_logger
from app.models import Email, EmailChunk

logger = get_logger("app.services.embeddings")

# Load model globally to avoid reloading
model = SentenceTransformer(settings.EMBEDDING_MODEL)


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 100) -> list[str]:
    chunks = []
    if not text:
        return chunks
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    start_time = time.perf_counter()
    embeddings = model.encode(texts)
    latency_ms = (time.perf_counter() - start_time) * 1000
    logger.info(
        f"Generated embeddings for {len(texts)} chunks in {latency_ms:.2f}ms",
        extra={"latency_ms": latency_ms, "chunk_count": len(texts)},
    )
    return embeddings.tolist()


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
            embedding=embedding,
        )
        db.add(db_chunk)

    db.commit()


def process_unembedded_emails(db: Session):
    # Find emails without chunks
    unembedded = (
        db.query(Email)
        .outerjoin(EmailChunk)
        .filter(EmailChunk.id == None)
        .limit(50)
        .all()
    )
    for email in unembedded:
        try:
            process_email_embeddings(db, email)
        except Exception as e:
            logger.error(
                f"Error embedding email {email.id}: {e}",
                exc_info=True,
                extra={"email_id": email.id},
            )
            db.rollback()
