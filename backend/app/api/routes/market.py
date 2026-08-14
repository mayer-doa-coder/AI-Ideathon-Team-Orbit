"""Market Price Intelligence endpoints. Real DAM-sourced data only — see
`tools/market_price.py` for how it's actually ingested and
`tools/market_analytics.py` / `tools/market_decision.py` for how these
responses are computed. Nothing here calls DAM live (it's far too slow for
a request/response cycle); every route reads what `scripts/ingest_market_prices.py`
already wrote to Postgres.
"""
from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.models import MarketPrice
from app.db.session import get_db
from app.models.user import User
from app.schemas.market import (
    MarketDecisionOut,
    MarketHistoryPointOut,
    MarketIntelligenceOut,
    MarketSnapshotOut,
)
from app.tools.market_analytics import get_market_snapshot
from app.tools.market_decision import make_decision
from app.tools.market_price import CANONICAL_CROPS, resolve_commodity

router = APIRouter(prefix="/api/market", tags=["market"])


@router.get("/crops")
def list_supported_crops(current_user: User = Depends(get_current_user)):
    """The canonical crops market intelligence has a DAM mapping for —
    lentil is deliberately absent (see tools/market_price.py)."""
    return {"crops": CANONICAL_CROPS}


@router.get("/current", response_model=MarketSnapshotOut)
def get_current_price(
    crop: str,
    season: str | None = None,
    district: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    snapshot = get_market_snapshot(db, crop=crop, season=season, district=district)
    return MarketSnapshotOut.from_snapshot(snapshot)


@router.get("/history", response_model=list[MarketHistoryPointOut])
def get_price_history(
    crop: str,
    season: str | None = None,
    district: str | None = None,
    days: int = Query(180, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    commodity_entry = resolve_commodity(crop, season)
    if commodity_entry is None:
        return []
    dam_commodity_id = int(commodity_entry.split("|", 1)[0])

    cutoff = date.today() - timedelta(days=days)
    query = db.query(MarketPrice).filter(
        MarketPrice.dam_commodity_id == dam_commodity_id,
        MarketPrice.price_date >= cutoff,
    )
    if district:
        district_rows = query.filter(MarketPrice.district.ilike(f"%{district}%")).order_by(MarketPrice.price_date).all()
        rows = district_rows or query.order_by(MarketPrice.price_date).all()
    else:
        rows = query.order_by(MarketPrice.price_date).all()

    return [
        MarketHistoryPointOut(
            price_date=r.price_date.isoformat(),
            period_start=r.period_start.isoformat(),
            period_end=r.period_end.isoformat(),
            district=r.district,
            market=r.market,
            price_type=r.price_type,
            min_price=r.min_price,
            max_price=r.max_price,
            avg_price=r.avg_price,
            unit=r.unit,
        )
        for r in rows
    ]


@router.get("/decision", response_model=MarketIntelligenceOut)
def get_market_decision(
    crop: str,
    season: str | None = None,
    district: str | None = None,
    storage_available: bool | None = None,
    storage_cost_bdt_per_unit_per_month: float | None = None,
    quantity_kg: float | None = None,
    urgent_cash_needed: bool | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    snapshot = get_market_snapshot(db, crop=crop, season=season, district=district)
    decision = make_decision(
        snapshot,
        season=season,
        storage_available=storage_available,
        storage_cost_bdt_per_unit_per_month=storage_cost_bdt_per_unit_per_month,
        quantity_kg=quantity_kg,
        urgent_cash_needed=urgent_cash_needed,
    )
    return MarketIntelligenceOut(
        snapshot=MarketSnapshotOut.from_snapshot(snapshot),
        decision=MarketDecisionOut.from_decision(decision),
    )
