from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TraceLogOut(BaseModel):
    id: int
    farm_id: int | None
    source: str
    node_name: str
    tool_name: str | None
    params: dict | None
    result: dict | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
