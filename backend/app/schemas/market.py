from pydantic import BaseModel

from app.tools.market_analytics import MarketSnapshot
from app.tools.market_decision import MarketDecision


class MarketSnapshotOut(BaseModel):
    crop: str
    season: str | None
    dam_commodity_name: str | None
    district: str | None
    district_matched: bool
    unit: str | None
    has_data: bool
    current_price: float | None
    current_price_date: str | None
    historical_average: float | None
    historical_high: float | None
    historical_low: float | None
    change_7d_pct: float | None
    change_30d_pct: float | None
    trend: str | None
    observation_count: int
    markets: list[str]
    source: str | None
    source_url: str | None
    unavailable_reason: str | None

    @classmethod
    def from_snapshot(cls, s: MarketSnapshot) -> "MarketSnapshotOut":
        return cls(
            crop=s.crop,
            season=s.season,
            dam_commodity_name=s.dam_commodity_name,
            district=s.district,
            district_matched=s.district_matched,
            unit=s.unit,
            has_data=s.has_data,
            current_price=s.current_price,
            current_price_date=s.current_price_date.isoformat() if s.current_price_date else None,
            historical_average=s.historical_average,
            historical_high=s.historical_high,
            historical_low=s.historical_low,
            change_7d_pct=s.change_7d_pct,
            change_30d_pct=s.change_30d_pct,
            trend=s.trend,
            observation_count=s.observation_count,
            markets=s.markets,
            source=s.source,
            source_url=s.source_url,
            unavailable_reason=s.unavailable_reason,
        )


class MarketDecisionOut(BaseModel):
    verdict: str | None
    score: float | None
    reasons: list[str]

    @classmethod
    def from_decision(cls, d: MarketDecision) -> "MarketDecisionOut":
        return cls(verdict=d.verdict, score=d.score, reasons=d.reasons)


class MarketIntelligenceOut(BaseModel):
    snapshot: MarketSnapshotOut
    decision: MarketDecisionOut


class MarketHistoryPointOut(BaseModel):
    price_date: str
    period_start: str
    period_end: str
    district: str | None
    market: str | None
    price_type: str
    min_price: float
    max_price: float
    avg_price: float
    unit: str
