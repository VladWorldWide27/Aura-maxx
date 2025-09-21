import base64
import json
import google.generativeai as genai
import os
from PIL import Image
import io
import re

class GeminiObstacleDetector:
    def __init__(self):
        # ⚠️ SECURITY: Use environment variable instead of hardcoded key
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("❌ Missing GEMINI_API_KEY environment variable")
        
        genai.configure(api_key=api_key)
        # Try different model names - use the most current one available
        try:
            self.model = genai.GenerativeModel("gemini-1.5-flash")
        except Exception:
            try:
                self.model = genai.GenerativeModel("gemini-pro-vision")
            except Exception:
                self.model = genai.GenerativeModel("gemini-pro")

    def verify_obstacle(self, image_bytes: bytes, coords: tuple):
        try:
            # Convert raw bytes → PIL image
            image = Image.open(io.BytesIO(image_bytes))
            
            # Resize image if too large (Gemini has size limits)
            max_size = 1024
            if image.width > max_size or image.height > max_size:
                image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

            # Simplified, more direct prompt
            prompt = """
            Analyze this image for accessibility obstacles. Look for stairs, curbs, barriers, debris, or anything blocking pedestrian paths.

            Respond with valid JSON only:
            {
                "is_obstacle": true,
                "obstacle_type": "description here",
                "confidence": 0.85,
                "severity": "HIGH"
            }

            Confidence: 0.0-1.0, Severity: NONE/LOW/MEDIUM/HIGH
            """

            print(f"🔍 Sending image to Gemini API...")
            
            # Generate content with better error handling
            try:
                response = self.model.generate_content([prompt, image])
                print(f"📥 Received response from Gemini")
                
                # Check for safety blocks
                if hasattr(response, 'prompt_feedback') and response.prompt_feedback:
                    if hasattr(response.prompt_feedback, 'block_reason'):
                        print(f"🚫 Content blocked: {response.prompt_feedback.block_reason}")
                        return self._create_error_response(f"Content blocked: {response.prompt_feedback.block_reason}")

                # Check if response exists
                if not response:
                    print("❌ No response from Gemini API")
                    return self._create_error_response("No response from Gemini API")
                
                # Check for text attribute
                if not hasattr(response, 'text'):
                    print("❌ Response object has no text attribute")
                    print(f"Response object: {dir(response)}")
                    return self._create_error_response("Response object has no text attribute")
                
                # Check if text is empty
                if not response.text:
                    print("❌ Empty text response from Gemini API")
                    return self._create_error_response("Empty text response from Gemini API")

                response_text = response.text.strip()
                print(f"📝 Raw Gemini response: '{response_text}'")

            except Exception as api_error:
                print(f"❌ Gemini API error: {str(api_error)}")
                return self._create_error_response(f"Gemini API error: {str(api_error)}")

            # Clean response text
            text_out = response_text.strip()
            
            # Remove markdown code blocks if present
            if text_out.startswith('```json'):
                text_out = text_out.replace('```json', '').replace('```', '').strip()
            elif text_out.startswith('```'):
                text_out = text_out.replace('```', '').strip()
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', text_out, re.DOTALL)
            if json_match:
                json_text = json_match.group(0)
            else:
                print(f"❌ No JSON found in response: '{text_out}'")
                return self._fallback_analysis(text_out, "No JSON structure found")

            # Parse JSON
            try:
                analysis = json.loads(json_text)
                print(f"✅ Successfully parsed JSON: {analysis}")
            except json.JSONDecodeError as json_error:
                print(f"❌ JSON parse error: {json_error}")
                print(f"❌ Attempted to parse: '{json_text}'")
                return self._fallback_analysis(text_out, str(json_error))

            # Validate and clean up the response
            analysis = self._validate_response(analysis)
            return analysis

        except Exception as e:
            print(f"❌ General error in verify_obstacle: {str(e)}")
            return self._create_error_response(str(e))

    def _validate_response(self, analysis):
        """Validate and fix the analysis response"""
        # Ensure required fields exist
        required_fields = {
            "is_obstacle": False,
            "obstacle_type": "unknown",
            "confidence": 0.0,
            "severity": "NONE"
        }
        
        for field, default in required_fields.items():
            if field not in analysis:
                analysis[field] = default

        # Ensure proper data types
        analysis["is_obstacle"] = bool(analysis.get("is_obstacle", False))
        
        # Handle confidence as float
        try:
            analysis["confidence"] = float(analysis.get("confidence", 0.0))
        except (ValueError, TypeError):
            analysis["confidence"] = 0.0
            
        # Ensure confidence is between 0 and 1
        analysis["confidence"] = max(0.0, min(1.0, analysis["confidence"]))
        
        # Validate severity
        valid_severities = ["NONE", "LOW", "MEDIUM", "HIGH"]
        severity = str(analysis.get("severity", "NONE")).upper()
        if severity not in valid_severities:
            analysis["severity"] = "NONE"
        else:
            analysis["severity"] = severity

        return analysis

    def _create_error_response(self, error_message: str):
        """Create a standardized error response"""
        return {
            "error": error_message,
            "is_obstacle": False,
            "obstacle_type": "unknown",
            "confidence": 0.0,
            "severity": "NONE"
        }

    def _fallback_analysis(self, raw_text: str, json_error: str):
        """Attempt to extract meaning from non-JSON responses"""
        raw_lower = raw_text.lower()
        
        # Simple keyword-based fallback
        obstacle_keywords = [
            "obstacle", "barrier", "blocked", "stairs", "curb", 
            "debris", "construction", "parked car", "uneven",
            "step", "bump", "hole", "crack", "tree", "pole"
        ]
        
        is_obstacle = any(word in raw_lower for word in obstacle_keywords)
        
        # Try to extract confidence if mentioned
        confidence_match = re.search(r'confidence[:\s]*([0-9.]+)', raw_lower)
        if confidence_match:
            try:
                confidence = float(confidence_match.group(1))
                if confidence > 1.0:  # Handle percentage format
                    confidence = confidence / 100.0
                confidence = max(0.0, min(1.0, confidence))
            except ValueError:
                confidence = 0.3 if is_obstacle else 0.1
        else:
            confidence = 0.3 if is_obstacle else 0.1
        
        return {
            "error": f"JSON parse failed: {json_error}",
            "is_obstacle": is_obstacle,
            "obstacle_type": "detected_via_keywords" if is_obstacle else "unknown",
            "confidence": confidence,
            "severity": "LOW" if is_obstacle else "NONE",
            "raw_response": raw_text
        }

# Test function to debug API connectivity
def test_gemini_connection():
    """Test if Gemini API is working"""
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("❌ No API key found")
            return False
            
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        # Simple text test
        response = model.generate_content("Say 'Hello, API is working!'")
        print(f"✅ API Test Response: {response.text}")
        return True
        
    except Exception as e:
        print(f"❌ API Test Failed: {e}")
        return False

# Example usage with debugging
if __name__ == "__main__":
    # Test API connection first
    print("🧪 Testing Gemini API connection...")
    if not test_gemini_connection():
        print("❌ API connection failed. Check your API key.")
        exit(1)
    
    # Test detector
    print("🧪 Testing obstacle detector...")
    detector = GeminiObstacleDetector()
    
    # Test with image file
    try:
        with open("test_image.jpg", "rb") as f:
            image_bytes = f.read()
        
        result = detector.verify_obstacle(image_bytes, (0, 0))
        print("🎯 Final result:")
        print(json.dumps(result, indent=2))
        
    except FileNotFoundError:
        print("📁 Test image not found. Please provide a valid image file.")
    except Exception as e:
        print(f"❌ Error: {e}")