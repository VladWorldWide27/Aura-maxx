from fastapi import FastAPI
from pydantic import BaseModel
from typing import List

app = FastAPI()

obstacles=[] # in memory tracker

class Obstacle(BaseModel):
    location:str
    description:str

#get directions
@app.get("/directions")
def get_directions(start: str, end: str):
    return {
        "start": start,
        "end": end,
        "directions": [
            f"Walk straight from {start}",
            "Turn xxx after xxx",
            f"Arrive at {end}"
        ],
        "obstacles": obstacles
    }

#get obstacles
@app.get("/obstacles", response_model=List[Obstacle])
def get_obstacles():
    return obstacles

#post- add obstacles
@app.post("/obstacles")
def add_obstacle(obstacle: Obstacle):
    obstacles.append(obstacle)
    return {"message": "Obstacle added", "obstacle": obstacle}
