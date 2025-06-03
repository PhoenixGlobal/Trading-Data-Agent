import datetime
from log import log
from flask import Flask, request
from langchain_openai import ChatOpenAI
from tools import *
from dotenv import load_dotenv
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
import os
from langgraph_supervisor import create_supervisor

load_dotenv()

port = os.environ.get("PORT")
app = Flask(__name__)

# model = ChatOpenAI(model="gpt-4o-mini")

market_agent = create_react_agent(
    model=ChatOpenAI(model="gpt-4o-mini", max_retries=2),
    tools=[get_coin_now_price, get_coin_historical_price, get_coin_market_cap, get_coin_supply_info,get_coin_info,
           get_coin_historical_periods_price, get_coin_order_book, get_coin_rsi, get_coin_historical_price_change,
           get_coin_macd, get_coin_kdj, get_coin_insights],
    prompt="You are an agent that retrieves cryptocurrency market data. You can obtain information including price, "
           "market capitalization, supply info, order book, basic information, and some technical analysis indicators.",
    name="market_agent",
)

chain_agent = create_react_agent(
    model=ChatOpenAI(model="gpt-4o-mini", max_retries=2),
    tools=[get_holders, get_contract_holders,get_contract_token_info,get_dex_pool_info,
           get_address_summary, get_address_tokens,get_address_token,  get_tokens_by_topic],
    prompt="You are an agent that retrieves on-chain cryptocurrency data. You can obtain information such as holders, "
           "token details, DEX pool information, and blockchain address data — including the address overview, whether "
           "it's a token contract or a regular address, and the tokens it holds. You can also fetch popular on-chain "
           "tokens based on specific topics.",
    name="chain_agent",
)

social_sentiment_agent = create_react_agent(
    model=ChatOpenAI(model="gpt-4o-mini", max_retries=2),
    tools=[search_x_by_keyword],
    prompt="You are an agent that retrieves public sentiment on cryptocurrency from social media. You can query tweets "
           "based on specific keywords.",
    name="social_sentiment_agent",
)

check_pointer = MemorySaver()

supervisor = create_supervisor(
    model=ChatOpenAI(model="gpt-4o-mini", max_retries=2),
    agents=[market_agent, chain_agent, social_sentiment_agent],
    prompt=(
        "You are a supervisor managing three agents:"
        "- One agent is responsible for cryptocurrency market data."
        "- One agent is responsible for cryptocurrency on-chain data."
        "- One agent is responsible for cryptocurrency social sentiment data."
        "When the user asks a cryptocurrency-related question, break it down into sub-questions and assign each one "
        "to the appropriate agent."
        "When the user asks a general, non-cryptocurrency question, answer it yourself directly as a general-purpose "
        "language model."
        "Your job is to understand the user's intent, break it into suitable sub-tasks, assign each crypto-related task "
        "to the corresponding agent, collect their responses, and return a unified answer to the user."
    ),
    add_handoff_back_messages=True,
    output_mode="full_history",
).compile(checkpointer=check_pointer)

graph = supervisor


@app.route('/response', methods=["GET", "POST"])
def response():
    """
    current request body:
    {
        "user_input" : "...",
        "thread_id" : "..."
    }
    """

    data = request.get_json()
    query = data.get("user_input")
    thread_id = data.get("thread_id")
    log(f"query data: {data},user_input:{query},thread_id:{thread_id}.")
    inputs = {"messages": [("user", query)]}
    query_response = graph.invoke(inputs,config={"configurable": {"thread_id": thread_id}})
    log(f"Agent response is {query_response}.")
    rsp = query_response["messages"][-1].content
    res_completion = {
        "query": query,
        "text": rsp,
        "created": datetime.datetime.now().timestamp(),
    }
    return res_completion


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=port)
