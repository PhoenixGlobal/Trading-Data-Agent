import datetime
from log import log
from flask import Flask, request
from langchain_openai import ChatOpenAI
from tools import *
from dotenv import load_dotenv
from langgraph.prebuilt import ToolNode
from langgraph.graph import END, START, StateGraph, MessagesState
from langgraph.checkpoint.redis import RedisSaver
from typing import Literal
import os
from langfuse.langchain import CallbackHandler
import redis

load_dotenv()

langfuse_handler = CallbackHandler()

redis_password = os.environ.get("REDIS_PASSWORD")
ttl = os.environ.get("REDIS_TTL")
pool = redis.ConnectionPool(
    host='127.0.0.1',
    port=6379,
    db=0,
    password=redis_password,
    decode_responses=False,
    max_connections=30
)
redis_client = redis.Redis(connection_pool=pool)
ttl_config = {"default_ttl": int(ttl), "refresh_on_read": True}
saver = RedisSaver(redis_client=redis_client, ttl=ttl_config)
saver.setup()

port = os.environ.get("PORT")
app = Flask(__name__)

tools = [get_coin_now_price, get_coin_historical_price, get_coin_market_cap, get_coin_supply_info,
         get_coin_historical_periods_price, get_coin_order_book, get_coin_rsi, get_holders, get_contract_holders,
         get_contract_token_info, get_coin_info, get_dex_pool_info, get_address_tokens,
         get_coin_historical_price_change, get_coin_macd, get_coin_kdj, get_tokens_by_topic,
         search_x_by_keyword, get_coin_insights]

tool_node = ToolNode(tools)

model = ChatOpenAI(
    model="gpt-4o-mini",
    base_url=os.getenv('BASE_URL'),
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
checkpointer = saver

graph = workflow.compile(checkpointer=checkpointer)

system_prompt = """
You are an agent that retrieves cryptocurrency data.

You are an AI assistant with deep reasoning capabilities. Before answering user questions or using tools, you must the steps below: 
- [Thought]: Thoroughly break down the user’s request, analyze the current state, and list the logical reasoning process.
- [Action]: If external information is required, select the appropriate tool and provide the necessary parameters.
- [Final Answer]: Provide the final response only after all logic is complete and coherent.

Do not skip the thinking step and provide the answer directly.
Do not include terms such as “Conclusion,” “Final Answer,” or similar wording in the final response.

If the data includes time-series data (which must include an explicit date or time field):
- You MUST return the time-series data in JSONC format.
- The time-series data MUST be fully complete with NO omissions.
- The date format MUST follow the standard "2006-01-02".

If the data is NOT time-series (i.e., no date or time field), you MUST NOT use JSONC format.

The language of all returned results MUST match the user's input language.
"""


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
