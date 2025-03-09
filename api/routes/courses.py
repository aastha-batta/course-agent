# routes/courses.py
from flask import Blueprint, jsonify, request
import asyncio
import json
import uuid
import logging
from datetime import datetime
from typing import Dict
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from services.research_service import ResearchService
from models.course import Course

# Create blueprint
courses_bp = Blueprint('courses', __name__, url_prefix='/api/courses')

course_tasks: Dict[str, Dict] = {}

@courses_bp.route('/', methods=['POST'])
def create_course():
    """Create a new course generation task"""
    data = request.json
    
    # Validate input
    if not data or "topic" not in data:
        return jsonify({"error": "Missing required field: topic"}), 400
    
    # Set default values if not provided
    topic = data.get("topic")
    depth = data.get("depth", "beginner")
    target_audience = data.get("target_audience", "General audience")
    
    # Create a unique task ID
    task_id = str(uuid.uuid4())
    
    # Store task info
    course_tasks[task_id] = {
        "id": task_id,
        "topic": topic,
        "depth": depth,
        "target_audience": target_audience,
        "status": "queued",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    # Start the course generation process in the background
    # Note: In production, this would be handled by a task queue like Celery
    asyncio.run(process_course_generation(task_id, data))
    
    return jsonify({
        "message": "Course generation started",
        "task_id": task_id,
        "status": "queued"
    })

@courses_bp.route('/<task_id>', methods=['GET'])
def get_course_status(task_id):
    """Get the status of a course generation task"""
    # Check if task exists
    if task_id not in course_tasks:
        return jsonify({"error": "Course task not found"}), 404
    
    task_info = course_tasks[task_id]
    
    # If task is completed, include the output file location
    if task_info.get("status") == "completed":
        output_file = os.path.join("output", f"{task_id}_output.json")
        
        if os.path.exists(output_file):
            # Load the course data
            try:
                with open(output_file, 'r') as f:
                    course_data = json.load(f)
                
                # Include a summary in the response
                return jsonify({
                    **task_info,
                    "course_title": course_data.get("title", ""),
                    "modules_count": len(course_data.get("modules", [])),
                    "download_url": f"/api/courses/{task_id}/download"
                })
            except Exception as e:
                return jsonify({
                    **task_info,
                    "error": f"Error reading course data: {str(e)}"
                })
    
    return jsonify(task_info)

@courses_bp.route('/<task_id>/download', methods=['GET'])
def download_course(task_id):
    """Download the generated course content"""
    # Check if task exists and is completed
    if task_id not in course_tasks:
        return jsonify({"error": "Course task not found"}), 404
    
    task_info = course_tasks[task_id]
    if task_info.get("status") != "completed":
        return jsonify({"error": "Course generation not yet complete"}), 400
    
    output_file = os.path.join("output", f"{task_id}_output.json")
    
    if not os.path.exists(output_file):
        return jsonify({"error": "Course output file not found"}), 404
    
    try:
        with open(output_file, 'r') as f:
            course_data = json.load(f)
        
        return jsonify(course_data)
    except Exception as e:
        return jsonify({"error": f"Error reading course data: {str(e)}"}), 500

@courses_bp.route('/<task_id>/refine', methods=['POST'])
def refine_course(task_id):
    """Refine an existing course with additional parameters"""
    # Check if task exists and is completed
    if task_id not in course_tasks:
        return jsonify({"error": "Course task not found"}), 404
    
    task_info = course_tasks[task_id]
    if task_info.get("status") != "completed":
        return jsonify({"error": "Cannot refine a course that is not yet complete"}), 400
    
    data = request.json
    refinement_type = data.get("refinement_type", "general")
    refinement_instructions = data.get("instructions", "")
    
    # Create a new task for refinement
    refinement_id = f"{task_id}_refine_{str(uuid.uuid4())[:8]}"
    
    # Store refinement task info
    course_tasks[refinement_id] = {
        "id": refinement_id,
        "original_task_id": task_id,
        "refinement_type": refinement_type,
        "instructions": refinement_instructions,
        "status": "queued",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    # Start the refinement process
    # This would call a different workflow specifically for refinement
    asyncio.create_task(process_course_refinement(refinement_id, task_id, data))
    
    return jsonify({
        "message": "Course refinement started",
        "refinement_id": refinement_id,
        "status": "queued"
    })

# Background processing functions
async def process_course_generation(task_id, input_data):
    """Background process for course generation"""
    from agents.coordinator import CoordinatorAgent
    from agents.researcher import ResearchAgent
    from agents.structurer import StructureAgent
    from agents.content_generator import ContentGenerationAgent
    from agents.validator import ValidationAgent
    
    try:
        # Update task status
        course_tasks[task_id]["status"] = "processing"
        course_tasks[task_id]["updated_at"] = datetime.now().isoformat()
        
        # Create agents
        coordinator = CoordinatorAgent()
        researcher = ResearchAgent()
        structurer = StructureAgent()
        content_generator = ContentGenerationAgent()
        validator = ValidationAgent()
        
        # Register agents with coordinator
        coordinator.register_agent("researcher", researcher)
        coordinator.register_agent("structurer", structurer)
        coordinator.register_agent("content_generator", content_generator)
        coordinator.register_agent("validator", validator)
        
        # Set workflow
        coordinator.set_workflow(["researcher", "structurer", "content_generator", "validator"])
        
        # Process through the workflow
        result = await coordinator.process(input_data)
        
        # Extract the final course structure
        final_course = Course.from_dict(result.get("course", {}).get("content_structure", {}))
        final_course.topic = input_data.get("topic", "")
        final_course.depth = input_data.get("depth", "intermediate")
        final_course.course_duration = input_data.get("course_duration", "Unknown Duration")
        
        # Adjust modules to match course duration
        final_course.adjust_modules_to_duration()
        
        output_file = os.path.join("output", f"{task_id}_output.json")
        
        # Save to file
        with open(output_file, "w") as f:
            json.dump(final_course.to_dict(), f, indent=2)
        
        # Update task status
        course_tasks[task_id]["status"] = "completed"
        course_tasks[task_id]["updated_at"] = datetime.now().isoformat()
        
        logging.info(f"Task {task_id} completed successfully")
    except Exception as e:
        # Handle errors and update task status
        error_message = str(e)
        course_tasks[task_id]["status"] = "failed"
        course_tasks[task_id]["error"] = error_message
        course_tasks[task_id]["updated_at"] = datetime.now().isoformat()
        
        logging.error(f"Error in task {task_id}: {error_message}")

async def process_course_refinement(refinement_id, original_task_id, refinement_data):
    """Background process for course refinement"""
    try:
        # Update task status
        course_tasks[refinement_id]["status"] = "processing"
        course_tasks[refinement_id]["updated_at"] = datetime.now().isoformat()
        
        original_file = os.path.join("output", f"{original_task_id}_output.json")
        refinement_file = os.path.join("output", f"{refinement_id}_output.json")
        
        # Load the original course data
        with open(original_file, "r") as f:
            original_course = json.load(f)
        
        # This would call a specialized refinement workflow
        # For now, we'll implement a simplified version that just adds a note
        
        refinement_type = refinement_data.get("refinement_type", "general")
        instructions = refinement_data.get("instructions", "")
        
        # Add refinement info to the course
        if "validation_results" not in original_course:
            original_course["validation_results"] = {}
            
        if "refinements" not in original_course["validation_results"]:
            original_course["validation_results"]["refinements"] = []
        
        original_course["validation_results"]["refinements"].append({
            "type": refinement_type,
            "instructions": instructions,
            "applied_at": datetime.now().isoformat()
        })
        
        # Save refined course
        with open(refinement_file, "w") as f:
            json.dump(original_course, f, indent=2)
        
        # Update task status
        course_tasks[refinement_id]["status"] = "completed"
        course_tasks[refinement_id]["updated_at"] = datetime.now().isoformat()
        
        logging.info(f"Refinement {refinement_id} completed successfully")
    except Exception as e:
        # Handle errors and update task status
        error_message = str(e)
        course_tasks[refinement_id]["status"] = "failed"
        course_tasks[refinement_id]["error"] = error_message
        course_tasks[refinement_id]["updated_at"] = datetime.now().isoformat()
        
        logging.error(f"Error in refinement {refinement_id}: {error_message}")