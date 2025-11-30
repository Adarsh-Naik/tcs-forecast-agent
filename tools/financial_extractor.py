"""
Financial Data Extractor Tool
Extracts key financial metrics from quarterly reports using LLM
"""
from langchain.tools import Tool
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from utils.llm_provider import get_llm
from utils.document_loader import DocumentLoader
from typing import Dict, Any
import json
import logging
import re

logger = logging.getLogger(__name__)


# Extraction prompt template
EXTRACTION_PROMPT = """You are a financial analyst expert. Extract key financial metrics from the provided quarterly report text.

Report Text:
{report_text}

Extract the following information and return ONLY a valid JSON object:
{{
    "quarter": "Q1/Q2/Q3/Q4",
    "year": 2024,
    "total_revenue": amount in crores,
    "net_profit": amount in crores,
    "operating_margin": percentage,
    "revenue_growth": percentage compared to previous quarter or year,
    "key_highlights": ["highlight1", "highlight2", ...],
    "segment_performance": {{"segment_name": "brief description"}}
}}

If any value is not found, use null. Be precise and extract only factual numbers mentioned in the report.

JSON Output:"""


def extract_financial_data(file_path: str) -> str:
    """
    Extract financial data from report
    
    Args:
        file_path: Path to financial report PDF or directory
    
    Returns:
        JSON string with extracted financial metrics
    """
    try:
        # Initialize LLM and document loader
        llm = get_llm(temperature=0.0)  # Deterministic for extraction
        document_loader = DocumentLoader(chunk_size=2000)
        
        # Load document(s)
        from pathlib import Path
        path = Path(file_path)
        
        if path.is_dir():
            documents = document_loader.load_directory(file_path, ".pdf")
        elif path.suffix == ".pdf":
            documents = document_loader.load_pdf(file_path)
        else:
            documents = document_loader.load_text(file_path)
        
        if not documents:
            return json.dumps({"error": "No documents loaded"})
        
        # Combine relevant chunks (first 5 usually contain financial summary)
        combined_text = "\n\n".join([doc.page_content for doc in documents[:5]])
        
        # Create extraction chain
        prompt = PromptTemplate(
            input_variables=["report_text"],
            template=EXTRACTION_PROMPT
        )
        extraction_chain = LLMChain(llm=llm, prompt=prompt)
        
        # Extract metrics using LLM
        result = extraction_chain.run(report_text=combined_text)
        
        # Parse and validate JSON
        try:
            parsed_result = json.loads(result.strip())
            logger.info(f"Successfully extracted metrics: {parsed_result.get('quarter', 'Unknown')}")
            return json.dumps(parsed_result, indent=2)
        except json.JSONDecodeError:
            # LLM might include extra text, try to extract JSON
            json_match = re.search(r'\{.*\}', result, re.DOTALL)
            if json_match:
                return json_match.group()
            return json.dumps({"error": "Failed to parse LLM output", "raw": result})
            
    except Exception as e:
        logger.error(f"Error in financial extraction: {e}")
        return json.dumps({"error": str(e)})


# Create the tool
financial_data_extractor_tool = Tool(
    name="financial_data_extractor",
    func=extract_financial_data,
    description=(
        "Extracts key financial metrics from TCS quarterly financial reports. "
        "Input should be a path to the report file or directory. "
        "Returns structured financial data including revenue, profit, margins, and trends."
    )
)