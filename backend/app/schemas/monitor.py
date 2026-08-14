from pydantic import BaseModel


class SimulateTriggerRequest(BaseModel):
    """Optional custom forecast override. Omit the body entirely to use the
    endpoint's built-in synthetic heavy-rain scenario."""

    weather_override: dict | None = None


class MonitorSweepResponse(BaseModel):
    farm_id: int
    simulated: bool
    triggered: bool
    trigger_reason: str | None
    weather_data: dict | None
    updated_plan: dict | None
    updated_financials: dict | None
