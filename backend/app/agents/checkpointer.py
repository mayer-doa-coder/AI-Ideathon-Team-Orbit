"""LangGraph's Postgres checkpointer — the durable store for short-term
conversational state (messages, in-progress farm_profile, trace_log, ...),
keyed per-thread by farmer_id. Uses psycopg3 directly; the rest of the app
keeps using psycopg2 through SQLAlchemy for the relational tables — the two
drivers coexist fine against the same Postgres instance.
"""
from langgraph.checkpoint.postgres import PostgresSaver
from psycopg_pool import ConnectionPool

from app.core.config import settings

_pool = ConnectionPool(
    conninfo=settings.database_url,
    max_size=10,
    kwargs={"autocommit": True, "prepare_threshold": 0},
    open=False,
)

checkpointer = PostgresSaver(_pool)


def init_checkpointer() -> None:
    """Open the pool and create langgraph's own checkpoint tables if they
    don't exist yet. Idempotent — safe to call on every startup."""
    if _pool.closed:
        _pool.open()
    checkpointer.setup()
