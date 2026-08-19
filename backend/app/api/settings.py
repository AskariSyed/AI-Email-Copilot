from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import StyleProfile
from pydantic import BaseModel
from typing import Dict, Any

router = APIRouter()

class SettingsUpdate(BaseModel):
    profile_data: Dict[str, Any]

@router.get("")
def get_settings(db: Session = Depends(get_db)):
    user_id = 1
    profile = db.query(StyleProfile).filter(StyleProfile.user_id == user_id).first()
    if not profile:
        return {"profile_data": {}}
    return {"profile_data": profile.profile_data}

@router.post("")
def update_settings(req: SettingsUpdate, db: Session = Depends(get_db)):
    user_id = 1
    profile = db.query(StyleProfile).filter(StyleProfile.user_id == user_id).first()
    if not profile:
        profile = StyleProfile(user_id=user_id, profile_data=req.profile_data)
        db.add(profile)
    else:
        profile.profile_data = req.profile_data
        
    db.commit()
    db.refresh(profile)
    return {"profile_data": profile.profile_data}
