from pydantic import BaseModel, Field
from typing import Optional
from coords import Coordinates

class GraphNode(BaseModel):
    nodeId: str = Field(..., example="N123")
    name: Optional[str] = Field(None, example="Library Entrance")
    coordinates: Coordinates
    type: str = Field(default="other", example="intersection")
    active: bool = True
