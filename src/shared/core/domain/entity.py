from datetime import datetime

from pydantic import BaseModel, Field


class Entity(BaseModel):
    id: str
    created_at: datetime
    updated_at: datetime | None = Field(default=None)
