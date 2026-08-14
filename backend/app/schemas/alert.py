from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AlertOut(BaseModel):
    id: int
    farm_id: int
    trigger_reason: str
    message: str
    payload: dict | None
    is_read: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
