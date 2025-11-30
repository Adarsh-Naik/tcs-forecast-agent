"""
LLM Provider Abstraction
Automatically switches between OpenAI and Ollama based on configuration
"""
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.chat_models import ChatOllama
from app.config import settings
import logging

logger = logging.getLogger(__name__)


def get_llm(temperature: float = 0.0):
    """
    Get LLM instance based on configuration
    
    Args:
        temperature: Controls randomness (0.0 = deterministic)
    
    Returns:
        LLM instance (OpenAI or Ollama)
    """
    if settings.use_openai:
        logger.info("Using OpenAI as LLM provider")
        return ChatOpenAI(
            model="gpt-4o-mini",
            temperature=temperature,
            api_key=settings.openai_api_key
        )
    else:
        logger.info(f"Using Ollama ({settings.ollama_model}) as LLM provider")
        return ChatOllama(
            base_url=settings.ollama_base_url,
            model=settings.ollama_model,
            temperature=temperature
        )


def get_embeddings():
    """
    Get embeddings model
    Uses OpenAI embeddings if API key provided, otherwise local embeddings
    
    Returns:
        Embeddings instance
    """
    if settings.use_openai:
        logger.info("Using OpenAI embeddings")
        return OpenAIEmbeddings(api_key=settings.openai_api_key)
    else:
        logger.info("Using local HuggingFace embeddings")
        return HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )


def get_provider_name() -> str:
    """Get the name of current LLM provider"""
    return "openai" if settings.use_openai else "ollama"