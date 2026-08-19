from app.core.database import SessionLocal
from app.models import Email, EmailThread, Draft, EmailChunk

def reset_db():
    db = SessionLocal()
    db.query(Draft).delete()
    db.query(EmailChunk).delete()
    db.query(Email).delete()
    db.query(EmailThread).delete()
    db.commit()
    print("Database cleared of emails and threads.")

if __name__ == "__main__":
    reset_db()
