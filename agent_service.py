import datetime
from log import log
from flask import Flask, request
from langchain_openai import ChatOpenAI
from tools import *
from dotenv import load_dotenv
from langgraph.prebuilt import ToolNode
from langgraph.graph import END, START, StateGraph, MessagesState
from typing import Literal

load_dotenv()

app = Flask(__name__)

tools = [get_coin_now_price, get_coin_historical_price, get_coin_market_cap, get_coin_supply_info,
         get_coin_historical_periods_price, get_coin_order_book]

tool_node = ToolNode(tools)

model = ChatOpenAI(model="gpt-4o-mini").bind_tools(tools)


def should_continue(state: MessagesState) -> Literal["tools", END]:
    messages = state['messages']
    last_message = messages[-1]
    if last_message.tool_calls:
        return "tools"
    return END


def call_model(state: MessagesState):
    messages = state['messages']
    model_response = model.invoke(messages)
    # We return a list, because this will get added to the existing list
    return {"messages": [model_response]}


workflow = StateGraph(MessagesState)

workflow.add_node("agent", call_model)
workflow.add_node("tools", tool_node)

workflow.add_edge(START, "agent")
workflow.add_conditional_edges(
    # First, we define the start node. We use `agent`.
    # This means these are the edges taken after the `agent` node is called.
    "agent",
    # Next, we pass in the function that will determine which node is called next.
    should_continue,
)

workflow.add_edge("tools", 'agent')

graph = workflow.compile()


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
    app.run(host='0.0.0.0', port=5011)
