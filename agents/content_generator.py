from typing import Dict, Any, List
from .base_agent import BaseAgent
from langchain_core.messages import HumanMessage
from services.llm_service import get_llm
import json
import sys
import os
from utils.logging_config import setup_logging


logging = setup_logging(log_level="INFO")

# Add the project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.json_cleaner import clean_json_string

class ContentGenerationAgent(BaseAgent):
    """Agent responsible for generating detailed content for each lesson"""
    
    def __init__(self, name: str = "ContentGenerator"):
        super().__init__(name)
        self.llm = get_llm()
    
    async def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Generate content for each lesson in the course structure"""
        topic = inputs.get("topic", "")
        structure_str = inputs.get("structure", "")
        
        # logging.info the structure for debugging
        logging.info("\nStructure received by ContentGenerationAgent:")
        logging.info(structure_str[:500] + "..." if len(structure_str) > 500 else structure_str)
        
        try:
            # Use our cleaner to parse the JSON
            structure = clean_json_string(structure_str)
            
            # Extract course info
            course_title = structure.get("title", "")
            description = structure.get("description", "")
            modules = structure.get("modules", [])
            
            logging.info(f"\nSuccessfully parsed structure. Course title: {course_title}")
            logging.info(f"Number of modules: {len(modules)}")
            
            # Initialize the content structure
            content_structure = {
                "course_title": course_title,
                "description": description,
                "modules": [],
                "references": []
            }
            
            # Process ALL modules instead of just the first 2
            for module_index, module in enumerate(modules):
                module_title = module.get("title", "")
                module_content = {"title": module_title, "lessons": []}
                
                logging.info(f"\nProcessing module: {module_title}")
                
                # Process ALL lessons in the module instead of just the first 2
                for lesson_index, lesson in enumerate(module.get("lessons", [])):
                    lesson_title = lesson.get("title", "")
                    lesson_description = lesson.get("description", "")
                    
                    logging.info(f"  Generating content for lesson: {lesson_title}")
                    
                    # Generate detailed content for the lesson
                    content_prompt = f"""
                    Generate detailed educational content for a lesson titled "{lesson_title}" which is part of the module "{module_title}" in a course about {topic}.
                    
                    Lesson description: {lesson_description}
                    
                    Your task is to create:
                    1. Comprehensive lesson content (at least 250 words)
                    2. A list of 3-5 resources for further learning
                    
                    Format your response as:
                    
                    CONTENT:
                    [Your lesson content here]
                    
                    RESOURCES:
                    - [Resource 1]
                    - [Resource 2]
                    - [Resource 3]
                    """
                    
                    # Create a proper message object
                    message = HumanMessage(content=content_prompt)
                    
                    # Call the LLM with the message
                    content_response = await self.llm.ainvoke([message])
                    response_text = content_response.content
                    
                    # Parse the response
                    content_parts = response_text.split("RESOURCES:")
                    
                    lesson_content = content_parts[0].replace("CONTENT:", "").strip()
                    
                    resources = []
                    if len(content_parts) > 1:
                        resources_text = content_parts[1].strip()
                        resources = [
                            resource.strip().lstrip('-').strip() 
                            for resource in resources_text.split('\n') 
                            if resource.strip()
                        ]
                    
                    # Add to the content structure
                    module_content["lessons"].append({
                        "title": lesson_title,
                        "content": lesson_content,
                        "resources": resources
                    })
                
                content_structure["modules"].append(module_content)
            
            # Generate references
            logging.info("\nGenerating references...")
            references_prompt = f"""
            Generate 5-7 academic or professional references for a course on {topic}.
            Each reference should follow standard citation format.
            """
            
            # Create a message for references
            ref_message = HumanMessage(content=references_prompt)
            ref_response = await self.llm.ainvoke([ref_message])
            
            # Parse references (assuming one reference per line)
            references = [ref.strip() for ref in ref_response.content.strip().split('\n') if ref.strip()]
            content_structure["references"] = references
            
            logging.info("\nContent generation complete!")
            return {
                **inputs,
                "content_structure": content_structure
            }
            
        except json.JSONDecodeError as e:
            logging.error(f"\nJSON parsing error: {e}")
            logging.error("The first 100 characters of the structure string:")
            logging.error(structure_str[:100])
            
            return {
                **inputs,
                "error": f"Failed to parse course structure JSON: {str(e)}",
                "content_structure": {
                    "course_title": "Error in structure parsing",
                    "description": "Could not generate content due to structure format issues",
                    "modules": [],
                    "references": []
                }
            }
        except Exception as e:
            logging.info(f"\nUnexpected error in content generation: {str(e)}")
            
            return {
                **inputs,
                "error": f"Error in content generation: {str(e)}",
                "content_structure": {
                    "course_title": "Error in content generation",
                    "description": "An unexpected error occurred",
                    "modules": [],
                    "references": []
                }
            }