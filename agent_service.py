import datetime
from log import log
from flask import Flask, request
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from tools import *
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

tools = [get_coin_now_price, get_coin_historical_price, get_coin_market_cap, get_coin_supply_info,
         get_coin_historical_periods_price, get_coin_order_book]
model = ChatOpenAI(model="gpt-4o-mini")
graph = create_react_agent(model, tools=tools)


@app.route('/response', methods=["GET", "POST"])
def response():
    """
    current request body:
    {
        "user_input" : "..."
    }
    """

    data = request.get_json()
    query = data.get("user_input")
    log(f"query data: {data},user_input:{query}.")
    inputs = {"messages": [("user", query)]}
    query_response = graph.invoke(inputs)
    log(f"Agent response is {query_response}.")
    rsp = query_response["messages"][-1].content
    res_completion = {
        "query": query,
        "text": rsp,
        "created": datetime.datetime.now().timestamp(),
    }
    return res_completion


if __name__ == "__main__":
    app.run(port=5011,debug=True)
