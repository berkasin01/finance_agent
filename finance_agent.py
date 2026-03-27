import nest_asyncio
from langchain.agents import create_agent
from langchain.tools import tool
import requests
import pandas as pd
import os

# @tool("get_sentiment)", description="Return weather information for a given city", return_direct=False)
def get_ticker_sentiment(company: str, news_num: int = 1000 ):
        api_key = os.environ.get("POLYGON_API_KEY")
        header = {"Authorization": str(api_key)}
        params = {
            "ticker": company,
            "limit": news_num,
            "order": "desc"
        }
        get_news_url = 'https://api.polygon.io/v2/reference/news'
        response = requests.get(url=get_news_url, headers=header, params=params)

        news_response = response.json()
        news = news_response['results'][:25]
        return news



# agent = create_agent(
#     model="gemini-2.5-flash"
#     tools=[get_weather],
#     system_prompt="you are a good boy"
# )

print(get_ticker_sentiment(company="NVDA"))


