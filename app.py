import asyncio
import json
from datetime import datetime
from typing import Dict, Any, List
from agents.coordinator import CoordinatorAgent
from agents.researcher import ResearchAgent
from agents.structurer import StructureAgent
from agents.content_generator import ContentGenerationAgent
from agents.validator import ValidationAgent
from models.course import Course, Module, Lesson
from utils.logging_config import setup_logging


logging = setup_logging(log_level="INFO")
logging.info("Application starting...")


async def main():
    logging.info("\n=== AI-Powered Course Generator ===\n")
    
    # Create agents
    coordinator = CoordinatorAgent()
    researcher = ResearchAgent()
    structurer = StructureAgent()
    content_generator = ContentGenerationAgent()
    validator = ValidationAgent()
    
    # Register agents with the coordinator
    coordinator.register_agent("researcher", researcher)
    coordinator.register_agent("structurer", structurer)
    coordinator.register_agent("content_generator", content_generator)
    coordinator.register_agent("validator", validator)
    
    # Define the workflow
    coordinator.set_workflow(["researcher", "structurer", "content_generator", "validator"])
    
    # Example input
    input_data = {
        "topic": "Artificial Intelligence in Healthcare",
        "depth": "advanced",
        "target_audience": "Healthcare professionals and AI researchers",
        "course_duration": "6 weeks"
    }
    
    logging.info(f"Generating course on: {input_data['topic']}")
    logging.info(f"Depth: {input_data['depth']}")
    logging.info(f"Target audience: {input_data['target_audience']}")
    logging.info(f"Course Duration: {input_data['course_duration']}")
    logging.info("\nStarting workflow...\n")
    
    # Process through the workflow
    result = await coordinator.process(input_data)
    
    # Extract the final course
    final_course = Course.from_dict(result.get("course", {}).get("content_structure", {}))
    final_course.topic = input_data.get("topic", "")
    final_course.depth = input_data.get("depth", "intermediate")
    final_course.course_duration = input_data.get("course_duration", "Unknown Duration")
    
    # Use the course's built-in method to adjust modules
    final_course.adjust_modules_to_duration()
    
    # Save structured course output
    with open("course_structure.json", "w") as f:
        json.dump(final_course.to_dict(), f, indent=2)
        logging.info("Course structure saved to course_structure.json")
    
    logging.info("\n=== Course Generation Complete ===\n")
    logging.info(f"Course Title: {final_course.title}")
    logging.info(f"Number of Modules: {len(final_course.modules)}")
    logging.info(f"Course Duration: {final_course.course_duration}")
    
if __name__ == "__main__":
    asyncio.run(main())