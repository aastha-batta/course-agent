from typing import Dict, Any
import os
from .base_agent import BaseAgent
from langchain_core.messages import HumanMessage
from services.llm_service import get_llm
from services.research_service import ResearchService
from utils.logging_config import setup_logging


logging = setup_logging(log_level="INFO")

class ResearchAgent(BaseAgent):
    """Agent responsible for gathering research for course content"""
    
    def __init__(self, name: str = "Researcher"):
        super().__init__(name)
        self.llm = get_llm()
        self.research_service = ResearchService()
    
    async def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Research content for the course"""
        topic = inputs.get("topic", "")
        depth = inputs.get("depth", "intermediate")
        
        logging.info(f"\nResearching topic: {topic} at {depth} level...")
        
        # Step 1: Gather raw research from various sources
        try:
            research_data = await self.research_service.gather_research(topic, depth)
            
            # Extract some information for the prompt
            web_sources = research_data.get("web_sources", [])
            academic_sources = research_data.get("academic_sources", [])
            
            # Prepare source summaries
            web_summaries = "\n\n".join([
                f"SOURCE {i+1}: {source.get('title', '')}\n{source.get('content', '')[:500]}..."
                for i, source in enumerate(web_sources[:3])
            ])
            
            academic_summaries = "\n\n".join([
                f"ACADEMIC SOURCE {i+1}: {source.get('title', '')}\n{source.get('content', '')[:500]}..."
                for i, source in enumerate(academic_sources[:2])
            ])
            
            logging.info(f"Gathered {len(web_sources)} web sources and {len(academic_sources)} academic sources")
        except Exception as e:
            logging.error(f"Error in research gathering: {str(e)}")
            web_summaries = "Error retrieving web sources."
            academic_summaries = "Error retrieving academic sources."
        
        # Step 2: Create a research synthesis using the LLM
        research_prompt = f"""
        You are a thorough researcher creating educational content about {topic} at a {depth} level.
        
        Here are some web sources about the topic:
        {web_summaries}
        
        Here are some academic sources about the topic:
        {academic_summaries}
        
        Based on these sources and your knowledge, research the following aspects:
        1. Core concepts and fundamentals of {topic}
        2. Latest developments and advancements
        3. Practical applications
        4. Common challenges and solutions
        5. Resources for further learning
        
        Provide a comprehensive research summary that could be used to create an educational course.
        Structure your response with clear headings for each section.
        """
        
        # Create a proper message object
        message = HumanMessage(content=research_prompt)
        
        # Call the LLM with the message
        research_response = await self.llm.ainvoke([message])
        research_content = research_response.content
        
        logging.info(f"Research synthesis complete: {len(research_content)} characters")
        
        return {
            **inputs,
            "research": research_content,
            "research_sources": {
                "web": [{"title": s.get("title", ""), "url": s.get("url", "")} for s in web_sources],
                "academic": [{"title": s.get("title", ""), "url": s.get("url", "")} for s in academic_sources]
            }
        }