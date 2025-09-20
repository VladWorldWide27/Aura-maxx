from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from datetime import datetime
import uuid

from obstacle import Obstacle
from graph_node import GraphNode
from graph_edge import GraphEdge
from database import obstacles_collection, nodes_collection, edges_collection

app = FastAPI(title="Hackathon Navigation API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Obstacle Endpoints 
@app.get("/obstacles", response_model=List[Obstacle])
async def get_obstacles():
    """Get all active obstacles"""
    try:
        cursor = obstacles_collection.find({"active": True})
        obstacles = []
        async for obstacle in cursor:
            # Convert MongoDB _id to string and remove it
            obstacle.pop("_id", None)
            obstacles.append(Obstacle(**obstacle))
        return obstacles
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/obstacles")
async def add_obstacle(obstacle: Obstacle):
    """Add new obstacle report"""
    try:
        # Convert Pydantic model to dict
        obstacle_dict = obstacle.dict()
        obstacle_dict["_id"] = str(uuid.uuid4())  # Add unique ID
        
        # Store in MongoDB
        result = await obstacles_collection.insert_one(obstacle_dict)
        
        return {
            "message": "Obstacle added successfully",
            "id": obstacle_dict["_id"],
            "obstacle": obstacle
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Graph Node Endpoints
@app.get("/nodes", response_model=List[GraphNode])
async def get_nodes():
    """Get all graph nodes"""
    try:
        cursor = nodes_collection.find({"active": True})
        nodes = []
        async for node in cursor:
            node.pop("_id", None)
            nodes.append(GraphNode(**node))
        return nodes
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/nodes")
async def add_node(node: GraphNode):
    """Add new graph node"""
    try:
        node_dict = node.dict()
        node_dict["_id"] = node_dict["nodeId"]  # Use nodeId as _id
        
        result = await nodes_collection.insert_one(node_dict)
        
        return {
            "message": "Node added successfully",
            "node": node
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Graph Edge Endpoints
@app.get("/edges", response_model=List[GraphEdge])
async def get_edges():
    """Get all graph edges"""
    try:
        cursor = edges_collection.find({"active": True})
        edges = []
        async for edge in cursor:
            edge.pop("_id", None)
            edges.append(GraphEdge(**edge))
        return edges
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/edges")
async def add_edge(edge: GraphEdge):
    """Add new graph edge"""
    try:
        edge_dict = edge.dict()
        edge_dict["_id"] = edge_dict["edgeId"]  # Use edgeId as _id
        
        result = await edges_collection.insert_one(edge_dict)
        
        return {
            "message": "Edge added successfully",
            "edge": edge
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Directions
@app.get("/directions")
async def get_directions(start: str, end: str):
    """Get directions with current obstacles"""
    try:
        # Get obstacles from database
        cursor = obstacles_collection.find({"active": True})
        obstacles = []
        async for obstacle in cursor:
            obstacle.pop("_id", None)
            obstacles.append(obstacle)
        
        return {
            "start": start,
            "end": end,
            "directions": [
                f"Walk straight from {start}",
                "Turn right after 200m",
                f"Arrive at {end}"
            ],
            "obstacles": obstacles
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
