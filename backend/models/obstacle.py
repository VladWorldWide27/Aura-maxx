from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from backend.models.coords import Coordinates

class Obstacle(BaseModel):
    description: str = Field(..., example="Construction blocking sidewalk")
    coords: Coordinates
    photoUrl: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    active: bool = True
