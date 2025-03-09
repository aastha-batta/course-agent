import json
from typing import Dict, Any
from utils.logging_config import setup_logging


logging = setup_logging(log_level="INFO")

def format_course_output(course_data: Dict[str, Any]) -> Dict[str, Any]:
    """Format the course data to match the desired output structure"""
    try:
        # If we already have content_structure, return it
        if "content_structure" in course_data:
            return course_data["content_structure"]
        
        # If we have structure as a string, parse it
        if "structure" in course_data and isinstance(course_data["structure"], str):
            structure = json.loads(course_data["structure"])
            
            # Basic transformation
            return {
                "course_title": structure.get("title", ""),
                "description": structure.get("description", ""),
                "modules": structure.get("modules", []),
                "references": []
            }
        
        # Fallback: return an empty structure
        return {
            "course_title": "",
            "description": "",
            "modules": [],
            "references": []
        }
    except Exception as e:
        logging.error(f"Error formatting course output: {e}")
        return {
            "course_title": "Error in formatting",
            "description": "Could not format the course data properly",
            "modules": [],
            "references": []
        }