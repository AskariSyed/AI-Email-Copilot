from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import GmailAccount, User
from app.services.gmail.auth import get_auth_url, get_credentials_from_code

router = APIRouter()


class AuthUrlResponse(BaseModel):
    url: str


class AuthCallbackRequest(BaseModel):
    code: str
    # In a real app, you'd get the user from an auth token or session.
    # For MVP, we'll hardcode a dummy user ID or pass it.
    user_id: int = 1


from fastapi.responses import RedirectResponse


@router.get("/google", response_model=AuthUrlResponse)
def get_google_auth_url():
    auth_url, state = get_auth_url()
    return {"url": auth_url}


@router.get("/google/callback")
def google_auth_callback(code: str, state: str = None, db: Session = Depends(get_db)):
    try:
        credentials = get_credentials_from_code(code, state)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid code: {e!s}")

    user_id = 1

    # Ensure user exists for MVP
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        user = User(id=user_id, email="mvp_user@example.com", name="MVP User")
        db.add(user)
        db.commit()

    # Fetch profile info
    from googleapiclient.discovery import build

    service = build("oauth2", "v2", credentials=credentials)
    user_info = service.userinfo().get().execute()
    fetched_email = user_info.get("email")
    fetched_name = user_info.get("name")
    fetched_picture = user_info.get("picture")

    account = (
        db.query(GmailAccount)
        .filter(
            GmailAccount.user_id == user.id, GmailAccount.email_address == fetched_email
        )
        .first()
    )

    if not account:
        account = GmailAccount(
            user_id=user.id,
            email_address=fetched_email,
            name=fetched_name,
            picture_url=fetched_picture,
            access_token=credentials.token,
            refresh_token=credentials.refresh_token,
            token_uri=credentials.token_uri,
            client_id=credentials.client_id,
            client_secret=credentials.client_secret,
            scopes=",".join(credentials.scopes) if credentials.scopes else "",
        )
        db.add(account)
    else:
        account.access_token = credentials.token
        account.name = fetched_name
        account.picture_url = fetched_picture
        if credentials.refresh_token:
            account.refresh_token = credentials.refresh_token

    db.commit()
    return RedirectResponse("http://localhost:5173/?auth=success")


@router.get("/accounts")
def get_user_accounts(db: Session = Depends(get_db)):
    user_id = 1
    accounts = db.query(GmailAccount).filter(GmailAccount.user_id == user_id).all()

    return [
        {
            "id": a.id,
            "email_address": a.email_address,
            "name": a.name,
            "picture_url": a.picture_url,
        }
        for a in accounts
    ]


@router.get("/me")
def get_current_user_profile(db: Session = Depends(get_db)):
    user_id = 1
    # Fallback for backwards compatibility in frontend, return the first account
    account = db.query(GmailAccount).filter(GmailAccount.user_id == user_id).first()
    if not account:
        return {"connected": False}

    return {
        "connected": True,
        "email_address": account.email_address,
        "name": account.name,
        "picture_url": account.picture_url,
    }
