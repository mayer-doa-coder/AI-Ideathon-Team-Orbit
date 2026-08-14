"""Small helper for writing to `trace_log`, shared by any graph node.

Kept separate from the graph nodes themselves so a trace-write failure
(e.g. a transient DB blip) can never break the node's real work — logging
visibility is best-effort, not part of the graph's control flow.
"""
import logging

from app.db.models import TraceLog
from app.db.session import SessionLocal

logger = logging.getLogger(__name__)


def log_trace(
    farm_id: int | None,
    source: str,
    node_name: str,
    tool_name: str | None = None,
    params: dict | None = None,
    result: dict | None = None,
) -> None:
    db = SessionLocal()
    try:
        db.add(
            TraceLog(
                farm_id=farm_id,
                source=source,
                node_name=node_name,
                tool_name=tool_name,
                params=params,
                result=result,
            )
        )
        db.commit()
    except Exception:
        logger.exception("Failed to write trace_log entry for node=%s farm_id=%s", node_name, farm_id)
        db.rollback()
    finally:
        db.close()
