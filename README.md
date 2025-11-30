# TCS Financial Forecasting Agent

An AI-powered financial forecasting system that analyzes Tata Consultancy Services (TCS) quarterly reports and earnings transcripts to generate structured business outlook forecasts.

## Project Overview

### Architectural Approach

This application uses a **sequential orchestration pattern** with a multi-tool agent architecture. The system is designed to:

1. **Extract quantitative data** from financial reports using LLM-powered extraction
2. **Analyze qualitative insights** from earnings call transcripts using RAG (Retrieval-Augmented Generation)
3. **Synthesize information** into structured forecasts using a master LLM orchestrator
4. **Store results** in MySQL for audit and analysis

### Design Choices

**Sequential Tool Execution**: Instead of a complex ReAct agent that decides tool usage dynamically, we use a sequential approach where tools are executed in a predefined order:
- **Financial Data Extractor** → **Qualitative Analysis** → **Market Data** → **LLM Synthesis**

This design choice was made because:
- More reliable with local/remote Ollama models that may struggle with complex agent reasoning
- Predictable execution flow ensures all data sources are consulted
- Easier to debug and monitor each step
- Better error handling - if one tool fails, others can still provide value

**LLM Provider Abstraction**: The system supports both OpenAI and Ollama, automatically switching based on configuration. This allows for:
- Cost-effective local development with Ollama
- Production deployment with OpenAI for better performance
- Easy switching between providers via environment variables

**RAG for Transcripts**: Earnings call transcripts are embedded and stored in ChromaDB vector store, enabling semantic search for management statements, strategic themes, and forward-looking guidance.

### How the Agent Chains Thoughts and Tools

The forecasting process follows this flow:

```
User Request
    ↓
ForecastOrchestrator.generate_forecast()
    ↓
┌─────────────────────────────────────────┐
│ Step 1: Financial Data Extraction       │
│ - Load PDF reports from data/reports/   │
│ - Use LLM to extract structured metrics │
│ - Returns: Revenue, Profit, Margins     │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ Step 2: Qualitative Analysis            │
│ - Query vector store with task keywords │
│ - Retrieve relevant transcript chunks   │
│ - Use LLM to analyze sentiment/themes   │
│ - Returns: Management outlook, risks    │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ Step 3: Market Data (Optional)          │
│ - Fetch current stock price from Yahoo  │
│ - Returns: Price, change, market context│
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ Step 4: LLM Synthesis                   │
│ - Combine all tool outputs              │
│ - Use master prompt to generate forecast│
│ - Parse JSON response                   │
│ - Returns: Structured forecast          │
└─────────────────────────────────────────┘
    ↓
Database Logging & API Response
```

The orchestrator doesn't use dynamic tool selection - it always runs all tools sequentially and combines their outputs. The LLM then synthesizes this information into a structured forecast.

## Agent & Tool Design

### Master Prompt

The system uses a master prompt (`AGENT_SYSTEM_PROMPT` in `agent/prompts.py`) that defines the agent's role and output requirements:

```
You are a Financial Forecasting AI Agent specializing in analyzing Tata Consultancy Services (TCS).

Your role is to:
1. Analyze financial reports and extract quantitative metrics
2. Review earnings call transcripts for qualitative insights
3. Synthesize information to generate forward-looking forecasts
4. Provide structured, actionable business outlook

Analysis Framework:
1. GATHER: Use tools to collect financial data and qualitative insights
2. ANALYZE: Identify trends, patterns, and anomalies
3. SYNTHESIZE: Combine quantitative and qualitative findings
4. FORECAST: Generate forward-looking outlook with reasoning

Output Requirements:
Your final answer MUST be a valid JSON object with this exact structure:
{
    "summary": "2-3 sentence executive summary",
    "financial_trends": [...],
    "management_outlook": {...},
    "risks_and_opportunities": [...],
    "quarterly_forecast": "...",
    "confidence_level": "high/medium/low",
    "data_sources_used": [...]
}
```

### Tools

#### 1. Financial Data Extractor (`tools/financial_extractor.py`)

**Purpose**: Extracts structured financial metrics from quarterly PDF reports.

**How it works**:
- Uses `DocumentLoader` to load and chunk PDF reports
- Sends first 5 chunks (usually contain financial summary) to LLM
- LLM extracts metrics using a structured prompt
- Returns JSON with: quarter, revenue, profit, margins, growth rates, highlights

**Input**: File path or directory containing PDF reports  
**Output**: JSON string with financial metrics  
**LLM Temperature**: 0.0 (deterministic extraction)

**Example Output**:
```json
{
  "quarter": "Q3",
  "year": 2024,
  "total_revenue": 60500.0,
  "net_profit": 11000.0,
  "operating_margin": 25.5,
  "revenue_growth": 2.1,
  "key_highlights": ["Strong digital growth", "Margin expansion"]
}
```

#### 2. Qualitative Analysis Tool (`tools/qualitative_analysis.py`)

**Purpose**: Performs semantic search on earnings call transcripts to extract management insights.

**How it works**:
- Initializes ChromaDB vector store with transcript embeddings (one-time setup)
- Uses RAG (Retrieval-Augmented Generation) with semantic search
- Retrieves top 4 relevant chunks based on query
- LLM analyzes retrieved content for sentiment, themes, and strategic focus
- Returns structured analysis of management statements

**Input**: Query string (e.g., "What is management's outlook on AI?")  
**Output**: JSON string with analysis, sentiment, and key statements  
**LLM Temperature**: 0.3 (slightly creative for analysis)  
**Embeddings**: Uses HuggingFace `all-MiniLM-L6-v2` (local) or OpenAI embeddings

**Example Output**:
```json
{
  "query": "What is management's outlook on AI?",
  "analysis": "Management expressed strong optimism...",
  "sentiment": "positive",
  "key_statements": ["AI is a key growth driver", "Investing heavily in GenAI"]
}
```

#### 3. Market Data Tool (`tools/market_data.py`)

**Purpose**: Fetches current stock price and market context from Yahoo Finance API.

**How it works**:
- Makes HTTP request to Yahoo Finance API (no authentication required)
- Extracts current price, previous close, day range
- Calculates price change and percentage change
- Returns structured market data

**Input**: Stock symbol (default: "TCS.NS" for NSE)  
**Output**: JSON string with price, change, and market metrics  
**External API**: Yahoo Finance (free, no key required)

**Example Output**:
```json
{
  "symbol": "TCS.NS",
  "current_price": 3850.50,
  "previous_close": 3820.00,
  "change": 30.50,
  "change_percent": 0.80,
  "day_range": {"low": 3830.00, "high": 3860.00}
}
```

### Orchestrator Logic

The `ForecastOrchestrator` class (`agent/orchestrator.py`) coordinates all tools:

1. **Sequential Execution**: Runs tools in fixed order (financial → transcripts → market)
2. **Error Handling**: If a tool fails, continues with others and logs the failure
3. **Data Combination**: Combines all tool outputs into a single context
4. **LLM Synthesis**: Sends combined data to LLM with structured prompt
5. **JSON Parsing**: Extracts JSON from LLM response (handles markdown code blocks, extra text)
6. **Fallback**: If JSON parsing fails, creates minimal valid structure

The synthesis prompt instructs the LLM to generate a specific JSON structure matching the `ForecastOutput` model.

## Setup Instructions

### Prerequisites

- Python 3.10 or higher
- MySQL 8.0 or higher
- Ollama (for local LLM) OR OpenAI API key

### Step 1: Clone and Navigate

```bash
cd /path/to/tcs-forecast-agent
```

### Step 2: Create Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```
If found any dependency issue, use this command
```bash
pip install -r req.txt
```

### Step 4: Set Up MySQL Database

1. **Start MySQL service**:
   ```bash
   sudo systemctl start mysql  # Linux
   # OR
   brew services start mysql  # macOS
   ```

2. **Create database and tables**:
   ```bash
   mysql -u root -p < setup.sql
   ```

3. **Verify database**:
   ```bash
   mysql -u root -p -e "SHOW TABLES;" tcs_forecast
   ```
   Should show: `forecast_logs` and `financial_metrics`

### Step 5: Configure LLM Provider

Choose **ONE** of the following options:

#### Option A: Use Ollama (Local/Remote)

1. **If using local Ollama**:
   ```bash
   # Install Ollama (if not installed)
   curl -fsSL https://ollama.com/install.sh | sh
   
   # Pull required model
   ollama pull gemma2:9b
   
   # Verify model is available
   ollama list
   ```

2. **Set below configurations in `.env` file** (or update `app/config.py` defaults):
   ```bash
   # For local Ollama
   OLLAMA_BASE_URL=http://localhost:11434
   OLLAMA_MODEL=gemma2:9b
   ```

3. **If using remote Ollama** (via ngrok or other tunnel):
   ```bash
   OLLAMA_BASE_URL=https://your-ngrok-url.ngrok-free.app
   OLLAMA_MODEL=gemma2:9b
   ```

#### Option B: Use OpenAI

1. **Get API key** from https://platform.openai.com/api-keys

2. **Set Key in `.env` file**:
   ```bash
   OPENAI_API_KEY=sk-your-api-key-here
   ```

   The system will automatically use OpenAI if `OPENAI_API_KEY` is set.

### Step 6: Configure Database Credentials

Create or update `.env` file with MySQL credentials:

```bash
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_mysql_password <<-- MySQL password here
MYSQL_DATABASE=tcs_forecast
```

**Note**: If no `.env` file exists, the system uses defaults from `app/config.py`:
- Host: `localhost`
- Port: `3306`
- User: `root`
- Password: `your_mysql_password`
- Database: `tcs_forecast`

### Step 7: Prepare Data Files

Ensure your data directories exist and contain files:

```bash
# Check data structure
ls -la data/reports/    # Should contain TCS quarterly PDFs
ls -la data/transcripts/ # Should contain earnings call transcripts
```

The application expects:
- **Financial Reports**: PDF files in `data/reports/` (e.g., `TCS_Q2_FY2024.pdf`)
- **Transcripts**: PDF or TXT files in `data/transcripts/` (e.g., `TCS_Q2_FY2024_Transcript.pdf`)

Already added some pdf files in data directory, if you want more to be added visit https://www.screener.in/company/TCS/consolidated/#documents and get the pdf files

### Step 8: Verify Configuration

Run a quick test to verify everything is configured:

```bash
python3 -c "from app.config import settings; print(f'LLM: {settings.use_openai and \"OpenAI\" or \"Ollama\"}'); print(f'DB: {settings.database_url.split(\"@\")[1] if \"@\" in settings.database_url else \"Not configured\"}')"
```

### Troubleshooting Setup

**MySQL Connection Issues**:
- Verify MySQL is running: `sudo systemctl status mysql`
- Check credentials in `.env` file
- Test connection: `mysql -u root -p -e "SELECT 1;"`

**Ollama Model Not Found**:
- Check model is pulled: `ollama list`
- Pull model: `ollama pull gemma2:9b`
- Verify Ollama is running: `curl http://localhost:11434/api/tags`

**OpenAI API Issues**:
- Verify API key is set: `echo $OPENAI_API_KEY`
- Check API key is valid and has credits
- Ensure no network firewall blocking OpenAI

## How to Run

### Start the FastAPI Server

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Verify Server is Running

1. **Health Check**:
   ```bash
   curl http://localhost:8000/health
   ```

2. **Open API Documentation**:
   - Swagger UI: http://localhost:8000/docs

### API Endpoints

- **GET `/`**: Root health check
- **GET `/health`**: Detailed health check with LLM provider info
- **POST `/forecast`**: Generate forecast (requires JSON body with `task` field)
- **GET `/logs`**: Retrieve recent forecast logs (optional `limit` query param)

Use API /forecast with request. 
Example request: 
  {
    "task": "Analyze TCS financial data from the last 2 quarters and provide a brief forecast for the upcoming quarter."
  }

### Expected Output

The forecast endpoint returns a structured JSON response:

```json
{
  "status": "success",
  "timestamp": "2024-11-29T01:00:00",
  "execution_time_seconds": 15.23,
  "tools_used": ["financial_data_extractor", "qualitative_analysis", "market_data"],
  "forecast": {
    "summary": "TCS shows strong growth...",
    "financial_trends": [...],
    "management_outlook": {...},
    "risks_and_opportunities": [...],
    "quarterly_forecast": "...",
    "confidence_level": "high",
    "data_sources_used": [...]
  },
  "log_id": 1
}
```

---

## Project Structure

```
tcs-forecast-agent/
├── app/
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Configuration management
│   ├── database.py          # Database models and session
│   └── models.py            # Pydantic request/response models
├── agent/
│   ├── orchestrator.py     # Main agent orchestration logic
│   └── prompts.py           # Master agent prompts
├── tools/
│   ├── financial_extractor.py    # Financial data extraction tool
│   ├── qualitative_analysis.py   # RAG-based transcript analysis
│   └── market_data.py            # Market data fetching tool
├── utils/
│   ├── llm_provider.py     # LLM provider abstraction
│   ├── document_loader.py  # PDF/text document loading
│   └── logger.py           # Logging utilities
├── data/
│   ├── reports/             # Financial report PDFs
│   └── transcripts/         # Earnings call transcripts
├── requirements.txt         # Python dependencies
├── setup.sql               # Database schema
├── Test1.py               # Test script
└── README.md              # This file
```

