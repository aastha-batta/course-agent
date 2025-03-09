# routes/courses_restx.py
from flask import jsonify, request
from flask_restx import Resource, fields
import asyncio
import json
import uuid
import logging
from datetime import datetime
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from services.research_service import ResearchService
from models.course import Course
from typing import Dict
course_tasks: Dict[str, Dict] = {}



def register_routes(api, ns):
    """Register all routes with the API namespace"""
    
    # Define models
    course_request = api.model('CourseRequest', {
        'topic': fields.String(required=True, description='The main topic of the course'),
        'depth': fields.String(required=False, default='beginner', description='The depth of the course (beginner, intermediate, advanced)'),
        'target_audience': fields.String(required=False, default='General audience', description='The target audience for the course'),
        'course_duration': fields.String(required=False, description='Expected duration of the course')
    })
    
    course_response = api.model('CourseResponse', {
        'message': fields.String(description='Response message'),
        'task_id': fields.String(description='Unique task identifier'),
        'status': fields.String(description='Task status')
    })
    
    task_status = api.model('TaskStatus', {
        'id': fields.String(description='Task ID'),
        'topic': fields.String(description='Course topic'),
        'depth': fields.String(description='Course depth'),
        'target_audience': fields.String(description='Target audience'),
        'status': fields.String(description='Current status'),
        'created_at': fields.String(description='Creation timestamp'),
        'updated_at': fields.String(description='Last update timestamp'),
        'course_title': fields.String(description='Course title (when completed)'),
        'modules_count': fields.Integer(description='Number of modules (when completed)'),
        'download_url': fields.String(description='URL to download the course (when completed)')
    })
    
    refinement_request = api.model('RefinementRequest', {
        'refinement_type': fields.String(required=False, default='general', description='Type of refinement'),
        'instructions': fields.String(required=True, description='Specific instructions for refinement')
    })
    
    refinement_response = api.model('RefinementResponse', {
        'message': fields.String(description='Response message'),
        'refinement_id': fields.String(description='Unique refinement task identifier'),
        'status': fields.String(description='Refinement task status')
    })

    @ns.route('/')
    class CourseCollection(Resource):
        @api.doc('create_course')
        @api.expect(course_request)
        @api.marshal_with(course_response, code=201)  # Changed to 201 Created for POST
        def post(self):
            """Create a new course generation task"""
            data = request.json
            
            # Validate input
            if not data or "topic" not in data:
                api.abort(400, "Missing required field: topic")
            
            # Set default values if not provided
            topic = data.get("topic")
            depth = data.get("depth", "beginner")
            target_audience = data.get("target_audience", "General audience")
            course_duration = data.get("course_duration", "4 weeks")
            
            # Create a unique task ID
            task_id = str(uuid.uuid4())
            
            # Store task info
            course_tasks[task_id] = {
                "id": task_id,
                "topic": topic,
                "depth": depth,
                "target_audience": target_audience,
                "course_duration": course_duration,
                "status": "queued",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            

            asyncio.run(process_course_generation(task_id, data))
            
            return {
                "message": "Course generation started",
                "task_id": task_id,
                "status": "queued"
            }, 201  # Return 201 Created status

        @api.doc('list_courses')
        def get(self):
            """List all courses"""
            return list(course_tasks.values())

    @ns.route('/<string:task_id>')
    @api.doc(params={'task_id': 'The task identifier'})
    class CourseItem(Resource):
        @api.doc('get_course_status')
        @api.response(404, 'Course task not found')
        def get(self, task_id):
            """Get the status of a course generation task"""
            # Check if task exists
            if task_id not in course_tasks:
                api.abort(404, "Course task not found")
            
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
                        return {
                            **task_info,
                            "course_title": course_data.get("title", ""),
                            "modules_count": len(course_data.get("modules", [])),
                            "download_url": f"/api/courses/{task_id}/download"
                        }
                    except Exception as e:
                        return {
                            **task_info,
                            "error": f"Error reading course data: {str(e)}"
                        }
            
            return task_info

    @ns.route('/<string:task_id>/download')
    @api.doc(params={'task_id': 'The task identifier'})
    class CourseDownload(Resource):
        @api.doc('download_course')
        @api.response(404, 'Course task not found')
        @api.response(400, 'Course generation not yet complete')
        def get(self, task_id):
            """Download the generated course content"""
            # Check if task exists and is completed
            if task_id not in course_tasks:
                api.abort(404, "Course task not found")
            
            task_info = course_tasks[task_id]
            if task_info.get("status") != "completed":
                api.abort(400, "Course generation not yet complete")
            
            output_file = os.path.join("output", f"{task_id}_output.json")
            
            if not os.path.exists(output_file):
                api.abort(404, "Course output file not found")
            
            try:
                with open(output_file, 'r') as f:
                    course_data = json.load(f)
                
                return course_data
            except Exception as e:
                api.abort(500, f"Error reading course data: {str(e)}")

    @ns.route('/<string:task_id>/refine')
    @api.doc(params={'task_id': 'The task identifier'})
    class CourseRefine(Resource):
        @api.doc('refine_course')
        @api.expect(refinement_request)
        @api.marshal_with(refinement_response, code=202)  # Using 202 Accepted for refinement
        @api.response(404, 'Course task not found')
        @api.response(400, 'Cannot refine a course that is not yet complete')
        def post(self, task_id):
            """Refine an existing course with additional parameters"""
            # Check if task exists and is completed
            if task_id not in course_tasks:
                api.abort(404, "Course task not found")
            
            task_info = course_tasks[task_id]
            if task_info.get("status") != "completed":
                api.abort(400, "Cannot refine a course that is not yet complete")
            
            data = request.json
            refinement_type = data.get("refinement_type", "general")
            refinement_instructions = data.get("instructions", "")
            
            # Create a new task for refinement
            refinement_id = f"{task_id}_refine_{str(uuid.uuid4())[:8]}"
            
            # Store refinement task info
            course_tasks[refinement_id] = {
                "id": refinement_id,
                "original_task_id": task_id,
                "topic": task_info.get("topic", "Unknown"),  # Copy original topic
                "refinement_type": refinement_type,
                "instructions": refinement_instructions,
                "status": "queued",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            # Start the refinement process
            asyncio.create_task(process_course_refinement(refinement_id, task_id, data))
            
            return {
                "message": "Course refinement started",
                "refinement_id": refinement_id,
                "status": "queued"
            }, 202  # Return 202 Accepted status

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