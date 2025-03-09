from langchain_openai import ChatOpenAI
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

def get_llm():
    """Get the LLM instance based on configuration"""
    return ChatOpenAI(
        model_name=config.LLM_MODEL,
        temperature=0.2,
        openai_api_key=config.OPENAI_API_KEY
    )