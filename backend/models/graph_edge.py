from pydantic import BaseModel, Field

class GraphEdge(BaseModel):
    edgeId: str = Field(..., example="E456")
    fromNodeId: str = Field(..., alias="from")  # Maps database "from" to "fromNodeId"
    toNodeId: str = Field(..., alias="to")      # Maps database "to" to "toNodeId"
    distance: float = Field(default=10.0, description="Distance in meters")
    walkingTime: float = Field(default=8.0, description="Walking time in seconds")
    active: bool = True
    name: str = Field(default="", description="Street name")

    class Config:
        allow_population_by_field_name = True  # Allows both field names
