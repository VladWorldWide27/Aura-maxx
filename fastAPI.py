from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

from typing import List, Optional
from datetime import datetime
import uuid
import json
import os
import io  # ← ADD THIS IMPORT
from PIL import Image as PILImage  # ← ADD THIS IMPORT

from backend.models.obstacle import Obstacle, Coordinates
from backend.models.graph_node import GraphNode
from backend.models.graph_edge import GraphEdge

# Try to import database collections, fallback if not available
try:
    from backend.models.database import obstacles_collection, nodes_collection, edges_collection
    database_available = True
    print("✅ Database connection available")
except Exception as e:
    print(f"⚠️  Warning: Database not available: {e}")
    obstacles_collection = None
    nodes_collection = None
    edges_collection = None
    database_available = False

# Try to import Gemini detector, fallback if not available
try:
    from gemini_obstacle_detector import GeminiObstacleDetector
    gemini_detector = GeminiObstacleDetector()
    gemini_available = True
    print("✅ Gemini obstacle detector initialized successfully")
except Exception as e:
    print(f"⚠️  Warning: Gemini obstacle detector not available: {e}")
    gemini_detector = None
    gemini_available = False

import sys
from navigation.navigator import Navigator, Graph

app = FastAPI(title="Hackathon Navigation API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for frontend
app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")

# Initialize Gemini detector with proper error handling
# (Already handled above)

# Health check endpoint
@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Aura-maxx Navigation API is running",
        "status": "healthy",
        "gemini_available": gemini_available,
        "database_available": database_available
    }

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
    

@app.post("/detect")
async def detect(file: UploadFile = File(...)):
    try:
        # Check if Gemini is available
        if not gemini_available or not gemini_detector:
            return JSONResponse(
                content={"error": "Gemini service unavailable", "is_obstacle": False},
                status_code=503
            )

        # Read the uploaded file
        image_bytes = await file.read()
        coords = (0, 0)  # replace with actual coords if needed

        # Call Gemini
        result = gemini_detector.verify_obstacle(image_bytes, coords)

        # Ensure JSON response
        return JSONResponse(content=result)

    except Exception as e:
        # Log error clearly in server logs
        print(f"🔥 ERROR in /detect: {e}")
        return JSONResponse(
            content={"error": str(e), "is_obstacle": False},
            status_code=500
        )

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

@app.post("/report-obstacle")
async def report_obstacle(
    image: UploadFile = File(..., description="Image of the potential obstacle"),
    gps_coordinates: str = Form(..., description="GPS coordinates as JSON string"),
    description: str = Form(..., description="User description of the obstacle")
):
    """
    Report a potential obstacle with image analysis using Gemini AI
    """
    try:
        # Check if Gemini is available
        if not gemini_available or not gemini_detector:
            print("❌ Gemini service not available")
            raise HTTPException(
                status_code=503, 
                detail="Gemini AI service is not available. Please check API key configuration."
            )
        
        # Validate image file
        if not image.content_type or not image.content_type.startswith('image/'):
            print(f"❌ Invalid content type: {image.content_type}")
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Parse GPS coordinates
        try:
            coords_data = json.loads(gps_coordinates)
            lat = float(coords_data['lat'])
            lng = float(coords_data['lng'])
            print(f"📍 GPS coordinates: {lat}, {lng}")
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"❌ GPS parsing error: {e}")
            raise HTTPException(status_code=400, detail=f"Invalid GPS coordinates format: {e}")
        
        # Read image data
        print("📸 Reading image data...")
        image_bytes = await image.read()
        if len(image_bytes) == 0:
            print("❌ Empty image file")
            raise HTTPException(status_code=400, detail="Empty image file")
        
        print(f"📊 Image size: {len(image_bytes)} bytes")
        
        # Test if we can create a PIL image from the bytes
        try:
            test_image = PILImage.open(io.BytesIO(image_bytes))
            print(f"✅ Valid image: {test_image.size}, format: {test_image.format}")
        except Exception as img_error:
            print(f"❌ Invalid image data: {img_error}")
            raise HTTPException(status_code=400, detail=f"Invalid image data: {img_error}")
        
        # Analyze image with Gemini
        print(f"🔍 Analyzing image for obstacle detection...")
        analysis_result = gemini_detector.verify_obstacle(image_bytes, (lat, lng))
        
        print(f"📊 Raw analysis result: {analysis_result}")
        
        # Check for analysis errors
        if analysis_result.get('error'):
            error_msg = analysis_result['error']
            print(f"❌ Gemini analysis error: {error_msg}")
            
            # For JSON parsing errors, try to provide a fallback response
            if "Expecting value" in error_msg or "JSON" in error_msg:
                print("🔄 Using fallback analysis due to JSON error")
                analysis_result = {
                    "is_obstacle": False,
                    "obstacle_type": "analysis_failed",
                    "confidence": 0.0,
                    "severity": "NONE",
                    "error": f"AI analysis failed: {error_msg}"
                }
            else:
                raise HTTPException(
                    status_code=500, 
                    detail=f"Image analysis failed: {error_msg}"
                )
        
        print(f"✅ Analysis completed successfully")
        
        # Create obstacle object with AI analysis data
        obstacle_data = {
            "description": description,
            "coords": {
                "lat": lat,
                "lng": lng
            },
            "photoUrl": None,  # Could implement photo storage later
            "timestamp": datetime.utcnow(),
            "active": True,
            "ai_verified": analysis_result.get('is_obstacle', False),
            "obstacle_type": analysis_result.get('obstacle_type', 'unknown'),
            "ai_confidence": analysis_result.get('confidence', 0.0),
            "ai_error": analysis_result.get('error'),
            "_id": str(uuid.uuid4())
        }
        
        # Always save to database (whether obstacle detected or not, for data collection)
        try:
            await obstacles_collection.insert_one(obstacle_data)
            print(f"💾 Obstacle report saved to database with ID: {obstacle_data['_id']}")
        except Exception as db_error:
            print(f"⚠️ Database save failed: {db_error}")
            # Continue anyway, just log the error
        
        return {
            "message": "Image analysis completed successfully",
            "analysis": {
                "is_obstacle": analysis_result.get('is_obstacle', False),
                "obstacle_type": analysis_result.get('obstacle_type', 'unknown'),
                "severity": analysis_result.get('severity', 'NONE'),
                "confidence": analysis_result.get('confidence', 0.0),
                "raw_response": analysis_result.get('raw_response', ''),
                "error": analysis_result.get('error')
            },
            "coordinates": {"lat": lat, "lng": lng},
            "user_description": description,
            "obstacle_saved": True,
            "database_id": obstacle_data['_id']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Unexpected error in report_obstacle: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

# Add a simple test endpoint
@app.post("/test-gemini")
async def test_gemini_simple():
    """Simple test endpoint for Gemini API"""
    try:
        if not gemini_available or not gemini_detector:
            return {"status": "error", "message": "Gemini not available"}
        
        # Test with a simple text prompt
        import google.generativeai as genai
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content("Respond with exactly this JSON: {\"test\": \"success\"}")
        
        return {
            "status": "success",
            "message": "Gemini API is working",
            "response": response.text if hasattr(response, 'text') else str(response)
        }
    except Exception as e:
        return {
            "status": "error", 
            "message": f"Gemini test failed: {str(e)}"
        }

@app.get("/gemini-status")
async def get_gemini_status():
    """
    Check if Gemini obstacle detection service is available
    """
    return {
        "gemini_available": gemini_available,
        "service_status": "online" if gemini_available else "offline",
        "message": "Gemini obstacle detection is ready" if gemini_available else "Gemini service unavailable - check API key configuration"
    }

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
from fastapi import Query

@app.get("/directions")
async def get_directions(start_lat: float, start_lng: float, end_lat: float, end_lng: float):
    """Get real directions using your existing navigation system"""
    try:
        # Create a navigator instance with the graph file
        navigator = Navigator(None, "navigation/graph_points.txt")
        
        # Get obstacles from database and add them to navigator
        if database_available and obstacles_collection:
            try:
                obstacles_cursor = obstacles_collection.find({"active": True, "ai_verified": True})
                async for obstacle in obstacles_cursor:
                    obs_coords = (obstacle['coords']['lat'], obstacle['coords']['lng'])
                    navigator.add_obstacle(obs_coords)
            except Exception as db_error:
                print(f"Warning: Could not load obstacles from database: {db_error}")
                # Continue without obstacles
        else:
            print("Database not available, proceeding without obstacles")
        
        # Use your existing navigation method
        start_coords = (start_lat, start_lng)
        end_coords = (end_lat, end_lng)
        
        route_coords = navigator.navigate(start_coords, end_coords)
        
        if route_coords:
            return {
                "start": {"lat": start_lat, "lng": start_lng},
                "end": {"lat": end_lat, "lng": end_lng},
                "path": route_coords,  # Your navigator returns [lng, lat] pairs
                "success": True,
                "obstacles_avoided": len(navigator.obstacles),
                "directions": [
                    "Follow the calculated route avoiding reported obstacles",
                    f"Route avoids {len(navigator.obstacles)} obstacles",
                    "Arrive at destination"
                ]
            }
        else:
            return {
                "start": {"lat": start_lat, "lng": start_lng},
                "end": {"lat": end_lat, "lng": end_lng},
                "error": "No path found - all routes may be blocked",
                "success": False
            }
            
    except Exception as e:
        print(f"Navigation error: {e}")
        raise HTTPException(status_code=500, detail=f"Navigation error: {str(e)}")


async def build_graph_from_database():
    """Convert your MongoDB data to the format your Navigator expects"""
    
    # Get all nodes from database
    nodes_cursor = nodes_collection.find({"active": True})
    edges_cursor = edges_collection.find({"active": True})
    
    # Build nodes in your navigator's expected format
    graph_nodes = []
    node_links = {}
    
    async for node in nodes_cursor:
        node_data = {
            'id': int(node['nodeId']),  # Your navigator expects integer IDs
            'gps_coords': (node['coordinates']['lat'], node['coordinates']['lng']),
            'name': node.get('name', f"Node_{node['nodeId']}"),
            'links': []  # Will populate from edges
        }
        graph_nodes.append(node_data)
    
    # Build adjacency list from edges
    async for edge in edges_cursor:
        from_id = int(edge.get('from', edge.get('fromNodeId', 0)))
        to_id = int(edge.get('to', edge.get('toNodeId', 0)))
        
        if from_id not in node_links:
            node_links[from_id] = []
        if to_id not in node_links:
            node_links[to_id] = []
            
        node_links[from_id].append(to_id)
        node_links[to_id].append(from_id)  # Bidirectional
    
    # Add links to nodes
    for node in graph_nodes:
        node['links'] = node_links.get(node['id'], [])
    
    return graph_nodes
