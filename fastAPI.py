from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from datetime import datetime
import uuid

from obstacle import Obstacle
from graph_node import GraphNode
from graph_edge import GraphEdge
from database import obstacles_collection, nodes_collection, edges_collection

from navigator import Navigator, Node, Graph

app = FastAPI(title="Hackathon Navigation API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create an instance of the Navigator class globally
# This will be shared across all requests
nav = None

@app.on_event("startup")
async def startup_event():
    """Load graph data from the database on application startup."""
    global nav
    try:
        # Load nodes
        nodes = []
        node_cursor = nodes_collection.find()
        async for node_data in node_cursor:
            nodes.append(Node(
                node_data['id'],
                (node_data['lat'], node_data['lon']),
                node_data['name']
            ))

        # Load edges and add to nodes
        edge_cursor = edges_collection.find()
        async for edge_data in edge_cursor:
            if edge_data['src'] in [n.id for n in nodes]:
                nodes[[n.id for n in nodes].index(edge_data['src'])].links.append(edge_data['dst'])
            if edge_data['dst'] in [n.id for n in nodes]:
                nodes[[n.id for n in nodes].index(edge_data['dst'])].links.append(edge_data['src'])

        # Create the graph
        graph = Graph(nodes)
        nav = Navigator(graph)
        print("Graph loaded successfully from the database.")
    except Exception as e:
        print(f"Failed to load graph on startup: {e}")

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
    if nav is None:
        raise HTTPException(status_code=503, detail="Navigation service not ready. Graph not loaded.")
    
    try:
        # Get start and end coordinates from the request
        # You will need to parse the start and end strings into (lat, lon) tuples
        start_lat, start_lon = map(float, start.split(','))
        end_lat, end_lon = map(float, end.split(','))
        start_coords = (start_lat, start_lon)
        end_coords = (end_lat, end_lon)

        # Get obstacles from database
        cursor = obstacles_collection.find({"active": True})
        obstacles = []
        async for obstacle in cursor:
            obstacle.pop("_id", None)
            obstacles.append(obstacle)

        # Use the navigator to find the nearest nodes
        start_node = nav.graph.find_nearest(start_coords)
        end_node = nav.graph.find_nearest(end_coords)

        if not start_node or not end_node:
            raise HTTPException(status_code=404, detail="Could not find a path. Start or end point is too far from a known node.")

        # Find the path, considering obstacles
        path_nodes = nav.find_path(start_node.id, end_node.id, obstacles)

        # Format the path into a list of directions
        directions_list = nav.get_text_directions(path_nodes)
        
        return {
            "start": start,
            "end": end,
            "directions": directions_list,
            "obstacles": obstacles
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred while calculating directions: {str(e)}")
        
