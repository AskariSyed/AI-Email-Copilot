from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List

from app.core.database import get_db
from app.models import EmailChunk, Email, StyleProfile
from app.services.embeddings.manager import model
import os
from groq import AsyncGroq

router = APIRouter(tags=["chat"])

class ChatRequest(BaseModel):
    query: str
    account_id: int = 1 # Hardcoded for now, will update in Multi-Account phase

class ChatResponse(BaseModel):
    response: str
    sources: List[dict]

@router.post("/chat", response_model=ChatResponse)
async def chat_with_inbox(request: ChatRequest, db: Session = Depends(get_db)):
    # 1. Embed the query
    query_embedding = model.encode(request.query).tolist()
    
    # 2. Retrieve relevant context (Top 5 chunks)
    # Using L2 distance or cosine similarity
    top_chunks = (
        db.query(EmailChunk)
        .join(Email)
        # Assuming we only search this account's threads when we have account_id
        # We can add thread.gmail_account_id filter later
        .order_by(EmailChunk.embedding.cosine_distance(query_embedding))
        .limit(5)
        .all()
    )
    
    if not top_chunks:
        return {"response": "I couldn't find any relevant emails in your inbox to answer that.", "sources": []}
        
    context_text = ""
    sources = []
    
    for i, chunk in enumerate(top_chunks):
        email = chunk.email
        context_text += f"--- Email {i+1} ---\n"
        context_text += f"Date: {email.timestamp}\n"
        context_text += f"From: {email.sender}\n"
        context_text += f"Subject: {email.subject}\n"
        context_text += f"Content: {chunk.text_content}\n\n"
        
        sources.append({
            "id": email.id,
            "subject": email.subject,
            "sender": email.sender
        })
        
    # 3. Call LLM
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY not set")
        
    client = AsyncGroq(api_key=api_key)
    
    # Optional: Get style profile to know user's name
    profile = db.query(StyleProfile).filter(StyleProfile.user_id == 1).first()
    profile_instructions = profile.profile_data.get("instructions", "") if profile and profile.profile_data else ""
    
    system_prompt = (
        "You are an AI Email Assistant acting on behalf of the user. "
        "You have access to the user's email history via semantic search context. "
        "Answer the user's question directly and concisely based ONLY on the provided email context. "
        "If the answer is not in the context, say you don't know.\n\n"
        "User's AI Style Profile Instructions (if relevant): " + profile_instructions
    )
    
    user_prompt = f"Email Context:\n{context_text}\n\nQuestion: {request.query}"
    
    try:
        completion = await client.chat.completions.create(
            model=os.getenv("LLM_MODEL", "llama3-8b-8192"),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2,
            max_tokens=1000
        )
        
        answer = completion.choices[0].message.content
        return {"response": answer, "sources": sources}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM Error: {str(e)}")
