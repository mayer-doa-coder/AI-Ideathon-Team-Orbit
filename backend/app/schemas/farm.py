from pydantic import BaseModel, ConfigDict


class FarmOut(BaseModel):
    id: int
    location: str | None
    lat: float | None
    lon: float | None
    acres: float | None
    soil_type: str | None
    water_availability: str | None
    budget: float | None
    season: str | None

    model_config = ConfigDict(from_attributes=True)


class PlanOut(BaseModel):
    """The farm's actual committed plan as it stands in Postgres right now —
    reflects monitor-agent adjustments immediately, unlike the conversation
    graph's checkpointed state (`/api/chat/state`), which the monitor graph
    never touches. This is what the dashboard must reload from after a
    refresh so a persisted adjustment doesn't appear to "revert"."""

    crop: str | None
    season_plan: dict | None
    financials: dict | None

    model_config = ConfigDict(from_attributes=True)
