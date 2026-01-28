import asyncio
import datetime
from log import log
from fastapi import FastAPI
from langchain_openai import ChatOpenAI
from tools import *
from dotenv import load_dotenv
from langgraph.prebuilt import ToolNode
from langgraph.graph import END, START, StateGraph, MessagesState
from langgraph.checkpoint.redis import AsyncRedisSaver
from langchain_mcp_adapters.client import MultiServerMCPClient
from typing import Literal
import os
from langfuse import get_client
from langfuse.langchain import CallbackHandler
from pydantic import BaseModel
import redis.asyncio as async_redis
import uvicorn

load_dotenv()

# Initialize Langfuse client
langfuse = get_client()

langfuse_handler = CallbackHandler()

redis_password = os.environ.get("REDIS_PASSWORD")
ttl = os.environ.get("REDIS_TTL")
pool = None
redis_client = None
ttl_config = {"default_ttl": int(ttl), "refresh_on_read": True}
saver = None

port = os.environ.get("PORT")
app = FastAPI()

tools = []
tool_node = None

async def get_mcp_tools():
    global tools, tool_node
    client = MultiServerMCPClient(
        {
            "Crypto-Agent": {
                "transport": "sse",
                "url": "http://127.0.0.1:8000/sse",
            }
        }
    )
    tools = await client.get_tools()
    print(f"Loaded {len(tools)} tools from MCP, tools: {tools}")
    tool_node = ToolNode(tools)


# tools = [get_coin_now_price, get_coin_historical_price, get_coin_market_cap, get_coin_supply_info,
#          get_coin_historical_periods_price, get_coin_order_book, get_coin_rsi, get_holders, get_contract_holders,
#          get_contract_token_info, get_coin_info, get_dex_pool_info, get_address_tokens,
#          get_coin_historical_price_change, get_coin_macd, get_coin_kdj, get_tokens_by_topic,
#          search_x_by_keyword, get_coin_insights]


@app.on_event("startup")
async def startup_event():
    await get_mcp_tools()
    global pool, redis_client, saver
    pool = async_redis.ConnectionPool(
        host='127.0.0.1',
        port=6379,
        db=0,
        password=redis_password,
        decode_responses=False,
        max_connections=30
    )
    redis_client = async_redis.Redis(connection_pool=pool)
    saver = AsyncRedisSaver(redis_client=redis_client, ttl=ttl_config)
    await saver.setup()
    loop = asyncio.get_running_loop()
    loop.run_in_executor(None, create_graph)

graph = None
model = None

def create_graph():
    global graph, tools, tool_node, saver, model
    model = ChatOpenAI(
        model="gpt-4o-mini",
        base_url=os.getenv('BASE_URL'),
        max_retries=2,
    ).bind_tools(tools)
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


def should_continue(state: MessagesState) -> Literal["tools", END]:
    messages = state['messages']
    last_message = messages[-1]
    if last_message.tool_calls:
        return "tools"
    return END


async def call_model(state: MessagesState):
    messages = state['messages']
    model_response = await model.ainvoke(messages)
    # We return a list, because this will get added to the existing list
    print(f"Token Usage Check: {model_response.usage_metadata}")
    return {"messages": [model_response]}


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


class RspItem(BaseModel):
    query: str
    text: str
    created: float

class Item(BaseModel):
    user_input: str
    thread_id: str


@app.post('/response', response_model=RspItem)
async def response(item: Item):
    """
    current request body:
    {
        "user_input" : "...",
        "thread_id" : "..."
    }
    """
    handler = CallbackHandler()
    log(f"chat query data: {item}.")
    # data = request.get_json()
    query = item.user_input
    thread_id = item.thread_id
    log(f"user_input:{query},thread_id:{thread_id}.")
    inputs = {"messages": [{"role": "system", "content": system_prompt},
                           {"role": "user", "content": query}]}
    query_response = await graph.ainvoke(inputs,config={"configurable": {"thread_id": thread_id}, "callbacks": [handler]})
    handler.client.flush()
    log(f"Agent response is {query_response}.")
    rsp = query_response["messages"][-1].content
    res_completion = {
        "query": query,
        "text": rsp,
        "created": datetime.datetime.now().timestamp(),
    }
    return res_completion


@app.post('/response', response_model=RspItem)
async def chat(item: Item):
    """
    current request body:
    {
        "user_input" : [{"role":"user","content":"tell a joke"}]
    }
    """

    log(f"chat query data: {item}.")
    # data = request.get_json()
    query = item.user_input
    thread_id = item.thread_id
    log(f"user_input:{query},thread_id:{thread_id}.")
    inputs = {"messages": query}
    millis = int(time.time() * 1000)
    thread_id = f"chat-{millis}"
    query_response = await graph.ainvoke(inputs, config={"configurable": {"thread_id": thread_id}, "callbacks": [langfuse_handler]})
    log(f"Agent chat response is {query_response}.")
    rsp = query_response["messages"][-1].content
    res_completion = {
        "query": query,
        "text": rsp,
        "created": datetime.datetime.now().timestamp(),
    }
    return res_completion


if __name__ == "__main__":
    uvicorn.run("agent_service:app", host='0.0.0.0', port=int(port))
