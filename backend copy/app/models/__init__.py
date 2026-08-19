from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from datetime import datetime, timezone
from app.core.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    gmail_account = relationship("GmailAccount", back_populates="user", uselist=False)

class GmailAccount(Base):
    __tablename__ = "gmail_accounts"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    email_address = Column(String, unique=True, index=True)
    access_token = Column(String, nullable=True)
    refresh_token = Column(String, nullable=True)
    token_uri = Column(String, nullable=True)
    client_id = Column(String, nullable=True)
    client_secret = Column(String, nullable=True)
    scopes = Column(String, nullable=True)
    history_id = Column(String, nullable=True)
    last_synced_at = Column(DateTime, nullable=True)
    
    user = relationship("User", back_populates="gmail_account")
    threads = relationship("EmailThread", back_populates="gmail_account")

class EmailThread(Base):
    __tablename__ = "email_threads"
    id = Column(Integer, primary_key=True, index=True)
    gmail_account_id = Column(Integer, ForeignKey("gmail_accounts.id"))
    gmail_thread_id = Column(String, unique=True, index=True)
    subject = Column(String, nullable=True)
    last_message_date = Column(DateTime, nullable=True)
    
    gmail_account = relationship("GmailAccount", back_populates="threads")
    emails = relationship("Email", back_populates="thread")

class Email(Base):
    __tablename__ = "emails"
    id = Column(Integer, primary_key=True, index=True)
    thread_id = Column(Integer, ForeignKey("email_threads.id"))
    gmail_message_id = Column(String, unique=True, index=True)
    sender = Column(String, index=True)
    recipients = Column(String)  # JSON or comma-separated
    cc = Column(String, nullable=True)
    bcc = Column(String, nullable=True)
    subject = Column(String, nullable=True)
    timestamp = Column(DateTime, index=True)
    labels = Column(JSON, nullable=True) # JSON array of labels like ["INBOX", "SENT"]
    direction = Column(String) # "incoming" or "outgoing"
    body = Column(Text, nullable=True)
    cleaned_body = Column(Text, nullable=True)
    snippet = Column(Text, nullable=True)
    references = Column(Text, nullable=True)
    reply_to = Column(String, nullable=True)
    
    thread = relationship("EmailThread", back_populates="emails")
    chunks = relationship("EmailChunk", back_populates="email")

class EmailChunk(Base):
    __tablename__ = "email_chunks"
    id = Column(Integer, primary_key=True, index=True)
    email_id = Column(Integer, ForeignKey("emails.id"))
    chunk_index = Column(Integer)
    text_content = Column(Text)
    embedding = Column(Vector(1536)) # Assuming text-embedding-3-small (1536 dims)
    
    email = relationship("Email", back_populates="chunks")

class Draft(Base):
    __tablename__ = "drafts"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    original_email_id = Column(Integer, ForeignKey("emails.id"), nullable=True)
    subject = Column(String, nullable=True)
    body = Column(Text)
    status = Column(String) # "generated", "edited", "sent"
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    user = relationship("User")
    original_email = relationship("Email")

class StyleProfile(Base):
    __tablename__ = "style_profiles"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    profile_data = Column(JSON) # e.g. {"formality": "...", "tone": "..."}
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    user = relationship("User")
