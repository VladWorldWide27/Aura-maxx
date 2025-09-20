from pydantic import BaseModel, Field

class GraphEdge(BaseModel):
    edgeId: str = Field(..., example="E456")
    fromNodeId: str = Field(..., example="N123")
    toNodeId: str = Field(..., example="N124")
    distance: float = Field(..., example=15.5, description="Distance in meters")
    walkingTime: float = Field(..., example=20.0, description="Walking time in seconds")
    active: bool = True
