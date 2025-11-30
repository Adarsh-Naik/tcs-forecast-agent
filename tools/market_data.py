"""
Market Data Tool (Optional)
Fetches live market data for additional context
"""
from langchain.tools import Tool
import requests
import json
import logging

logger = logging.getLogger(__name__)


def fetch_market_data(symbol: str = "TCS.NS") -> str:
    """
    Fetch market data
    
    Args:
        symbol: Stock symbol (default: TCS.NS for NSE)
    
    Returns:
        JSON string with market data
    """
    try:
        # Example using Yahoo Finance API (free, no key required)
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
        params = {
            "interval": "1d",
            "range": "1mo"
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # Extract relevant information
            result = data.get("chart", {}).get("result", [{}])[0]
            meta = result.get("meta", {})
            
            market_data = {
                "symbol": symbol,
                "current_price": meta.get("regularMarketPrice"),
                "previous_close": meta.get("previousClose"),
                "currency": meta.get("currency"),
                "exchange": meta.get("exchangeName"),
                "timestamp": meta.get("regularMarketTime"),
                "day_range": {
                    "low": meta.get("regularMarketDayLow"),
                    "high": meta.get("regularMarketDayHigh")
                }
            }
            
            # Calculate change
            if market_data["current_price"] and market_data["previous_close"]:
                change = market_data["current_price"] - market_data["previous_close"]
                change_percent = (change / market_data["previous_close"]) * 100
                market_data["change"] = round(change, 2)
                market_data["change_percent"] = round(change_percent, 2)
            
            logger.info(f"Fetched market data for {symbol}")
            return json.dumps(market_data, indent=2)
        else:
            return json.dumps({
                "error": f"Failed to fetch data: {response.status_code}",
                "symbol": symbol
            })
            
    except Exception as e:
        logger.error(f"Error fetching market data: {e}")
        return json.dumps({
            "error": str(e),
            "symbol": symbol,
            "note": "Market data unavailable"
        })


# Create the tool
market_data_tool = Tool(
    name="market_data",
    func=fetch_market_data,
    description=(
        "Fetches current stock price and market data for TCS. "
        "Input should be the stock symbol (e.g., 'TCS' or 'TCS.NS' for NSE). "
        "Returns current price, change, and market sentiment indicators."
    )
)