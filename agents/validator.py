from typing import Dict, Any
from .base_agent import BaseAgent
from langchain_core.messages import HumanMessage
from services.llm_service import get_llm
from utils.logging_config import setup_logging


logging = setup_logging(log_level="INFO")

class ValidationAgent(BaseAgent):
    """Agent responsible for validating and improving course content"""
    
    def __init__(self, name: str = "Validator"):
        super().__init__(name)
        self.llm = get_llm()
    
    async def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and improve the generated course content"""
        topic = inputs.get("topic", "")
        content_structure = inputs.get("content_structure", {})
        
        # Extract course information
        course_title = content_structure.get("course_title", "")
        description = content_structure.get("description", "")
        modules = content_structure.get("modules", [])
        
        validation_issues = []
        improvements = []
        
        # Validate overall course structure
        course_validation_prompt = f"""
        You are a quality assurance expert for educational content. Review this course on "{topic}" with the title "{course_title}" and description: "{description}".
        
        Evaluate:
        1. Is the course title clear and accurately reflects the content?
        2. Is the course description comprehensive and engaging?
        3. Does the overall structure make logical sense for the topic?
        
        Provide your assessment and suggest specific improvements.
        """
        
        # Create a message for course validation
        course_msg = HumanMessage(content=course_validation_prompt)
        course_response = await self.llm.ainvoke([course_msg])
        course_feedback = course_response.content
        
        # Store course-level feedback
        improvements.append({
            "type": "course_level",
            "feedback": course_feedback
        })
        
        # Validate each module and its lessons (limiting to 2 modules for testing)
        for module_index, module in enumerate(modules[:2]):
            module_title = module.get("title", "")
            module_lessons = module.get("lessons", [])
            
            logging.info(f"\nValidating module: {module_title}")
            
            # Check for lesson content quality and consistency
            if len(module_lessons) == 0:
                validation_issues.append(f"Module '{module_title}' has no lessons")
                continue
                
            # Validate a sample lesson from each module (first lesson)
            if module_lessons and len(module_lessons) > 0:
                sample_lesson = module_lessons[0]
                lesson_title = sample_lesson.get("title", "")
                lesson_content = sample_lesson.get("content", "")
                
                logging.info(f"  Validating lesson: {lesson_title}")
                
                lesson_validation_prompt = f"""
                Review this lesson titled "{lesson_title}" from the module "{module_title}" in a course about {topic}.
                
                Lesson content:
                {lesson_content[:1000]}... (truncated for brevity)
                
                Evaluate:
                1. Content accuracy: Is the information correct and up-to-date?
                2. Content completeness: Does it cover the topic thoroughly?
                3. Instructional quality: Is it clear and easy to understand?
                4. Engagement: Will it keep learners interested?
                
                Provide specific suggestions for improvement.
                """
                
                # Create a message for lesson validation
                lesson_msg = HumanMessage(content=lesson_validation_prompt)
                lesson_response = await self.llm.ainvoke([lesson_msg])
                lesson_feedback = lesson_response.content
                
                # Store lesson-level feedback
                improvements.append({
                    "type": "lesson_level",
                    "module": module_title,
                    "lesson": lesson_title,
                    "feedback": lesson_feedback
                })
        
        # Check for consistency across modules
        consistency_prompt = f"""
        Review the module structure for this course on "{topic}":
        
        {[module.get("title", "") for module in modules]}
        
        Evaluate:
        1. Do the modules flow logically from one to the next?
        2. Is there any redundancy or gaps in the curriculum?
        3. Is the difficulty progression appropriate?
        
        Provide feedback on the overall course structure.
        """
        
        # Create a message for consistency validation
        consistency_msg = HumanMessage(content=consistency_prompt)
        consistency_response = await self.llm.ainvoke([consistency_msg])
        consistency_feedback = consistency_response.content
        
        # Store structure-level feedback
        improvements.append({
            "type": "structure_level",
            "feedback": consistency_feedback
        })
        
        # Store validation results in a separate log but don't include in the content structure
        logging.info("\nValidation results:")
        logging.info(f"Issues: {validation_issues}")
        logging.info(f"Improvements: {improvements}")
        
        # Return the content structure without validation results
        logging.info("\nValidation complete!")
        return {
            **inputs,
            "content_structure": content_structure  
        }