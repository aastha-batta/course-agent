from typing import Dict, Any, List
from .base_agent import BaseAgent
from langchain_core.messages import HumanMessage
from services.llm_service import get_llm
from utils.logging_config import setup_logging


logging = setup_logging(log_level="INFO")

class StructureAgent(BaseAgent):
    """Agent responsible for structuring course content"""
    
    def __init__(self, name: str = "Structurer"):
        super().__init__(name)
        self.llm = get_llm()
    
    async def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Create a course structure based on research"""
        topic = inputs.get("topic", "")
        research = inputs.get("research", "")
        course_duration = inputs.get("course_duration", "6 weeks")
        
        # Extract number of weeks for appropriate module planning
        try:
            num_weeks = int(course_duration.split()[0])
        except (ValueError, IndexError):
            num_weeks = 6
        
        structure_prompt = f"""
        Based on the following research about "{topic}", create a well-structured course outline for a {course_duration} course.
        
        RESEARCH:
        {research}
        
        Your task is to:
        1. Create a course title
        2. Write a course description
        3. Identify exactly {num_weeks} logical modules (one module per week for a {course_duration} course)
        4. For each module, create 3-5 lessons
        5. Each lesson should have a title and brief description
        
        Format your response as VALID JSON with the following structure, with no extra text before or after:
        
        {{
            "title": "Course Title",
            "description": "Course Description",
            "course_duration": "{course_duration}",
            "modules": [
                {{
                    "title": "Module Title",
                    "description": "Module Description",
                    "duration": "1 week",
                    "lessons": [
                        {{
                            "title": "Lesson Title",
                            "description": "Lesson Description"
                        }}
                    ]
                }}
            ]
        }}
        
        IMPORTANT: Make sure to:
        - Create exactly {num_weeks} modules to match the {course_duration} course duration
        - Use double quotes for all keys and string values
        - Do not include trailing commas
        - Make sure the JSON is valid and can be parsed
        """
        
        # Create a proper message object
        message = HumanMessage(content=structure_prompt)
        
        # Call the LLM with the message
        structure_response = await self.llm.ainvoke([message])
        course_structure = structure_response.content
        
        # logging.info for debugging
        logging.info("\nStructure output from LLM:")
        logging.info(course_structure[:500] + "..." if len(course_structure) > 500 else course_structure)
        
        return {
            **inputs,
            "structure": course_structure
        }