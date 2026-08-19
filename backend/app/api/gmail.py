from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.gmail.sync import sync_emails

from app.models import GmailAccount

router = APIRouter()

from typing import Optional

@router.post("/sync")
def trigger_sync(account_id: Optional[int] = None, db: Session = Depends(get_db)):
    user_id = 1 # MVP hardcoded user
    
    if account_id:
        account = db.query(GmailAccount).filter(GmailAccount.id == account_id, GmailAccount.user_id == user_id).first()
    else:
        account = db.query(GmailAccount).filter(GmailAccount.user_id == user_id).first()
        
    if not account:
        raise HTTPException(status_code=400, detail="Account not linked")
        
    try:
        sync_emails(db, account_id=account.id, max_results=500) # fetch up to 500 emails
        return {"message": "Sync successful", "emails_synced": 500}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
