"""
Qualitative Analysis Tool
RAG-based tool for analyzing earnings call transcripts
"""
from langchain.tools import Tool
from langchain.chains import RetrievalQA
from langchain_community.vectorstores import Chroma
from utils.llm_provider import get_llm, get_embeddings
from utils.document_loader import DocumentLoader
from pathlib import Path
import logging
import json

logger = logging.getLogger(__name__)

# Global vectorstore (initialized once)
_vectorstore = None
_initialized = False


def initialize_vectorstore(transcripts_dir: str = "data/transcripts"):
    """Load transcripts and create vector store"""
    global _vectorstore, _initialized
    
    if _initialized:
        return _vectorstore
    
    try:
        # Check if directory exists
        if not Path(transcripts_dir).exists():
            logger.warning(f"Transcripts directory not found: {transcripts_dir}")
            return None
        
        # Load all transcripts
        document_loader = DocumentLoader(chunk_size=1000, chunk_overlap=150)
        documents = document_loader.load_directory(transcripts_dir, ".txt")
        
        if not documents:
            # Try PDF as fallback
            documents = document_loader.load_directory(transcripts_dir, ".pdf")
        
        if not documents:
            logger.warning("No transcripts found")
            return None
        
        # Get embeddings
        embeddings = get_embeddings()
        
        # Create vector store
        _vectorstore = Chroma.from_documents(
            documents=documents,
            embedding=embeddings,
            collection_name="tcs_transcripts"
        )
        _initialized = True
        logger.info(f"Initialized vectorstore with {len(documents)} chunks")
        return _vectorstore
        
    except Exception as e:
        logger.error(f"Error initializing vectorstore: {e}")
        return None


def analyze_transcripts(query: str) -> str:
    """
    Perform semantic search and analysis
    
    Args:
        query: Analysis query (e.g., "What is management's outlook on AI growth?")
    
    Returns:
        JSON string with analysis results
    """
    try:
        # Initialize vectorstore if needed
        vectorstore = initialize_vectorstore()
        
        if not vectorstore:
            return json.dumps({
                "error": "No transcripts loaded",
                "suggestion": "Add transcript files to data/transcripts/"
            })
        
        # Get LLM
        llm = get_llm(temperature=0.3)
        
        # Create retrieval QA chain
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=vectorstore.as_retriever(
                search_kwargs={"k": 4}  # Retrieve top 4 relevant chunks
            )
        )
        
        # Enhanced query for better analysis
        enhanced_query = f"""Based on the earnings call transcripts, answer this query:
{query}

Provide:
1. Direct quotes or paraphrased statements from management
2. Overall sentiment (positive/negative/neutral)
3. Key themes and strategic focus areas
4. Any risks or opportunities mentioned

Format as JSON."""
        
        result = qa_chain.run(enhanced_query)
        
        # Try to parse as JSON, or wrap in structure
        try:
            parsed = json.loads(result)
            return json.dumps(parsed, indent=2)
        except:
            # Create structured response
            return json.dumps({
                "query": query,
                "analysis": result,
                "source": "earnings_transcripts"
            }, indent=2)
            
    except Exception as e:
        logger.error(f"Error in qualitative analysis: {e}")
        return json.dumps({"error": str(e)})


# Create the tool
qualitative_analysis_tool = Tool(
    name="qualitative_analysis",
    func=analyze_transcripts,
    description=(
        "Performs semantic search and analysis on TCS earnings call transcripts. "
        "Input should be a query about management sentiment, strategic themes, "
        "or forward-looking statements. Returns relevant insights from past calls."
    )
)