from flask import Flask, jsonify, request, render_template, redirect, url_for, flash, send_from_directory
import os
from dotenv import load_dotenv
import requests
import json
import logging
from datetime import datetime
import time

# Load environment variables
load_dotenv()

# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
# Use a different port for the API
PORT = os.getenv("PORT", "5000")  # Default port for the Flask app
API_PORT = os.getenv("API_PORT", "5001")  # Default port for the API
API_BASE_URL = os.getenv("API_BASE_URL", f"http://localhost:{API_PORT}/api")

def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__)
    app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key")
    
    #-----------------------------------------------------------------------------
    # WEB UI ROUTES (for browser access)
    #-----------------------------------------------------------------------------
    
    @app.route("/")
    def index():
        """Home page"""
        # Get 3 most recent courses from API
        try:
            response = requests.get(f"{API_BASE_URL}/courses/")
            if response.status_code == 200:
                all_courses = response.json()
                # Sort by created_at (newest first)
                recent_courses = sorted(
                    all_courses, 
                    key=lambda x: x.get('created_at', ''), 
                    reverse=True
                )[:3]
            else:
                recent_courses = []
                flash('Unable to fetch recent courses', 'warning')
        except requests.RequestException as e:
            logger.error(f"API connection error: {str(e)}")
            recent_courses = []
            flash('API service is unavailable', 'danger')
            
        return render_template('index.html', recent_courses=recent_courses, current_year=datetime.now().year)
    
    @app.route("/courses")
    def courses_list():
        """List all courses"""
        try:
            response = requests.get(f"{API_BASE_URL}/courses/")
            if response.status_code == 200:
                # Sort courses by creation date (newest first)
                all_courses = sorted(
                    response.json(), 
                    key=lambda x: x.get('created_at', ''), 
                    reverse=True
                )
            else:
                all_courses = []
                flash('Unable to fetch courses', 'warning')
        except requests.RequestException as e:
            logger.error(f"API connection error: {str(e)}")
            all_courses = []
            flash('API service is unavailable', 'danger')
        
        return render_template('courses/list.html', courses=all_courses, current_year=datetime.now().year)
    
    @app.route("/courses/create", methods=["GET"])
    def create_course_form():
        """Display the course creation form"""
        return render_template('courses/create.html', current_year=datetime.now().year)
    
    @app.route("/courses/create", methods=["POST"])
    def create_course_submit():
        """Handle course creation form submission"""
        # Get form data
        topic = request.form.get('topic')
        depth = request.form.get('depth', 'beginner')
        target_audience = request.form.get('target_audience', 'General audience')
        course_duration = request.form.get('course_duration', '4 weeks')

        # Validate input
        if not topic:
            flash('Topic is required', 'danger')
            return redirect(url_for('create_course_form'))

        # Send request to API
        try:
            payload = {
                "topic": topic,
                "depth": depth,
                "target_audience": target_audience,
                "course_duration": course_duration
            }

            response = requests.post(f"{API_BASE_URL}/courses/", json=payload, allow_redirects=True)

            if response.status_code == 201:
                result = response.json()
                task_id = result.get('task_id')
                # Instead of redirecting, show a success page with the task ID
                flash('Course generation started', 'success')
                return render_template('courses/generation_started.html', 
                                      task_id=task_id, 
                                      topic=topic,
                                      current_year=datetime.now().year)
            else:
                flash(f'Error creating course: {response.text}', 'danger')
                return redirect(url_for('create_course_form'))

        except requests.RequestException as e:
            logger.error(f"API connection error: {str(e)}")
            flash('API service is unavailable', 'danger')
            return redirect(url_for('create_course_form'))
    
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
        
        # Redirect to the course view page
        return redirect(url_for('view_course', task_id=task_id))
    
    @app.route("/courses/<task_id>")
    def view_course(task_id):
        """View a specific course"""
        try:
            # Get course status from API
            response = requests.get(f"{API_BASE_URL}/courses/{task_id}/")
            
            if response.status_code != 200:
                flash('Course not found', 'danger')
                return redirect(url_for('courses_list'))
            
            course = response.json()
            course_data = None
            
            # If task is completed, get the course data
            if course.get("status") == "completed":
                try:
                    data_response = requests.get(f"{API_BASE_URL}/courses/{task_id}/download/")
                    if data_response.status_code == 200:
                        course_data = data_response.json()
                except Exception as e:
                    flash(f'Error loading course data: {str(e)}', 'danger')
            
        except requests.RequestException as e:
            logger.error(f"API connection error: {str(e)}")
            flash('API service is unavailable', 'danger')
            return redirect(url_for('courses_list'))
        
        return render_template('courses/view.html', 
                              course=course, 
                              course_data=course_data, 
                              current_year=datetime.now().year)
    
    @app.route("/courses/<task_id>/download")
    def download_course(task_id):
        """Download the course JSON file"""
        try:
            # Check if task exists and is completed via API
            response = requests.get(f"{API_BASE_URL}/courses/{task_id}")
            
            if response.status_code != 200:
                flash('Course not found', 'danger')
                return redirect(url_for('courses_list'))
            
            course = response.json()
            
            # Check if task is completed
            if course.get("status") != "completed":
                flash('Course generation not yet complete', 'warning')
                return redirect(url_for('view_course', task_id=task_id))
            
            # Get the course data
            data_response = requests.get(f"{API_BASE_URL}/courses/{task_id}/download/")
            
            if data_response.status_code != 200:
                flash('Course output file not found', 'danger')
                return redirect(url_for('view_course', task_id=task_id))
            
            # Save the file locally (temporarily)
            os.makedirs("temp_downloads", exist_ok=True)
            temp_file = os.path.join("temp_downloads", f"course_{task_id}.json")
            
            with open(temp_file, "w") as f:
                json.dump(data_response.json(), f, indent=2)
            
            return send_from_directory(
                os.path.abspath('temp_downloads'), 
                f"course_{task_id}.json",
                as_attachment=True,
                download_name=f"course_{task_id}.json"
            )
            
        except requests.RequestException as e:
            logger.error(f"API connection error: {str(e)}")
            flash('API service is unavailable', 'danger')
            return redirect(url_for('courses_list'))
    
    @app.route("/courses/<task_id>/refine", methods=["POST"])
    def refine_course_submit(task_id):
        """Handle course refinement form submission"""
        # Get form data
        refinement_type = request.form.get('refinement_type', 'general')
        instructions = request.form.get('instructions')
        
        # Validate input
        if not instructions:
            flash('Refinement instructions are required', 'danger')
            return redirect(url_for('view_course', task_id=task_id))
        
        # Send refinement request to API
        try:
            payload = {
                "refinement_type": refinement_type,
                "instructions": instructions
            }
            
            response = requests.post(f"{API_BASE_URL}/courses/{task_id}/refine/", json=payload, allow_redirects=True)
            
            if response.status_code == 202:
                result = response.json()
                refinement_id = result.get('refinement_id')
                flash('Course refinement started', 'success')
                return redirect(url_for('view_course', task_id=refinement_id))
            else:
                flash(f'Error refining course: {response.text}', 'danger')
                return redirect(url_for('view_course', task_id=task_id))
                
        except requests.RequestException as e:
            logger.error(f"API connection error: {str(e)}")
            flash('API service is unavailable', 'danger')
            return redirect(url_for('view_course', task_id=task_id))
    
    @app.route("/health")
    def health_check():
        """Health check endpoint"""
        # Check if API is available
        try:
            api_health = requests.get(f"{API_BASE_URL.split('/api')[0]}/health", timeout=2)
            api_status = "connected" if api_health.status_code == 200 else "disconnected"
        except:
            api_status = "disconnected"
            
        return jsonify({
            "status": "healthy",
            "api_status": api_status
        })
    
    @app.route("/api-docs")
    def api_docs():
        """Redirect to the API documentation"""
        api_docs_url = f"{API_BASE_URL.split('/api')[0]}/docs"
        return redirect(api_docs_url)
    
    @app.context_processor
    def inject_globals():
        """Inject global variables into templates"""
        return {
            'current_year': datetime.now().year
        }
    
    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))