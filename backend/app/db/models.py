from datetime import date, datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

EMBEDDING_DIM = 1536


class KBChunk(Base):
    __tablename__ = "kb_chunks"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    crop: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    topic: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    section_heading: Mapped[str | None] = mapped_column(String(255), nullable=True)
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIM), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Farm(Base):
    """One farm per user — the durable, directly-queryable record both graphs
    read/write. `user_id` is the `users.id` from auth (no separate `farmers`
    table). Fields are nullable because the conversation graph's `persist`
    node fills them in incrementally across onboarding turns; the monitor
    graph only ever acts on a farm once every field plus a committed `Plan`
    exist (see `graph_monitor.load_initial_state`)."""

    __tablename__ = "farms"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, index=True, nullable=False)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    lon: Mapped[float | None] = mapped_column(Float, nullable=True)
    acres: Mapped[float | None] = mapped_column(Float, nullable=True)
    soil_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    water_availability: Mapped[str | None] = mapped_column(String(50), nullable=True)
    budget: Mapped[float | None] = mapped_column(Float, nullable=True)
    season: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Plan(Base):
    """The single committed season plan + financials for a farm.

    One row per farm (not a history table) — scenario simulations are
    derived-only and never land here (see `is_scenario` handling in the
    `persist` node); only the monitor graph's real, triggered adjustments
    update `season_plan`/`financials` in place, which is what keeps the
    monitor's "memory" of a farm durable across sweeps and sessions.
    Fields are nullable for the same incremental-fill reason as `Farm`."""

    __tablename__ = "plans"

    id: Mapped[int] = mapped_column(primary_key=True)
    farm_id: Mapped[int] = mapped_column(ForeignKey("farms.id"), unique=True, index=True, nullable=False)
    selected_crop: Mapped[str | None] = mapped_column(String(100), nullable=True)
    crop_candidates: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    season_plan: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    financials: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(primary_key=True)
    farm_id: Mapped[int] = mapped_column(ForeignKey("farms.id"), nullable=False, index=True)
    trigger_reason: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


class Supplier(Base):
    """Seeded/mock supplier catalog for the Tier 2 marketplace capability
    (see `tools/marketplace.py`). Plain structured Postgres data queried
    directly — never chunked/embedded into `kb_chunks`, so it stays out of
    the RAG retrieval path entirely. Swapping this for a real supplier API
    later only means replacing the query functions in `tools/marketplace.py`;
    the node/graph wiring doesn't change."""

    __tablename__ = "suppliers"

    id: Mapped[int] = mapped_column(primary_key=True)
    business_name: Mapped[str] = mapped_column(String(255), nullable=False)
    district: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    lon: Mapped[float | None] = mapped_column(Float, nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    rating: Mapped[float] = mapped_column(Float, nullable=False, default=4.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    products: Mapped[list["SupplierProduct"]] = relationship(
        back_populates="supplier", cascade="all, delete-orphan"
    )


class SupplierProduct(Base):
    """One row per (supplier, product) — a supplier may list several
    products, each with its own price/stock/delivery estimate. `last_updated`
    is what the "explainable" recommendation can point to when telling the
    farmer how fresh a price/stock figure is."""

    __tablename__ = "supplier_products"

    id: Mapped[int] = mapped_column(primary_key=True)
    supplier_id: Mapped[int] = mapped_column(ForeignKey("suppliers.id"), nullable=False, index=True)
    product_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    unit: Mapped[str] = mapped_column(String(20), nullable=False, default="kg")
    price_bdt_per_unit: Mapped[float] = mapped_column(Float, nullable=False)
    stock_available: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    delivery_days: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    last_updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    supplier: Mapped["Supplier"] = relationship(back_populates="products")


class MarketPrice(Base):
    """One ingested price observation from the Bangladesh Department of
    Agricultural Marketing (DAM, market.dam.gov.bd) — see
    `tools/market_price.py` for how these are actually fetched (DAM has no
    documented API; this is real data scraped from their public commodity
    price report).

    DAM's own report is period-aggregated (min/max/avg over a queried date
    range), not a clean single-day price point, so each row represents one
    such window — `period_start`/`period_end` are the real query window,
    and `price_date` is when *we* ingested it (the "as of" date analytics
    and the UI should show). `min_price`/`max_price` are kept alongside
    `avg_price` because DAM provides them directly and they're useful for
    the historical-high/low requirement without extra computation.

    `unit` defaults to "kg" — DAM's report doesn't state a unit explicitly;
    this is DAM's documented standard convention for retail/producer prices,
    not fabricated, but is a real assumption worth flagging (see the
    ingestion module's docstring)."""

    __tablename__ = "market_prices"

    id: Mapped[int] = mapped_column(primary_key=True)
    crop: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    dam_commodity_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    dam_commodity_name: Mapped[str] = mapped_column(String(255), nullable=False)
    division: Mapped[str | None] = mapped_column(String(100), nullable=True)
    district: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    market: Mapped[str | None] = mapped_column(String(150), nullable=True)
    price_type: Mapped[str] = mapped_column(String(20), nullable=False)  # "producer" | "retail" | "wholesale"
    unit: Mapped[str] = mapped_column(String(20), nullable=False, default="kg")
    min_price: Mapped[float] = mapped_column(Float, nullable=False)
    max_price: Mapped[float] = mapped_column(Float, nullable=False)
    avg_price: Mapped[float] = mapped_column(Float, nullable=False)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    price_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(100), nullable=False, default="Bangladesh Department of Agricultural Marketing (DAM)")
    source_url: Mapped[str] = mapped_column(String(255), nullable=False)
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class BDAppsSubscriber(Base):
    """A BDApps subscriber's SMS/USSD channel access, driven entirely by the
    `subscription/notify` webhook — BDApps' own authoritative source of
    truth for subscribe/unsubscribe events (see
    `api/routes/bdapps.subscription_notification_callback`). Gates whether an
    MSISDN's SMS/USSD messages get routed to the conversation agent at all."""

    __tablename__ = "bdapps_subscribers"

    id: Mapped[int] = mapped_column(primary_key=True)
    msisdn: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    subscription_status: Mapped[str] = mapped_column(String(20), nullable=False)
    last_event_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class BDAppsChargeTransaction(Base):
    """One row per `caas/direct/debit` call made to BDApps
    (`tools/bdapps_client.direct_debit`), written by the CaaS checkout flow
    (`api/routes/payment.checkout`) whether the debit succeeds or fails —
    the durable receipt/audit record for every charge attempt.

    `user_id` ties the charge to the authenticated user who initiated it, so a
    successful (`S1000`) row is what grants that user premium entitlements
    (see `services.consultancy_service.user_has_premium`). Nullable because
    charges can also originate from the SMS/USSD channels, which are keyed by
    MSISDN and have no web user."""

    __tablename__ = "bdapps_charge_transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    msisdn: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    external_trx_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    internal_trx_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    reference_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="BDT")
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    status_detail: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ConsultationRequest(Base):
    """A premium farmer's booked consultation with a (mock) crop expert.

    Gated by a successful BDApps payment: the checkout is real, but the expert
    roster and the reply are mocked (see `services.consultancy_service`) — the
    point is to demonstrate the real CaaS payment unlocking a paid feature
    end-to-end, not to run an actual human advisory desk. One row per question
    a farmer submits; `expert_reply` is filled synchronously at creation."""

    __tablename__ = "consultation_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    expert_id: Mapped[str] = mapped_column(String(50), nullable=False)
    expert_name: Mapped[str] = mapped_column(String(100), nullable=False)
    expert_specialty: Mapped[str] = mapped_column(String(100), nullable=False)
    topic: Mapped[str] = mapped_column(Text, nullable=False)
    expert_reply: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="answered")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


class TraceLog(Base):
    """Every tool call any graph makes, for the "visible agent trace" requirement.

    `source` distinguishes which graph produced the entry ("monitor" today;
    the conversation graph can write "conversation" rows into this same table)."""

    __tablename__ = "trace_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    farm_id: Mapped[int | None] = mapped_column(ForeignKey("farms.id"), nullable=True, index=True)
    source: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    node_name: Mapped[str] = mapped_column(String(100), nullable=False)
    tool_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    params: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    result: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
