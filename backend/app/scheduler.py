"""In-process APScheduler job that sweeps every active farm through the
monitor graph on a fixed interval — no separate broker/worker service.

Each farm gets its own short-lived DB session so one farm's failure (bad
data, a transient DB hiccup) can't take down the rest of the sweep.
"""
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.agents.graph_monitor import run_monitor_sweep
from app.core.config import settings
from app.db.models import Farm
from app.db.session import SessionLocal

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()
MONITOR_JOB_ID = "monitor_sweep_all_active_farms"


def sweep_all_active_farms() -> None:
    # No more `is_active` flag on `Farm` — `user_id` is unique, so every
    # farm row that exists is by definition the account's one active farm.
    db = SessionLocal()
    try:
        farm_ids = [row.id for row in db.query(Farm.id).all()]
    finally:
        db.close()

    logger.info("Monitor sweep starting for %d active farm(s)", len(farm_ids))
    for farm_id in farm_ids:
        db = SessionLocal()
        try:
            result = run_monitor_sweep(db, farm_id)
            if result is None:
                logger.info("Skipped farm_id=%s: no committed plan yet", farm_id)
            elif result["triggered"]:
                logger.info(
                    "Monitor sweep triggered an adjustment for farm_id=%s: %s",
                    farm_id, result["trigger_reason"],
                )
        except Exception:
            logger.exception("Monitor sweep failed for farm_id=%s", farm_id)
        finally:
            db.close()


def start_scheduler() -> None:
    if scheduler.running:
        return
    scheduler.add_job(
        sweep_all_active_farms,
        trigger="interval",
        hours=settings.monitor_interval_hours,
        id=MONITOR_JOB_ID,
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Monitor scheduler started (interval=%sh)", settings.monitor_interval_hours)


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
