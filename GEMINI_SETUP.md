# Gemini Obstacle Detection Setup Guide

## Overview
The obstacle detection system uses Google's Gemini AI to analyze photos and determine if they contain obstacles that could impede navigation for people with disabilities.

## Setup Instructions

### 1. Get Gemini API Key
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Copy the API key

### 2. Set Environment Variable
```bash
export GEMINI_API_KEY="your_api_key_here"
```

Or create a `.env` file in the project root:
```
GEMINI_API_KEY=your_api_key_here
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Application
```bash
uvicorn fastAPI:app --reload --host 0.0.0.0 --port 8000
```

### 5. Access the Frontend
Open your browser to `http://localhost:8000/frontend/index.html`

## How It Works

1. **User Reports Obstacle**: User clicks "Add an Obstacle" button
2. **Photo Capture**: User takes a photo using their device camera
3. **GPS Collection**: System automatically gets current GPS coordinates
4. **AI Analysis**: Photo is sent to Gemini AI for obstacle detection
5. **Result Processing**: 
   - If obstacle detected: Added to navigation database
   - If no obstacle: User is thanked for helping maintain accuracy
6. **Route Planning**: Detected obstacles are considered in future navigation

## API Endpoints

### POST /report-obstacle
- **Purpose**: Submit obstacle report with image analysis
- **Parameters**:
  - `image`: Image file (JPG/PNG)
  - `gps_coordinates`: JSON string with lat/lng
  - `description`: User description
- **Response**: Analysis results and obstacle status

### GET /gemini-status
- **Purpose**: Check if Gemini service is available
- **Response**: Service availability status

### GET /obstacles
- **Purpose**: Get all reported obstacles
- **Response**: List of obstacles

## Testing the Integration

1. Start the server with a valid Gemini API key
2. Open the frontend in a browser
3. Click "Add an Obstacle"
4. Take a photo of something that could be an obstacle
5. Add a description
6. Submit the report
7. Check the AI analysis results

## Troubleshooting

- **"Obstacle detection service not available"**: Check that GEMINI_API_KEY is set
- **Image upload fails**: Ensure image is JPG/PNG format
- **GPS not working**: Allow location permissions in browser
- **API timeout**: Check internet connection and Gemini service status

## Future Enhancements

- Integration with MongoDB for persistent storage
- Real-time obstacle updates on map
- User feedback system for AI accuracy
- Batch processing for multiple images
- Integration with navigation routing system