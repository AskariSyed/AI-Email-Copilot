from sqlalchemy import desc, or_
from sqlalchemy.orm import Session

from app.models import Email, EmailChunk, EmailThread
from app.services.embeddings.manager import embed_texts


def retrieve_context(
    db: Session,
    incoming_email_text: str,
    sender: str,
    thread_id: int = None,
    limit: int = 5,
):
    context_data = {"thread_history": [], "sender_history": [], "similar_emails": []}

    # 1. Thread History
    if thread_id:
        thread_emails = (
            db.query(Email)
            .filter(Email.thread_id == thread_id)
            .order_by(Email.timestamp.asc())
            .all()
        )
        context_data["thread_history"] = [
            f"From: {e.sender}\nDate: {e.timestamp}\n{e.cleaned_body}"
            for e in thread_emails
        ]

    # 2. Sender History
    if sender:
        sender_emails = (
            db.query(Email)
            .filter(
                or_(
                    Email.sender.ilike(f"%{sender}%"),
                    Email.recipients.ilike(f"%{sender}%"),
                )
            )
            .order_by(desc(Email.timestamp))
            .limit(5)
            .all()
        )

        context_data["sender_history"] = [
            f"From: {e.sender}\nTo: {e.recipients}\nDate: {e.timestamp}\n{e.cleaned_body}"
            for e in sender_emails
            if e.thread_id != thread_id
        ]

    # 3. Semantic Similar Emails
    if incoming_email_text:
        import time

        from app.core.config import settings
        from app.core.logging import get_logger
        from app.services.rag.reranker import rerank_documents

        logger = get_logger("app.services.rag.retriever")

        class ThreadDocument:
            def __init__(self, thread_id, subject, messages):
                self.thread_id = thread_id
                self.subject = subject
                self.messages = messages

            def get_text(self):
                text = f"Thread Subject: {self.subject}\n\n"
                for msg in self.messages:
                    text += f"From: {msg.sender}\nDate: {msg.timestamp}\n{msg.cleaned_body}\n---\n"
                return text

        def reconstruct_threads(chunks):
            thread_map = {}
            for chunk in chunks:
                t_id = chunk.email.thread_id
                if t_id not in thread_map:
                    thread_map[t_id] = True

            thread_docs = []
            for t_id in thread_map:
                # Avoid fetching the active thread
                if t_id == thread_id:
                    continue
                thread = db.query(EmailThread).filter(EmailThread.id == t_id).first()
                if thread:
                    emails = (
                        db.query(Email)
                        .filter(Email.thread_id == t_id)
                        .order_by(Email.timestamp.asc())
                        .all()
                    )
                    thread_docs.append(ThreadDocument(t_id, thread.subject, emails))
            return thread_docs

        query_embedding = embed_texts([incoming_email_text])[0]

        candidate_limit = (
            settings.RERANK_CANDIDATE_COUNT if settings.ENABLE_RERANKING else limit
        )

        start_time = time.perf_counter()
        candidate_chunks = (
            db.query(EmailChunk)
            .order_by(EmailChunk.embedding.cosine_distance(query_embedding))
            .limit(candidate_limit)
            .all()
        )
        retrieval_latency = (time.perf_counter() - start_time) * 1000
        logger.info(
            f"Vector retrieval of {len(candidate_chunks)} chunks took {retrieval_latency:.2f}ms",
            extra={"latency_ms": retrieval_latency, "chunk_count": len(candidate_chunks)}
        )

        # Thread Reconstruction
        thread_candidates = reconstruct_threads(candidate_chunks)

        # Extract text function for the reranker
        def extract_text(thread_doc):
            return thread_doc.get_text()

        final_limit = (
            settings.RERANK_FINAL_COUNT if settings.ENABLE_RERANKING else limit
        )
        final_threads = rerank_documents(
            incoming_email_text, thread_candidates, extract_text, top_k=final_limit
        )

        for t_doc in final_threads:
            context_data["similar_emails"].append(t_doc.get_text())

    return context_data
