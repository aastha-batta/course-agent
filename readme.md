# Educational Course Generator

An AI-powered system for automatically generating structured educational courses on any topic. This application uses a multi-agent architecture to research, structure, generate content, and validate educational courses.

## Overview

The Educational Course Generator is an API-based service that allows users to:

1. Generate complete educational courses on any topic
2. Specify desired depth (beginner, intermediate, advanced)
3. Set target audience and course duration
4. Refine course content with additional instructions
5. Download generated courses as structured JSON

The system employs multiple specialized agents working together to create comprehensive, well-structured educational content.

## System Architecture

![User Interface](https://drive.google.com/file/d/1NrkzjNm_loG4cfs0Q7YZRNgDRutfUW-t/view?usp=sharing)

### Core Agents

- **CoordinatorAgent**: Orchestrates the workflow between all other agents
- **ResearchAgent**: Gathers information on the topic from web and academic sources
- **StructureAgent**: Creates a logical course structure with modules and lessons
- **ContentGenerationAgent**: Produces detailed content for each lesson
- **ValidationAgent**: Ensures quality and suggests improvements

## Installation

### Prerequisites

- Python 3.8+
- Flask
- LangChain
- OpenAI API key
- Tavily API key (for research component)

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/educational-course-generator.git
   cd educational-course-generator
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create an `.env` file with required API keys and configuration:
   ```
   OPENAI_API_KEY=your_openai_api_key
   TAVILY_API_KEY=your_tavily_api_key
   LLM_MODEL=gpt-4-turbo  # or another OpenAI model
   PORT=5000              # Web interface port
   API_PORT=5001          # API server port
   API_BASE_URL=http://localhost:5001/api
   SECRET_KEY=your_secret_key  # For Flask sessions
   ```

## Usage

### Running the Application

The system consists of two components:

1. **API Server**: Handles course generation and processing
2. **Web Interface**: Provides a user-friendly frontend

```bash
# Start the API server
python main.py

# Start the web interface
python app.py
```

The API server will start on `http://localhost:5001` by default.
The web interface will be available at `http://localhost:5000`.

### Web Interface

The web interface provides a user-friendly way to interact with the course generation system:

- **Home Page**: Overview and quick access to recent courses
- **Course Creation**: Form to specify topic, depth, audience, and duration
- **Course List**: View all generated courses
- **Course View**: Detailed view of a specific course with its content
- **Course Download**: Download the complete course as JSON
- **Course Refinement**: Submit additional instructions to improve the course

### API Endpoints

- **POST /api/courses/**: Create a new course
  ```json
  {
    "topic": "Machine Learning",
    "depth": "intermediate",
    "target_audience": "Computer Science students",
    "course_duration": "6 weeks"
  }
  ```

- **GET /api/courses/{task_id}**: Check course generation status
- **GET /api/courses/{task_id}/download**: Download the complete course
- **POST /api/courses/{task_id}/refine**: Refine an existing course
  ```json
  {
    "refinement_type": "content",
    "instructions": "Add more practical exercises to each lesson"
  }
  ```

### Example Usage

### Web Interface

1. Start both the API server and web interface:
   ```bash
   # Terminal 1
   python main.py
   
   # Terminal 2
   python app.py
   ```

2. Open your browser and navigate to `http://localhost:5000`

3. Use the "Create Course" form to generate a new course:
   - Enter a topic (e.g., "Introduction to Python Programming")
   - Select depth (beginner, intermediate, advanced)
   - Specify target audience and course duration
   - Click "Generate Course"

4. Track the course generation progress and view/download when complete

### API Usage

```python
import requests
import json
import time

# Create a new course
response = requests.post(
    "http://localhost:5001/api/courses/",
    json={
        "topic": "Introduction to Python Programming",
        "depth": "beginner",
        "target_audience": "High school students",
        "course_duration": "4 weeks"
    }
)

task_id = response.json()["task_id"]
print(f"Course generation started. Task ID: {task_id}")

# Poll until complete
while True:
    status_response = requests.get(f"http://localhost:5001/api/courses/{task_id}")
    status = status_response.json()["status"]
    print(f"Status: {status}")
    
    if status in ["completed", "failed"]:
        break
        
    time.sleep(5)  # Wait 5 seconds before checking again

# Download the complete course
if status == "completed":
    course_response = requests.get(f"http://localhost:5001/api/courses/{task_id}/download")
    course_data = course_response.json()
    
    # Save to file
    with open("my_python_course.json", "w") as f:
        json.dump(course_data, f, indent=2)
    
    print("Course downloaded successfully!")
```

## Project Structure

```
educational-course-generator/
├── agents/
│   ├── __init__.py
│   ├── base_agent.py        # Abstract base class for all agents
│   ├── coordinator.py       # Orchestrates the workflow
│   ├── researcher.py        # Gathers information
│   ├── structurer.py        # Creates course structure
│   ├── content_generator.py # Generates detailed content
│   └── validator.py         # Validates and improves content
├── services/
│   ├── __init__.py
│   ├── llm_service.py       # LLM interaction service
│   └── research_service.py  # External research API client
├── utils/
│   ├── __init__.py
│   ├── json_cleaner.py      # Fixes JSON formatting issues
│   ├── content_formatter.py # Formats course output
│   └── logging_config.py    # Configures logging
├── templates/
│   ├── base.html            # Base template with layout
│   ├── index.html           # Home page
│   ├── partials/
│   │   ├── header.html      # Navigation header
│   │   ├── footer.html      # Page footer
│   │   └── course_card.html # Reusable course component
│   └── courses/
│       ├── create.html      # Course creation form
│       ├── list.html        # List of all courses
│       ├── view.html        # Single course view
│       ├── lookup.html      # Task ID lookup
│       └── generation_started.html # Success page
├── static/
│   ├── css/                 # Stylesheets
│   ├── js/                  # JavaScript files
│   └── img/                 # Images
├── main.py                  # API server entry point
├── app.py                   # Web interface entry point
├── config.py                # Configuration settings
├── requirements.txt         # Dependencies
└── README.md                # This file
```

## Course JSON Structure

Generated courses follow this structure:

```json
{
  "title": "Introduction to Python Programming",
  "description": "A beginner course designed for high school students...",
  "topic": "Python Programming",
  "depth": "beginner",
  "target_audience": "High school students",
  "course_duration": "4 weeks",
  "modules": [
    {
      "title": "Getting Started with Python",
      "description": "Basic concepts and setup",
      "duration": "1 week",
      "lessons": [
        {
          "title": "Installing Python and First Steps",
          "content": "Detailed lesson content...",
          "resources": [
            "Python.org documentation",
            "Intro to Programming with Python (e-book)"
          ]
        }
      ]
    }
  ],
  "references": [
    "Python Documentation, Python Software Foundation, 2023",
    "..."
  ]
}
```

## Acknowledgments

- This project uses LangChain for LLM orchestration
- The research component is powered by Tavily API
- The content generation is handled by OpenAI models