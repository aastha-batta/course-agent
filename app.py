from flask import Flask, jsonify, request, render_template, redirect, url_for, flash, send_from_directory
import os
from dotenv import load_dotenv
import requests
import json
import logging
from datetime import datetime
import time
import uuid
from pathlib import Path
import threading

# Load environment variables
load_dotenv()

# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create a storage directory for courses
STORAGE_DIR = Path("./course_storage")
STORAGE_DIR.mkdir(exist_ok=True)

# Fix API configuration - use environment variables properly
API_PORT = os.getenv("API_PORT", "5000")  
API_HOST = os.getenv("API_HOST", "localhost")
API_BASE_URL = os.getenv("API_BASE_URL", f"http://{API_HOST}:{API_PORT}/api")

# Course storage functions
def save_course(course_data, task_id=None):
    """Save course data to a JSON file"""
    if not task_id:
        task_id = str(uuid.uuid4())
    
    course_data["task_id"] = task_id
    
    with open(STORAGE_DIR / f"{task_id}.json", "w") as f:
        json.dump(course_data, f, indent=2)
    
    return task_id

def get_course(task_id):
    """Retrieve course data from file"""
    try:
        with open(STORAGE_DIR / f"{task_id}.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return None
        
def get_all_courses():
    """Retrieve all courses"""
    courses = []
    for file_path in STORAGE_DIR.glob("*.json"):
        with open(file_path, "r") as f:
            try:
                course_data = json.load(f)
                courses.append(course_data)
            except json.JSONDecodeError:
                logger.error(f"Error decoding JSON from {file_path}")
                continue
    return courses

# Function to call the API asynchronously
def generate_course_async(task_id, course_data):
    """Call the API to generate a course in a separate thread"""
    # First, check if the course exists
    course = get_course(task_id)
    if not course:
        logger.error(f"Course {task_id} not found")
        return
        
    # Create or update the course with processing status
    course["status"] = "processing"
    save_course(course, task_id)
    
    logger.info(f"Starting course generation for task ID: {task_id}")
    logger.info(f"Using API URL: {API_BASE_URL}")
    
    # Call the main.py API endpoint to handle the course generation
    api_url = f"{API_BASE_URL}/courses/"
    
    # Add error handling and retries for the API call
    max_retries = 3
    retry_delay = 2
    api_available = False
    
    for attempt in range(max_retries):
        try:
            # We're making a request to the main.py API which should handle the actual processing
            logger.info(f"Attempt {attempt+1}: Calling API at {api_url}")
            response = requests.post(api_url, json=course_data, timeout=10)
            
            # If successful, break out of the retry loop
            if response.status_code == 201:
                logger.info(f"API call successful with status {response.status_code}")
                api_available = True
                break
                
            logger.warning(f"API returned unexpected status code: {response.status_code}")
            
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                
        except requests.exceptions.RequestException as req_error:
            logger.warning(f"API request error on attempt {attempt+1}: {str(req_error)}")
            if attempt < max_retries - 1:
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                # Final attempt failed
                logger.error(f"All API call attempts failed for task {task_id}")
    
    # If API is not available, generate course content locally
    if not api_available:
        logger.warning(f"API service unavailable. Falling back to local course generation for task {task_id}")
        
        # Update status to indicate we're generating locally
        course = get_course(task_id)
        if course:
            course["status"] = "processing"
            course["generation_method"] = "local"
            save_course(course, task_id)
        
        # Simulate processing time (in a real app, this would be the actual generation)
        # For this simplified UI, we'll make it faster - just 5 seconds total
        for i in range(5):
            time.sleep(1)
            # Update progress if needed
            if i == 2:  # At 60% mark
                course = get_course(task_id)
                if course:
                    course["progress"] = 60
                    save_course(course, task_id)
                    
        # Create a simple course structure
        generated_course = {
            "task_id": task_id,
            "topic": course_data.get("topic"),
            "depth": course_data.get("depth", "beginner"),
            "target_audience": course_data.get("target_audience", "General audience"),
            "course_duration": course_data.get("course_duration", "4 weeks"),
            "status": "completed",
            "created_at": course.get("created_at"),
            "completed_at": datetime.now().isoformat(),
            "content": {
                "title": f"Course on {course_data.get('topic')}",
                "description": f"A {course_data.get('depth', 'beginner')} level course about {course_data.get('topic')} for {course_data.get('target_audience', 'General audience')}.",
                "duration": course_data.get("course_duration", "4 weeks"),
                "modules": [
                    {
                        "title": "Module 1: Introduction",
                        "description": f"Introduction to {course_data.get('topic')}",
                        "lessons": [
                            {"title": "Lesson 1.1: Overview", "content": "This is an overview of the subject."},
                            {"title": "Lesson 1.2: Key Concepts", "content": "These are the key concepts you need to understand."}
                        ]
                    },
                    {
                        "title": "Module 2: Core Content",
                        "description": f"Main concepts of {course_data.get('topic')}",
                        "lessons": [
                            {"title": "Lesson 2.1: Fundamentals", "content": "The fundamental principles of the subject."},
                            {"title": "Lesson 2.2: Advanced Topics", "content": "More advanced topics to deepen your understanding."}
                        ]
                    }
                ]
            }
        }
        
        # If this is a refinement, add that information
        if "refinement_instructions" in course_data:
            generated_course["refinement_type"] = course_data.get("refinement_type", "general")
            generated_course["refinement_instructions"] = course_data.get("refinement_instructions")
            generated_course["refined_from"] = course_data.get("refined_from", task_id)
            
            # Add a note about the refinement
            generated_course["content"]["description"] += f" This course has been refined with the following instructions: {course_data.get('refinement_instructions')}"
        
        # Save the generated course
        save_course(generated_course, task_id)
        logger.info(f"Local course generation completed for task ID: {task_id}")
        return

def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__)
    app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key")
    
    #-----------------------------------------------------------------------------
    # API ROUTES - Adding direct API handling to fix course storage issues
    #-----------------------------------------------------------------------------
    
    @app.route("/api/courses/", methods=["GET"])
    def list_courses_api():
        """API endpoint to list all courses"""
        courses = get_all_courses()
        return jsonify(courses), 200
    
    @app.route("/api/courses/", methods=["POST"])
    def create_course_api():
        """API endpoint to create a new course"""
        data = request.json
        task_id = save_course({
            "topic": data.get("topic"),
            "depth": data.get("depth", "beginner"),
            "target_audience": data.get("target_audience", "General audience"),
            "course_duration": data.get("course_duration", "4 weeks"),
            "status": "processing",
            "created_at": datetime.now().isoformat()
        })
        
        # Start a background thread to process the course
        course_data = {
            "task_id": task_id,
            "topic": data.get("topic"),
            "depth": data.get("depth", "beginner"),
            "target_audience": data.get("target_audience", "General audience"),
            "course_duration": data.get("course_duration", "4 weeks")
        }
        
        thread = threading.Thread(target=generate_course_async, args=(task_id, course_data))
        thread.daemon = True
        thread.start()
        
        # Return the task ID
        return jsonify({"task_id": task_id}), 201
    
    @app.route("/api/courses/<task_id>/", methods=["GET"])
    def get_course_api(task_id):
        """API endpoint to get a specific course"""
        course = get_course(task_id)
        if not course:
            return jsonify({"error": "Course not found"}), 404
        
        return jsonify(course), 200
    
    @app.route("/api/courses/<task_id>/download/", methods=["GET"])
    def download_course_api(task_id):
        """API endpoint to download a course"""
        course = get_course(task_id)
        if not course:
            return jsonify({"error": "Course not found"}), 404
            
        if course.get("status") != "completed":
            return jsonify({"error": "Course not yet completed"}), 400
            
        return jsonify(course), 200
    
    @app.route("/api/courses/<task_id>/refine/", methods=["POST"])
    def refine_course_api(task_id):
        """API endpoint to refine a course"""
        course = get_course(task_id)
        if not course:
            return jsonify({"error": "Course not found"}), 404
            
        data = request.json
        
        # Create a new course as the refined version
        refined_course = course.copy()
        refined_course["refined_from"] = task_id
        refined_course["refinement_instructions"] = data
        
        new_task_id = save_course(refined_course)
        
        return jsonify({"refinement_id": new_task_id}), 202
    
    #-----------------------------------------------------------------------------
    # WEB UI ROUTES (for browser access)
    #-----------------------------------------------------------------------------
    
    @app.route("/")
    def index():
        """Home page"""
        try:
            # Get 3 most recent courses directly from storage
            all_courses = get_all_courses()
            recent_courses = sorted(
                all_courses, 
                key=lambda x: x.get('created_at', ''), 
                reverse=True
            )[:3]
                
            return render_template('index.html', recent_courses=recent_courses, current_year=datetime.now().year)
        except Exception as e:
            logger.error(f"Error rendering index: {str(e)}")
            flash("An error occurred while loading the home page", "danger")
            return render_template('index.html', recent_courses=[], current_year=datetime.now().year)
    
    @app.route("/courses")
    def courses_list():
        """List all courses"""
        try:
            # Get courses directly from storage
            all_courses = get_all_courses()
            all_courses = sorted(
                all_courses, 
                key=lambda x: x.get('created_at', ''), 
                reverse=True
            )
            
            return render_template('courses/list.html', courses=all_courses, current_year=datetime.now().year)
        except Exception as e:
            logger.error(f"Error rendering courses list: {str(e)}")
            flash("An error occurred while loading courses", "danger")
            return render_template('courses/list.html', courses=[], current_year=datetime.now().year)
    
    @app.route("/courses/create", methods=["GET"])
    def create_course_form():
        """Display the course creation form"""
        return render_template('courses/create.html', current_year=datetime.now().year)
    
    @app.route("/courses/create", methods=["POST"])
    def create_course_submit():
        """Handle course creation form submission"""
        try:
            # Get form data
            topic = request.form.get('topic')
            depth = request.form.get('depth', 'beginner')
            target_audience = request.form.get('target_audience', 'General audience')
            course_duration = request.form.get('course_duration', '4 weeks')

            # Validate input
            if not topic:
                flash('Topic is required', 'danger')
                return redirect(url_for('create_course_form'))

            # Create course with processing status
            task_id = save_course({
                "topic": topic,
                "depth": depth,
                "target_audience": target_audience,
                "course_duration": course_duration,
                "status": "processing",
                "created_at": datetime.now().isoformat()
            })
            
            # Start a background thread to process the course
            course_data = {
                "task_id": task_id,
                "topic": topic,
                "depth": depth,
                "target_audience": target_audience,
                "course_duration": course_duration
            }
            
            thread = threading.Thread(target=generate_course_async, args=(task_id, course_data))
            thread.daemon = True
            thread.start()
            
            flash('Course generation started', 'success')
            return render_template('courses/generation_started.html', 
                                task_id=task_id, 
                                topic=topic,
                                current_year=datetime.now().year)
        except Exception as e:
            logger.error(f"Error creating course: {str(e)}")
            flash(f"An error occurred while creating the course: {str(e)}", "danger")
            return redirect(url_for('create_course_form'))
    
    # New route to check the status of course generation
    @app.route("/courses/<task_id>/status")
    def check_course_status(task_id):
        """Check the status of course generation"""
        try:
            course = get_course(task_id)
            if not course:
                return jsonify({"error": "Course not found"}), 404

            status = course.get("status", "unknown")
            return jsonify({
                "status": status,
                "completed": status == "completed",
                "error": status == "error" or status == "failed",
                "error_message": course.get("error_message", "")
            })
        except Exception as e:
            logger.error(f"Error checking course status {task_id}: {str(e)}")
            return jsonify({"error": str(e)}), 500
        
    @app.route("/courses/lookup")
    def lookup_course_form():
        """Display the course lookup form"""
        return render_template('courses/lookup.html', current_year=datetime.now().year)

    @app.route("/courses/lookup/find")
    def lookup_course():
        """Look up a course by task ID"""
        task_id = request.args.get('task_id')
        
        if not task_id:
            flash('Task ID is required', 'danger')
            return redirect(url_for('lookup_course_form'))
        
        # Redirect to the course view page with the explicit task_id
        return redirect(url_for('view_course', task_id=task_id))
    
    @app.route("/courses/<task_id>")
    def view_course(task_id):
        """View a specific course"""
        try:
            # Get course directly from storage
            course = get_course(task_id)
            if not course:
                flash('Course not found', 'danger')
                return redirect(url_for('courses_list'))
            
            course_data = None
            # If task is completed, get the course data
            if course.get("status") == "completed":
                course_data = course.get("content")
            
            return render_template('courses/view.html', 
                                course=course, 
                                course_data=course_data, 
                                current_year=datetime.now().year)
        except Exception as e:
            logger.error(f"Error viewing course {task_id}: {str(e)}")
            flash(f"An error occurred while viewing the course: {str(e)}", "danger")
            return redirect(url_for('courses_list'))
    
    @app.route("/courses/<task_id>/download")
    def download_course(task_id):
        """Download the course JSON file"""
        try:
            course = get_course(task_id)
            if not course:
                flash('Course not found', 'danger')
                return redirect(url_for('courses_list'))
            
            # Check if task is completed
            if course.get("status") != "completed":
                flash('Course generation not yet complete', 'warning')
                return redirect(url_for('view_course', task_id=task_id))
            
            # Save the file locally (temporarily)
            os.makedirs("temp_downloads", exist_ok=True)
            temp_file = os.path.join("temp_downloads", f"course_{task_id}.json")
            
            with open(temp_file, "w") as f:
                json.dump(course, f, indent=2)
            
            logger.info(f"Sending file from {os.path.abspath('temp_downloads')}/{f'course_{task_id}.json'}")
            
            return send_from_directory(
                directory=os.path.abspath('temp_downloads'),
                path=f"course_{task_id}.json",
                as_attachment=True,
                download_name=f"course_{task_id}.json"
            )
        except Exception as e:
            logger.error(f"Error downloading course {task_id}: {str(e)}")
            flash(f"An error occurred while downloading the course: {str(e)}", "danger")
            return redirect(url_for('view_course', task_id=task_id))
    
    @app.route("/courses/<task_id>/refine", methods=["POST"])
    def refine_course_submit(task_id):
        """Handle course refinement form submission"""
        try:
            # Get form data
            refinement_type = request.form.get('refinement_type', 'general')
            instructions = request.form.get('instructions')
            
            # Validate input
            if not instructions:
                flash('Refinement instructions are required', 'danger')
                return redirect(url_for('view_course', task_id=task_id))
            
            # Get the original course
            course = get_course(task_id)
            if not course:
                flash('Course not found', 'danger')
                return redirect(url_for('courses_list'))
            
            # Create a new course as the refined version
            refined_course = course.copy()
            refined_course["refined_from"] = task_id
            refined_course["refinement_type"] = refinement_type
            refined_course["refinement_instructions"] = instructions
            refined_course["status"] = "processing"  # Set status to processing
            
            new_task_id = save_course(refined_course)
            
            # Start a background thread to process the refinement
            refinement_data = {
                "task_id": task_id,
                "refinement_type": refinement_type,
                "instructions": instructions
            }
            
            thread = threading.Thread(target=generate_course_async, args=(new_task_id, refinement_data))
            thread.daemon = True
            thread.start()
            
            flash('Course refinement started', 'success')
            return redirect(url_for('view_course', task_id=new_task_id))
        except Exception as e:
            logger.error(f"Error refining course {task_id}: {str(e)}")
            flash(f"An error occurred while refining the course: {str(e)}", "danger")
            return redirect(url_for('view_course', task_id=task_id))
    
    @app.route("/health")
    def health_check():
        """Health check endpoint"""
        return jsonify({
            "status": "healthy",
            "storage": "file-based",
            "course_count": len(list(STORAGE_DIR.glob("*.json")))
        })
    
    @app.route("/api-docs")
    def api_docs():
        """API documentation page"""
        try:
            return render_template('api_docs.html', current_year=datetime.now().year)
        except:
            # Fallback in case template doesn't exist
            return jsonify({
                "message": "API Documentation",
                "endpoints": [
                    {"path": "/api/courses/", "methods": ["GET", "POST"], "description": "List or create courses"},
                    {"path": "/api/courses/<task_id>/", "methods": ["GET"], "description": "Get a specific course"},
                    {"path": "/api/courses/<task_id>/download/", "methods": ["GET"], "description": "Download a course"},
                    {"path": "/api/courses/<task_id>/refine/", "methods": ["POST"], "description": "Refine a course"}
                ]
            })
    
    @app.errorhandler(404)
    def page_not_found(e):
        """Handle 404 errors"""
        flash("Page not found", "danger")
        return redirect(url_for('index'))
    
    @app.errorhandler(500)
    def server_error(e):
        """Handle 500 errors"""
        logger.error(f"Server error: {str(e)}")
        flash("An internal server error occurred", "danger")
        return redirect(url_for('index'))
    
    @app.context_processor
    def inject_globals():
        """Inject global variables into templates"""
        return {
            'current_year': datetime.now().year
        }
    
    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host="0.0.0.0", port=int(os.getenv("UI_PORT", 5001)))