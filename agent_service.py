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

model = ChatOpenAI(model="gpt-4o-mini")

market_agent = create_react_agent(
    model,
    tools=[get_coin_now_price, get_coin_historical_price, get_coin_market_cap, get_coin_supply_info,get_coin_info,
           get_coin_historical_periods_price, get_coin_order_book, get_coin_rsi, get_coin_historical_price_change,
           get_coin_macd, get_coin_kdj, get_coin_insights],
    prompt="You are an agent that retrieves cryptocurrency market data. Based on the cryptocurrency symbol provided "
           "by the user, such as BTC, ETH, or SOL, you can obtain information including price, market capitalization, "
           "supply info, order book, basic details, and technical indicators.",
    name="market_agent",
)

chain_agent = create_react_agent(
    model,
    tools=[get_holders, get_contract_holders,get_contract_token_info,get_dex_pool_info,
           get_address_summary, get_address_tokens,get_address_token,  get_tokens_by_topic],
    prompt="You are an agent that retrieves on-chain cryptocurrency data. You can obtain information such as holders, "
           "token details, DEX pool information, and blockchain address data — including the address overview, whether "
           "it's a token contract or a regular address, and the tokens it holds. You can also fetch popular on-chain "
           "tokens based on specific topics.",
    name="chain_agent",
)

social_sentiment_agent = create_react_agent(
    model,
    tools=[search_x_by_keyword],
    prompt="You are an agent that retrieves public sentiment on cryptocurrency from social media. You can query tweets "
           "based on specific keywords.",
    name="social_sentiment_agent",
)

check_pointer = MemorySaver()

supervisor = create_supervisor(
    model=model,
    agents=[market_agent, chain_agent, social_sentiment_agent],
    prompt=(
        "You are a supervisor managing three agents:\n"
        "One agent responsible for cryptocurrency market data. Assign tasks related to cryptocurrency market data to this agent.\n"
        "One agent responsible for cryptocurrency on-chain data. Assign tasks related to cryptocurrency on-chain data to this agent.\n"
        "One agent responsible for cryptocurrency social sentiment data. Assign tasks related to cryptocurrency social sentiment to this agent."
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
