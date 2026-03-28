# 📈 Investment Research Agent
[HERE IS THE LINK TO THE APP](https://financeagent-bottmvzfyresu9rrvojodd.streamlit.app/)
Multi-tool AI agent that pulls real-time financial data and gives you a full picture on any stock. Built with LangChain and Gemini.
Ask it something like "Give me the full picture on NVDA" and it'll hit all 4 tools in parallel, then synthesise everything into one answer.
## What it does
<img width="711" height="895" alt="Screenshot 2026-03-28 205334" src="https://github.com/user-attachments/assets/475a5677-c803-4538-aa6f-4209750f3769" />

The agent has 4 tools it can call depending on what you ask:

Stock Price — current price, daily change, volume, market cap, 52-week range, P/E ratio (via yfinance)
News Sentiment — pulls up to 1000 articles from Polygon API, counts positive/negative/neutral, summarises top headlines with reasoning
Fear & Greed Index — CNN's market fear indicator with current value, 5-day and 1-month trend, self-healing CSV that fetches fresh data from CNN's API if stale
Short Interest — NASDAQ short interest data with days to cover, share count, and change from prior period

The agent decides which tools to use based on your question. Ask about sentiment only? It'll just call that one. Ask for everything? It fires all 4 in parallel.
## Tech Stack

LangChain + LangGraph for agent orchestration
Gemini 2.5 Flash as the LLM
Polygon API for news + sentiment
CNN Fear & Greed API + historical CSV (3968 rows back to 2011)
NASDAQ API for short interest
yfinance for price data
Streamlit for the frontend

## Run it locally
bashgit clone https://github.com/berkasin01/finance_agent.git
cd finance_agent
pip install -r requirements.txt
Create a .streamlit/secrets.toml:
tomlGEMINI_API_KEY = "your_gemini_key"
POLYGON_API_KEY = "Bearer your_polygon_key"
Then:
bashstreamlit run finance_agent.py
## API Keys
You need two:

Gemini API Key — free from Google AI Studio
Polygon API Key — free tier at polygon.io

## Example Queries

Give me the full picture on NVDA — price, sentiment, fear levels, and short interest.
Should I be worried about AAPL right now?
What's the current market fear level?
What's the short interest situation on TSLA?

## Token Efficiency
Instead of dumping raw API responses into the LLM (which was 191k tokens for 50 articles), each tool pre-summarises the data and returns a compact string. A full 4-tool query runs at ~1,875 total tokens.
