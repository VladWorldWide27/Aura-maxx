import os
import base64
import requests
from PIL import Image
import io
import json
from typing import Tuple, Optional

class GeminiObstacleDetector:
    """
    A class to detect obstacles in images using Google's Gemini API.
    Processes images, shrinks them for efficiency, and analyzes them for obstacles.
    """
    
    def __init__(self, api_key: str = None):
        """
        Initialize the Gemini obstacle detector.
        
        Args:
            api_key: Google Gemini API key. If None, will try to get from environment.
        """
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("Gemini API key is required. Set GEMINI_API_KEY environment variable or pass it directly.")
        
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro-vision:generateContent"
        
        # Maximum image dimensions for processing (to reduce API costs and improve speed)
        self.max_width = 800
        self.max_height = 600
        
        # Prompt for obstacle detection
        self.detection_prompt = """
        Analyze this image carefully. This is a photo taken by a person with mobility challenges who needs to navigate sidewalks and pathways safely.

        Look for any obstacles or hazards that could impede safe navigation, including but not limited to:
        - Construction barriers, cones, or equipment
        - Debris, fallen branches, or objects blocking the path
        - Uneven surfaces, holes, or damaged pavement
        - Parked vehicles blocking sidewalks
        - Temporary barriers or signs
        - Any other physical obstructions

        Respond with ONLY the following format:
        OBSTACLE: [YES/NO]
        TYPE: [brief description of obstacle type, or "NONE" if no obstacle]

        Examples:
        OBSTACLE: YES
        TYPE: Construction barrier

        OBSTACLE: NO  
        TYPE: NONE
        """

    def _resize_image(self, image_bytes: bytes) -> bytes:
        """
        Resize image to reduce file size while maintaining quality for analysis.
        
        Args:
            image_bytes: Original image bytes
            
        Returns:
            Resized image bytes
        """
        try:
            # Open image
            image = Image.open(io.BytesIO(image_bytes))
            
            # Calculate new dimensions maintaining aspect ratio
            width, height = image.size
            if width > self.max_width or height > self.max_height:
                ratio = min(self.max_width / width, self.max_height / height)
                new_width = int(width * ratio)
                new_height = int(height * ratio)
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Convert to RGB if necessary (removes transparency)
            if image.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')
                background.paste(image, mask=image.split()[-1] if image.mode in ('RGBA', 'LA') else None)
                image = background
            
            # Save to bytes with optimized quality
            output = io.BytesIO()
            image.save(output, format='JPEG', quality=85, optimize=True)
            return output.getvalue()
            
        except Exception as e:
            raise ValueError(f"Failed to process image: {str(e)}")

    def _encode_image(self, image_bytes: bytes) -> str:
        """
        Encode image bytes to base64 string for API transmission.
        
        Args:
            image_bytes: Image bytes to encode
            
        Returns:
            Base64 encoded string
        """
        return base64.b64encode(image_bytes).decode('utf-8')

    def verify_obstacle(self, image_bytes: bytes, gps_coords: Tuple[float, float]) -> dict:
        """
        Analyze an image to detect obstacles and return structured results.
        
        Args:
            image_bytes: Image data as bytes (JPG, PNG, etc.)
            gps_coords: Tuple of (latitude, longitude) where photo was taken
            
        Returns:
            Dictionary containing:
            - is_obstacle: bool
            - obstacle_type: str
            - confidence: str
            - gps_coordinates: tuple
            - error: str (if any error occurred)
        """
        try:
            # Resize image for efficiency
            resized_image = self._resize_image(image_bytes)
            
            # Encode for API
            encoded_image = self._encode_image(resized_image)
            
            # Prepare API request
            headers = {
                'Content-Type': 'application/json',
            }
            
            payload = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": self.detection_prompt
                            },
                            {
                                "inline_data": {
                                    "mime_type": "image/jpeg",
                                    "data": encoded_image
                                }
                            }
                        ]
                    }
                ]
            }
            
            # Make API request
            url = f"{self.base_url}?key={self.api_key}"
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            if response.status_code != 200:
                return {
                    'is_obstacle': False,
                    'obstacle_type': 'NONE',
                    'confidence': 'error',
                    'gps_coordinates': gps_coords,
                    'error': f"API request failed: {response.status_code} - {response.text}"
                }
            
            # Parse response
            result = response.json()
            
            if 'candidates' not in result or not result['candidates']:
                return {
                    'is_obstacle': False,
                    'obstacle_type': 'NONE',
                    'confidence': 'error',
                    'gps_coordinates': gps_coords,
                    'error': "No response from Gemini API"
                }
            
            # Extract text response
            content = result['candidates'][0]['content']['parts'][0]['text'].strip()
            
            # Parse the structured response
            is_obstacle = False
            obstacle_type = 'NONE'
            
            lines = content.split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith('OBSTACLE:'):
                    is_obstacle = 'YES' in line.upper()
                elif line.startswith('TYPE:'):
                    obstacle_type = line.split(':', 1)[1].strip()
            
            return {
                'is_obstacle': is_obstacle,
                'obstacle_type': obstacle_type,
                'confidence': 'high',
                'gps_coordinates': gps_coords,
                'raw_response': content,
                'error': None
            }
            
        except requests.exceptions.Timeout:
            return {
                'is_obstacle': False,
                'obstacle_type': 'NONE',
                'confidence': 'error',
                'gps_coordinates': gps_coords,
                'error': "Request timeout"
            }
        except Exception as e:
            return {
                'is_obstacle': False,
                'obstacle_type': 'NONE',
                'confidence': 'error',
                'gps_coordinates': gps_coords,
                'error': f"Error processing image: {str(e)}"
            }

    def batch_verify_obstacles(self, image_data_list: list) -> list:
        """
        Process multiple images for obstacle detection.
        
        Args:
            image_data_list: List of tuples (image_bytes, gps_coords)
            
        Returns:
            List of detection results
        """
        results = []
        for image_bytes, gps_coords in image_data_list:
            result = self.verify_obstacle(image_bytes, gps_coords)
            results.append(result)
        return results

# Example usage and testing
if __name__ == "__main__":
    # This is for testing - you would set your actual API key
    detector = GeminiObstacleDetector()
    
    # Example: Load and test with a sample image
    # with open('sample_obstacle.jpg', 'rb') as f:
    #     image_data = f.read()
    # 
    # result = detector.verify_obstacle(image_data, (40.4443, -79.9532))
    # print(f"Obstacle detected: {result['is_obstacle']}")
    # print(f"Type: {result['obstacle_type']}")
    # print(f"GPS: {result['gps_coordinates']}")