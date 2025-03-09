from typing import Dict, Any, List
from .base_agent import BaseAgent
from utils.logging_config import setup_logging


logging = setup_logging(log_level="INFO")

class CoordinatorAgent(BaseAgent):
    """Agent responsible for orchestrating the course generation process"""
    
    def __init__(self, name: str = "Coordinator"):
        super().__init__(name)
        self.agents = {}
        self.workflow = []
    
    def register_agent(self, agent_name: str, agent: BaseAgent):
        """Register an agent with the coordinator"""
        self.agents[agent_name] = agent
    
    def set_workflow(self, workflow: List[str]):
        """Set the workflow as a sequence of agent names"""
        self.workflow = workflow
    
    async def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Process through the entire workflow"""
        current_input = inputs
        results = {"initial_input": inputs}
        
        for agent_name in self.workflow:
            if agent_name not in self.agents:
                raise ValueError(f"Agent {agent_name} not found in registered agents")
            
            agent = self.agents[agent_name]
            logging.info(f"Coordinator delegating to {agent_name}...")
            
            current_input = await agent.process(current_input)
            results[agent_name] = current_input
        
        return {
            "course": current_input,
            "process_results": results
        }