import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain.tools import tool
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()


@tool("get_ticker_sentiment", description="Get Stock News and its sentiment, you can also get up to 1000 news, can always get less too", return_direct=False)
def get_ticker_sentiment(company: str, news_num: int = 30):
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
    news = news_response['results']
    news_dict = {}
    for idx, e in enumerate(news):
        news_dict[idx] = {}

        publisher = e['publisher']["name"]
        news_dict[idx]["publisher"] = publisher

        title = e["title"]
        news_dict[idx]["title"] = title

        time = e["published_utc"]
        news_dict[idx]["time"] = time

        article_url = e["article_url"]
        news_dict[idx]["article_url"] = article_url

        insights = e["insights"]

        for i in insights:
            if i["ticker"] == company:
                ticker = i["ticker"]
                news_dict[idx]["ticker"] = ticker

                sentiment = i["sentiment"]
                news_dict[idx]["sentiment"] = sentiment

                sentiment_reasoning = i["sentiment_reasoning"]
                news_dict[idx]["sentiment_reasoning"] = sentiment_reasoning

    positive = sum(1 for v in news_dict.values() if v.get("sentiment") == "positive")
    negative = sum(1 for v in news_dict.values() if v.get("sentiment") == "negative")
    neutral = sum(1 for v in news_dict.values() if v.get("sentiment") == "neutral")

    summary = f"Sentiment for {company}: {positive} positive, {negative} negative, {neutral} neutral out of {len(news_dict)} articles.\n\nRecent headlines:\n"
    for idx in list(news_dict.keys())[:10]:
        article = news_dict[idx]
        summary += f"- [{article.get('sentiment', 'N/A')}] {article.get('title', '')} ({article.get('time', '')})\n  Reason: {article.get('sentiment_reasoning', '')}\n"

    return summary


@tool("get_fear_greed_index", description="Get the CNN Fear and Greed Index. Returns current value and recent trend.",
      return_direct=False)
def get_fear_greed_index():
    import pandas as pd

    df = pd.read_csv("cnn_fear_and_greed_index.csv")
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date", ascending=False)

    latest = df.iloc[0]
    week_ago = df.iloc[5] if len(df) > 5 else df.iloc[-1]
    month_ago = df.iloc[22] if len(df) > 22 else df.iloc[-1]

    return (
        f"Fear & Greed Index as of {latest['date'].strftime('%Y-%m-%d')}:\n"
        f"Current: {latest['value']} ({latest['label']})\n"
        f"5 days ago: {week_ago['value']} ({week_ago['label']})\n"
        f"~1 month ago: {month_ago['value']} ({month_ago['label']})\n"
        f"Trend: {'Improving' if latest['value'] > week_ago['value'] else 'Declining'}"
    )

##BUILD AGENT
GEMINI_API_KEY = str(os.environ.get("GEMINI_API_KEY"))
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=GEMINI_API_KEY)

agent = create_agent(
    model= llm,
    tools=[get_ticker_sentiment],
    system_prompt="""You are a senior investment research analyst. Your job is to answer financial questions using the tools available to you.

Rules:
- Always use tools to get real data before forming an opinion. Never guess.
- When analysing sentiment, report the sentiment score AND the reasoning behind it.
- If a tool returns no data, say so clearly. Do not fabricate results.
- Keep answers concise and data-driven. No filler.
- When multiple articles exist, summarise the overall trend, not every article.""",
    debug=True
)


response = agent.invoke(
    {"messages": [{"role": "user", "content": "What is the current sentiment on NVDA?"}]}
)
print(response["messages"][-1].content)

