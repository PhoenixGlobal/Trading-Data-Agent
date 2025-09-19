import datetime
from log import log
from flask import Flask, request
from langchain_openai import ChatOpenAI
from tools import *
from dotenv import load_dotenv
from langgraph.prebuilt import ToolNode
from langgraph.graph import END, START, StateGraph, MessagesState
from langgraph.checkpoint.memory import MemorySaver
from typing import Literal
import os
from langfuse.langchain import CallbackHandler

load_dotenv()

langfuse_handler = CallbackHandler()

port = os.environ.get("PORT")
app = Flask(__name__)

tools = [get_coin_now_price, get_coin_historical_price, get_coin_market_cap, get_coin_supply_info,
         get_coin_historical_periods_price, get_coin_order_book, get_coin_rsi, get_holders, get_contract_holders,
         get_contract_token_info, get_coin_info, get_dex_pool_info, get_address_tokens,
         get_coin_historical_price_change, get_coin_macd, get_coin_kdj, get_tokens_by_topic,
         search_x_by_keyword, get_coin_insights]

tool_node = ToolNode(tools)

model = ChatOpenAI(
    model="accounts/fireworks/models/qwen3-235b-a22b-instruct-2507",
    base_url="https://api.fireworks.ai/inference/v1",
    api_key=os.getenv('FIREWORKS_API_KEY'),
    max_retries=2,
).bind_tools(tools)


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

checkpointer = MemorySaver()

graph = workflow.compile(checkpointer=checkpointer)


@app.route('/response', methods=["GET", "POST"])
def response():
    """
    current request body:
    {
        "user_input" : "...",
        "thread_id" : "..."
    }
    """

    system_prompt = """
    You are an agent that retrieves cryptocurrency data.

    If the data includes time-series data (which must include an explicit date or time field):
    - You MUST return the time-series data in JSONC format.
    - The time-series data MUST be fully complete with NO omissions.
    - The date format MUST follow the standard "2006-01-02".
    
    If the data is NOT time-series (i.e., no date or time field), you MUST NOT use JSONC format.
    
    The language of all returned results MUST match the user's input language.
    """

    data = request.get_json()
    query = data.get("user_input")
    thread_id = data.get("thread_id")
    log(f"query data: {data},user_input:{query},thread_id:{thread_id}.")
    inputs = {"messages": [{"role": "system", "content": system_prompt},
                           {"role": "user", "content": query}]}
    query_response = graph.invoke(inputs,config={"configurable": {"thread_id": thread_id}, "callbacks": [langfuse_handler]})
    log(f"Agent response is {query_response}.")
    rsp = query_response["messages"][-1].content
    res_completion = {
        "query": query,
        "text": rsp,
        "created": datetime.datetime.now().timestamp(),
    }
    return res_completion


@app.route('/chat', methods=["GET", "POST"])
def chat():
    """
    current request body:
    {
        "user_input" : [{"role":"user","content":"tell a joke"}]
    }
    """

    system_prompt = """
    You are an agent that retrieves cryptocurrency data.

    If the data includes time-series data (which must include an explicit date or time field):
    - You MUST return the time-series data in JSONC format.
    - The time-series data MUST be fully complete with NO omissions.
    - The date format MUST follow the standard "2006-01-02".

    If the data is NOT time-series (i.e., no date or time field), you MUST NOT use JSONC format.

    The language of all returned results MUST match the user's input language.
    """

    data = request.get_json()
    query = data.get("user_input")
    log(f"chat query data: {data},user_input:{query}.")
    query.insert(0, {"role": "system", "content": system_prompt})
    inputs = {"messages": query}
    millis = int(time.time() * 1000)
    thread_id = f"chat-{millis}"
    query_response = graph.invoke(inputs, config={"configurable": {"thread_id": thread_id}, "callbacks": [langfuse_handler]})
    log(f"Agent chat response is {query_response}.")
    rsp = query_response["messages"][-1].content
    res_completion = {
        "query": query,
        "text": rsp,
        "created": datetime.datetime.now().timestamp(),
    }
    return res_completion


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=port)
