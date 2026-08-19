from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from app.core.database import SessionLocal
from app.services.gmail.sync import sync_emails
from app.models import GmailAccount
import logging

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()

def scheduled_sync():
    """Background job that runs every 5 minutes to sync emails for all accounts."""
    db = SessionLocal()
    try:
        accounts = db.query(GmailAccount).all()
        for account in accounts:
            logger.info(f"Background Sync: Starting sync for account {account.email_address}")
            try:
                sync_emails(db, account.id, max_results=50) # Fetch fewer in background
            except Exception as e:
                logger.error(f"Background Sync failed for account {account.email_address}: {e}")
    finally:
        db.close()

def start_scheduler():
    if not scheduler.running:
        scheduler.add_job(
            scheduled_sync,
            trigger=IntervalTrigger(minutes=5),
            id="sync_emails_job",
            name="Sync Gmail Emails every 5 minutes",
            replace_existing=True,
        )
        scheduler.start()
        logger.info("Background scheduler started.")

def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Background scheduler stopped.")
