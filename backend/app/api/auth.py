from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.gmail.auth import get_auth_url, get_credentials_from_code
from app.models import User, GmailAccount
from pydantic import BaseModel

router = APIRouter()

class AuthUrlResponse(BaseModel):
    url: str

class AuthCallbackRequest(BaseModel):
    code: str
    # In a real app, you'd get the user from an auth token or session. 
    # For MVP, we'll hardcode a dummy user ID or pass it.
    user_id: int = 1

@router.get("/google", response_model=AuthUrlResponse)
def get_google_auth_url():
    auth_url, state = get_auth_url()
    return {"url": auth_url}

@router.post("/google/callback")
def google_auth_callback(request: AuthCallbackRequest, db: Session = Depends(get_db)):
    try:
        credentials = get_credentials_from_code(request.code)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid code: {str(e)}")
        
    # Ensure user exists for MVP
    user = db.query(User).filter(User.id == request.user_id).first()
    if not user:
        user = User(id=request.user_id, email="mvp_user@example.com", name="MVP User")
        db.add(user)
        db.commit()
        
    account = db.query(GmailAccount).filter(GmailAccount.user_id == user.id).first()
    if not account:
        account = GmailAccount(
            user_id=user.id,
            email_address="linked_account@example.com", # Needs real email fetched via API
            access_token=credentials.token,
            refresh_token=credentials.refresh_token,
            token_uri=credentials.token_uri,
            client_id=credentials.client_id,
            client_secret=credentials.client_secret,
            scopes=",".join(credentials.scopes) if credentials.scopes else ""
        )
        db.add(account)
    else:
        account.access_token = credentials.token
        if credentials.refresh_token:
            account.refresh_token = credentials.refresh_token
            
    db.commit()
    return {"message": "Authentication successful"}
