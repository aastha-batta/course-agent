from flask import Flask, jsonify, request, send_from_directory
from flask_restx import Api, Resource, fields
import os
from dotenv import load_dotenv
import sys
import json
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from typing import Dict
import uuid
from pathlib import Path


course_tasks: Dict[str, Dict] = {}

load_dotenv()



# Create a storage directory
STORAGE_DIR = Path("./course_storage")
STORAGE_DIR.mkdir(exist_ok=True)

# Functions for course storage
def save_course(course_data, task_id=None):
    if not task_id:
        task_id = str(uuid.uuid4())
    
    course_data["task_id"] = task_id
    
    with open(STORAGE_DIR / f"{task_id}.json", "w") as f:
        json.dump(course_data, f, indent=2)
    
    return task_id

def get_course(task_id):
    try:
        with open(STORAGE_DIR / f"{task_id}.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return None
        
def get_all_courses():
    courses = []
    for file_path in STORAGE_DIR.glob("*.json"):
        with open(file_path, "r") as f:
            courses.append(json.load(f))
    return courses


def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__)
    
    api = Api(app, 
              version='1.0.0',
              title='Educational Course Generator API',
              description='API for generating and managing educational courses',
              doc='/swagger/')
    
    ns_health = api.namespace('health', description='Health check operations')
    ns_courses = api.namespace('api/courses', description='Course operations')
    
    from routes.courses_restx import register_routes
    
    # Register routes with the API
    register_routes(api, ns_courses)
    
    # Define health check resource
    @ns_health.route('/')
    class HealthCheck(Resource):
        def get(self):
            """Health check endpoint"""
            return {"status": "healthy"}
    
    @api.route('/')
    class Home(Resource):
        def get(self):
            """Home page"""
            return {
                "name": "Educational Course Generator API",
                "version": "1.0.0",
                "endpoints": {
                    "health": "/health",
                    "swagger_ui": "/swagger/",
                    "create_course": "/api/courses/",
                    "get_course": "/api/courses/<task_id>",
                    "download_course": "/api/courses/<task_id>/download",
                    "refine_course": "/api/courses/<task_id>/refine"
                }
            }
    
    # Create output directory if it doesn't exist
    os.makedirs("output", exist_ok=True)
    
    # Add route to get all courses for listing in the UI
    @ns_courses.route('/')
    class CourseList(Resource):
        def get(self):
            """List all courses"""
            return list(course_tasks.values())
    
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))