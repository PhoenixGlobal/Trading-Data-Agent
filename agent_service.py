import asyncio
import datetime
from log import log
from fastapi import FastAPI
from langchain_openai import ChatOpenAI
import time
from dotenv import load_dotenv
from langgraph.prebuilt import ToolNode
from langgraph.graph import END, START, StateGraph, MessagesState
from langgraph.checkpoint.redis import AsyncRedisSaver
from langchain_mcp_adapters.client import MultiServerMCPClient
from typing import Literal, List
import os
from langfuse import get_client
from langfuse.langchain import CallbackHandler
from pydantic import BaseModel
import redis.asyncio as async_redis
import uvicorn
from contextlib import asynccontextmanager

load_dotenv()

# Initialize Langfuse client
langfuse = get_client()

langfuse_handler = CallbackHandler()

saver = None

port = os.environ.get("PORT")
mcp_url = os.environ.get("MCP_URL")

tools = []
tool_node = None


async def get_mcp_tools():
    global tools, tool_node
    client = MultiServerMCPClient(
        {
            "Crypto-Agent": {
                "transport": "sse",
                "url": mcp_url,
            }
        }
    )
    tools = await client.get_tools()
    tool_node = ToolNode(tools)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await get_mcp_tools()
    global saver

    redis_password = os.environ.get("REDIS_PASSWORD")
    ttl = os.environ.get("REDIS_TTL")
    ttl_config = {"default_ttl": int(ttl), "refresh_on_read": True}
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

    create_graph()

    yield


app = FastAPI(lifespan=lifespan)


graph = None
model = None


def create_graph():
    global graph, tools, tool_node, saver, model
    model = ChatOpenAI(
        model="gpt-4o-mini",
        base_url=os.getenv('BASE_URL'),
        max_retries=2,
        callbacks=[langfuse_handler],
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


@app.get('/response', response_model=RspItem)
@app.post('/response', response_model=RspItem)
async def response(item: Item):
    """
    current request body:
    {
        "user_input" : "...",
        "thread_id" : "..."
    }
    """
    log(f"chat query data: {item}.")
    query = item.user_input
    thread_id = item.thread_id
    log(f"user_input:{query},thread_id:{thread_id}.")
    inputs = {"messages": [{"role": "system", "content": system_prompt},
                           {"role": "user", "content": query}]}
    query_response = await graph.ainvoke(inputs, config={"configurable": {"thread_id": thread_id},
                                                         "callbacks": [langfuse_handler]})
    log(f"Agent response is {query_response}.")
    rsp = query_response["messages"][-1].content
    res_completion = {
        "query": query,
        "text": rsp,
        "created": datetime.datetime.now().timestamp(),
    }
    return res_completion


class Message(BaseModel):
    role: str
    content: str


class ChatItem(BaseModel):
    user_input: List[Message]


@app.get('/chat', response_model=RspItem)
@app.post('/chat', response_model=RspItem)
async def chat(item: ChatItem):
    """
    current request body:
    {
        "user_input" : [{"role":"user","content":"tell a joke"}]
    }
    """

    log(f"chat query data: {item}.")
    query = [m.model_dump() for m in item.user_input]
    log(f"user_input:{query}.")
    query.insert(0, {"role": "system", "content": system_prompt})
    inputs = {"messages": query}
    millis = int(time.time() * 1000)
    thread_id = f"chat-{millis}"
    query_response = await graph.ainvoke(inputs, config={"configurable": {"thread_id": thread_id},
                                                         "callbacks": [langfuse_handler]})
    log(f"Agent chat response is {query_response}.")
    rsp = query_response["messages"][-1].content
    res_completion = {
        "query": query[-1]["content"],
        "text": rsp,
        "created": datetime.datetime.now().timestamp(),
    }
    return res_completion


if __name__ == "__main__":
    uvicorn.run("agent_service:app", host='0.0.0.0', port=int(port))
