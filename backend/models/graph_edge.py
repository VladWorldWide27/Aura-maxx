from pydantic import BaseModel, Field

class GraphEdge(BaseModel):
    edgeId: str = Field(..., example="E456")
    from_: str = Field(..., alias="from", example="1")  # Use alias for "from" 
    to: str = Field(..., example="2")
    active: bool = True
    name: str = Field(..., example="ohara_left")
    
    class Config:
        allow_population_by_field_name = True
