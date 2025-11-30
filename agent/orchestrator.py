"""
Agent Orchestrator
Main agent logic that coordinates tools and generates forecasts
"""
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from tools.financial_extractor import extract_financial_data
from tools.qualitative_analysis import analyze_transcripts
from tools.market_data import fetch_market_data
from agent.prompts import AGENT_SYSTEM_PROMPT
from utils.llm_provider import get_llm, get_provider_name
import json
import logging
import re

logger = logging.getLogger(__name__)


class ForecastOrchestrator:
    """
    Orchestrates the forecasting process using multiple tools
    Simple sequential approach - works better with Ollama
    """
    
    def __init__(self, reports_dir: str = "data/reports", 
                 transcripts_dir: str = "data/transcripts"):
        """
        Initialize orchestrator with tools
        
        Args:
            reports_dir: Directory containing financial reports
            transcripts_dir: Directory containing earnings transcripts
        """
        self.llm = get_llm(temperature=0.2)
        self.reports_dir = reports_dir
        self.transcripts_dir = transcripts_dir
    
    def generate_forecast(self, task: str) -> dict:
        """
        Generate forecast based on task description
        Uses simple sequential tool execution (better for Ollama)
        
        Args:
            task: The forecasting task
        
        Returns:
            Dictionary containing forecast and metadata
        """
        try:
            logger.info(f"Starting forecast generation: {task}")
            
            tools_used = []
            tool_outputs = []
            
            # Step 1: Extract financial data
            logger.info("Step 1: Extracting financial data...")
            try:
                financial_data = extract_financial_data(self.reports_dir)
                tool_outputs.append(f"Financial Data:\n{financial_data}")
                tools_used.append("financial_data_extractor")
                logger.info("✅ Financial data extracted")
            except Exception as e:
                logger.warning(f"Financial extraction failed: {e}")
                tool_outputs.append(f"Financial Data: Not available - {str(e)}")
            
            # Step 2: Analyze transcripts
            logger.info("Step 2: Analyzing earnings transcripts...")
            try:
                # Create a relevant query from the task
                transcript_query = self._extract_transcript_query(task)
                transcript_analysis = analyze_transcripts(transcript_query)
                tool_outputs.append(f"Transcript Analysis:\n{transcript_analysis}")
                tools_used.append("qualitative_analysis")
                logger.info("✅ Transcripts analyzed")
            except Exception as e:
                logger.warning(f"Transcript analysis failed: {e}")
                tool_outputs.append(f"Transcript Analysis: Not available - {str(e)}")
            
            # Step 3: Get market data (optional)
            logger.info("Step 3: Fetching market data...")
            try:
                market_data = fetch_market_data("TCS.NS")
                tool_outputs.append(f"Market Data:\n{market_data}")
                tools_used.append("market_data")
                logger.info("✅ Market data fetched")
            except Exception as e:
                logger.warning(f"Market data fetch failed: {e}")
                tool_outputs.append(f"Market Data: Not available - {str(e)}")
            
            # Step 4: Synthesize with LLM
            logger.info("Step 4: Synthesizing forecast with LLM...")
            combined_data = "\n\n".join(tool_outputs)
            
            synthesis_prompt = f"""Based on the following data about TCS, generate a comprehensive forecast.

Task: {task}

Available Data:
{combined_data}

Generate a forecast as a JSON object with this exact structure:
{{
    "summary": "2-3 sentence executive summary",
    "financial_trends": [
        {{
            "metric": "Revenue/Profit/Margin",
            "trend": "increasing/decreasing/stable",
            "percentage_change": 5.2,
            "analysis": "Brief explanation"
        }}
    ],
    "management_outlook": {{
        "sentiment": "positive/negative/neutral",
        "key_statements": ["statement1", "statement2"],
        "strategic_focus": ["focus1", "focus2"]
    }},
    "risks_and_opportunities": [
        {{
            "type": "risk" or "opportunity",
            "description": "Clear description",
            "potential_impact": "high/medium/low"
        }}
    ],
    "quarterly_forecast": "Detailed forecast for next quarter",
    "confidence_level": "high/medium/low",
    "data_sources_used": {json.dumps(tools_used)}
}}

Return ONLY the JSON object, no other text."""

            # Use LLM to synthesize
            response = self.llm.invoke(synthesis_prompt)
            
            # Extract content based on provider
            if get_provider_name() == "openai":
                output_text = response.content
            else:
                # Ollama returns different format
                output_text = response.content if hasattr(response, 'content') else str(response)
            
            logger.info("✅ LLM synthesis complete")
            
            # Parse JSON from output
            forecast_json = self._extract_json(output_text)
            
            return {
                "forecast": forecast_json,
                "tools_used": tools_used,
                "raw_output": output_text
            }
            
        except Exception as e:
            logger.error(f"Error generating forecast: {e}")
            raise
    
    def _extract_transcript_query(self, task: str) -> str:
        """
        Extract a relevant query for transcript analysis
        
        Args:
            task: Original task
            
        Returns:
            Query string for transcripts
        """
        # Simple extraction - look for keywords
        task_lower = task.lower()
        
        if "ai" in task_lower or "artificial intelligence" in task_lower:
            return "What is management's outlook on AI and digital transformation?"
        elif "outlook" in task_lower or "forecast" in task_lower:
            return "What is management's forward-looking guidance and outlook?"
        elif "risk" in task_lower:
            return "What risks and challenges did management discuss?"
        else:
            return "What are the key themes and strategic focus areas discussed by management?"
    
    def _extract_json(self, text: str) -> dict:
        """
        Extract JSON from LLM output
        
        Args:
            text: Raw text output from LLM
        
        Returns:
            Parsed JSON dictionary
        """
        try:
            # Try direct JSON parse
            return json.loads(text.strip())
        except json.JSONDecodeError:
            # Try to find JSON block in text
            # Look for JSON between ```json and ``` or just { and }
            json_patterns = [
                r'```json\s*(\{.*?\})\s*```',
                r'```\s*(\{.*?\})\s*```',
                r'(\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\})'
            ]
            
            for pattern in json_patterns:
                match = re.search(pattern, text, re.DOTALL)
                if match:
                    try:
                        return json.loads(match.group(1))
                    except:
                        continue
            
            # Last resort: try to extract just the outer braces
            start = text.find('{')
            end = text.rfind('}')
            if start != -1 and end != -1:
                try:
                    return json.loads(text[start:end+1])
                except:
                    pass
            
            # Fallback: create minimal valid structure
            logger.warning("Could not parse JSON from output, using fallback")
            return {
                "summary": "Analysis completed. Check logs for full details.",
                "financial_trends": [
                    {
                        "metric": "General Analysis",
                        "trend": "stable",
                        "percentage_change": 0.0,
                        "analysis": text[:200] if len(text) > 200 else text
                    }
                ],
                "management_outlook": {
                    "sentiment": "neutral",
                    "key_statements": ["See raw output for details"],
                    "strategic_focus": ["Multiple areas"]
                },
                "risks_and_opportunities": [
                    {
                        "type": "opportunity",
                        "description": "Analysis in progress",
                        "potential_impact": "medium"
                    }
                ],
                "quarterly_forecast": text[:500] if len(text) > 500 else text,
                "confidence_level": "medium",
                "data_sources_used": ["analysis_tools"]
            }


# """
# Agent Orchestrator
# Main agent logic that coordinates tools and generates forecasts
# """
# from langchain.agents import AgentExecutor, create_react_agent
# from langchain.prompts import PromptTemplate
# from tools.financial_extractor import financial_data_extractor_tool
# from tools.qualitative_analysis import qualitative_analysis_tool
# from tools.market_data import market_data_tool
# from agent.prompts import AGENT_SYSTEM_PROMPT
# from utils.llm_provider import get_llm
# import json
# import logging
# import re

# logger = logging.getLogger(__name__)


# class ForecastOrchestrator:
#     """
#     Orchestrates the forecasting process using multiple tools
#     """
    
#     def __init__(self, reports_dir: str = "data/reports", 
#                  transcripts_dir: str = "data/transcripts"):
#         """
#         Initialize orchestrator with tools
        
#         Args:
#             reports_dir: Directory containing financial reports
#             transcripts_dir: Directory containing earnings transcripts
#         """
#         self.llm = get_llm(temperature=0.2)
#         self.reports_dir = reports_dir
#         self.transcripts_dir = transcripts_dir
        
#         # Initialize tools (now they're simple Tool objects)
#         self.tools = [
#             financial_data_extractor_tool,
#             qualitative_analysis_tool,
#             market_data_tool
#         ]
        
#         # Create agent
#         self.agent_executor = self._create_agent()
    
#     def _create_agent(self):
#         """Create the ReAct agent with tools"""
        
#         # Agent prompt template
#         template = f"""{AGENT_SYSTEM_PROMPT}

# TOOLS:
# {{tools}}

# TOOL NAMES: {{tool_names}}

# Question: {{input}}

# Thought: Let me think step by step about what data I need to gather.
# {{agent_scratchpad}}"""
        
#         prompt = PromptTemplate.from_template(template)
        
#         # Create ReAct agent
#         agent = create_react_agent(
#             llm=self.llm,
#             tools=self.tools,
#             prompt=prompt
#         )
        
#         # Create executor with retry logic
#         agent_executor = AgentExecutor(
#             agent=agent,
#             tools=self.tools,
#             verbose=True,
#             max_iterations=10,
#             handle_parsing_errors=True,
#             return_intermediate_steps=True
#         )
        
#         return agent_executor
    
#     def generate_forecast(self, task: str) -> dict:
#         """
#         Generate forecast based on task description
        
#         Args:
#             task: The forecasting task
        
#         Returns:
#             Dictionary containing forecast and metadata
#         """
#         try:
#             logger.info(f"Starting forecast generation: {task}")
            
#             # Enhance task with data paths
#             enhanced_task = f"""{task}

# Use these data sources:
# - Financial reports directory: {self.reports_dir}
# - Earnings transcripts directory: {self.transcripts_dir}

# Steps:
# 1. Extract financial metrics from recent reports using financial_data_extractor tool with path: {self.reports_dir}
# 2. Analyze earnings transcripts for qualitative insights using qualitative_analysis tool
# 3. Optionally get current market data using market_data tool with symbol: TCS.NS
# 4. Synthesize all information into forecast

# Provide final answer as structured JSON matching the required format."""
            
#             # Execute agent
#             result = self.agent_executor.invoke({"input": enhanced_task})
            
#             # Extract tools used
#             tools_used = []
#             if "intermediate_steps" in result:
#                 for step in result["intermediate_steps"]:
#                     if len(step) > 0 and hasattr(step[0], 'tool'):
#                         tools_used.append(step[0].tool)
            
#             # Parse output
#             output_text = result.get("output", "")
#             forecast_json = self._extract_json(output_text)
            
#             return {
#                 "forecast": forecast_json,
#                 "tools_used": list(set(tools_used)) if tools_used else ["agent"],
#                 "raw_output": output_text
#             }
            
#         except Exception as e:
#             logger.error(f"Error generating forecast: {e}")
#             raise
    
#     def _extract_json(self, text: str) -> dict:
#         """
#         Extract JSON from LLM output
        
#         Args:
#             text: Raw text output from agent
        
#         Returns:
#             Parsed JSON dictionary
#         """
#         try:
#             # Try direct JSON parse
#             return json.loads(text)
#         except json.JSONDecodeError:
#             # Try to find JSON block in text
#             json_match = re.search(r'\{.*\}', text, re.DOTALL)
#             if json_match:
#                 try:
#                     return json.loads(json_match.group())
#                 except:
#                     pass
            
#             # Fallback: create minimal valid structure
#             logger.warning("Could not parse JSON from output, using fallback")
#             return {
#                 "summary": "Analysis completed but output format needs refinement. Please check logs for details.",
#                 "financial_trends": [
#                     {
#                         "metric": "General Analysis",
#                         "trend": "stable",
#                         "percentage_change": 0.0,
#                         "analysis": text[:200] if len(text) > 200 else text
#                     }
#                 ],
#                 "management_outlook": {
#                     "sentiment": "neutral",
#                     "key_statements": ["Analysis in progress"],
#                     "strategic_focus": ["Review agent logs for details"]
#                 },
#                 "risks_and_opportunities": [
#                     {
#                         "type": "opportunity",
#                         "description": "Further analysis needed",
#                         "potential_impact": "medium"
#                     }
#                 ],
#                 "quarterly_forecast": text[:500] if len(text) > 500 else text,
#                 "confidence_level": "low",
#                 "data_sources_used": ["agent_output"]
#             }