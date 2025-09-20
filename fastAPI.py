from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import json
from gemini_obstacle_detector import GeminiObstacleDetector

app = FastAPI()

# Initialize Gemini detector
try:
    gemini_detector = GeminiObstacleDetector()
except ValueError as e:
    print(f"Warning: Gemini detector not initialized: {e}")
    gemini_detector = None

obstacles=[] # in memory tracker

class Obstacle(BaseModel):
    location: str
    description: str
    obstacle_type: Optional[str] = None
    is_verified: Optional[bool] = False
    gps_coordinates: Optional[dict] = None

class ObstacleReport(BaseModel):
    gps_coordinates: dict  # {"lat": float, "lng": float}
    description: str
    is_obstacle: bool
    obstacle_type: str

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

#post- report obstacle with image analysis
@app.post("/report-obstacle")
async def report_obstacle(
    image: UploadFile = File(...),
    gps_coordinates: str = Form(...),
    description: str = Form(...)
):
    """
    Report an obstacle with image verification using Gemini AI.
    
    Args:
        image: Uploaded image file (JPG/PNG)
        gps_coordinates: JSON string with lat/lng coordinates
        description: User description of the obstacle
    
    Returns:
        Analysis result and obstacle information
    """
    if not gemini_detector:
        raise HTTPException(status_code=503, detail="Obstacle detection service not available. Please set GEMINI_API_KEY environment variable.")
    
    try:
        # Parse GPS coordinates
        gps_data = json.loads(gps_coordinates)
        if 'lat' not in gps_data or 'lng' not in gps_data:
            raise ValueError("GPS coordinates must include 'lat' and 'lng'")
        
        lat = float(gps_data['lat'])
        lng = float(gps_data['lng'])
        
        # Validate image file
        if not image.content_type or not image.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read image data
        image_data = await image.read()
        
        # Analyze with Gemini
        analysis_result = gemini_detector.verify_obstacle(image_data, (lat, lng))
        
        # Create obstacle report
        obstacle_report = {
            "gps_coordinates": {"lat": lat, "lng": lng},
            "description": description,
            "is_obstacle": analysis_result['is_obstacle'],
            "obstacle_type": analysis_result['obstacle_type'],
            "confidence": analysis_result['confidence'],
            "analysis_error": analysis_result.get('error'),
            "timestamp": None  # You can add timestamp if needed
        }
        
        # If Gemini confirms it's an obstacle, add to obstacles list
        if analysis_result['is_obstacle'] and not analysis_result.get('error'):
            obstacle = Obstacle(
                location=f"{lat}, {lng}",
                description=description,
                obstacle_type=analysis_result['obstacle_type'],
                is_verified=True,
                gps_coordinates={"lat": lat, "lng": lng}
            )
            obstacles.append(obstacle)
        
        return {
            "message": "Obstacle report processed successfully",
            "analysis": obstacle_report,
            "added_to_obstacles": analysis_result['is_obstacle'] and not analysis_result.get('error')
        }
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid GPS coordinates format")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing obstacle report: {str(e)}")

# Health check endpoint for Gemini service
@app.get("/gemini-status")
def gemini_status():
    """Check if Gemini obstacle detection service is available."""
    return {
        "gemini_available": gemini_detector is not None,
        "status": "ready" if gemini_detector else "api_key_missing"
    }
