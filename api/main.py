from flask import Flask, jsonify, request, send_from_directory
import os
from dotenv import load_dotenv
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Load environment variables
load_dotenv()

# Import routes
from routes.courses import courses_bp

def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__)
    
    # Register blueprints
    app.register_blueprint(courses_bp)
    
    @app.route("/health", methods=["GET"])
    def health_check():
        """Health check endpoint"""
        return jsonify({"status": "healthy"})
    
    @app.route("/", methods=["GET"])
    def home():
        """Home page"""
        return jsonify({
            "name": "Educational Course Generator API",
            "version": "1.0.0",
            "endpoints": {
                "health": "/health",
                "create_course": "/api/courses/",
                "get_course": "/api/courses/<task_id>",
                "download_course": "/api/courses/<task_id>/download",
                "refine_course": "/api/courses/<task_id>/refine"
            }
        })
    
    # Create output directory if it doesn't exist
    os.makedirs("output", exist_ok=True)
    
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))