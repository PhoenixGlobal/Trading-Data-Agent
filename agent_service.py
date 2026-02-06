import asyncio
import datetime
from log import log
from fastapi import FastAPI
from langchain_openai import ChatOpenAI
import time
import json
from langchain_core.runnables.config import var_child_runnable_config
from langchain_core.messages import ToolMessage
from dotenv import load_dotenv
from langgraph.prebuilt import ToolNode
from langgraph.graph import END, START, StateGraph, MessagesState
from langgraph.checkpoint.redis import AsyncRedisSaver
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.types import Command, interrupt
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

model_name = "gpt-4o-mini"

saver = None

port = os.environ.get("PORT")
mcp_url = os.environ.get("MCP_URL")
max_rounds = int(os.environ.get("MAX_ROUNDS"))

needs_approval_tool_names = ["deploy_user_strategy", "create_manual_split_order"]


def trim_history(messages, max_limits):
    system_prompt = messages[0] if messages and messages[0]["role"] == "system" else None
    rounds = [msg for msg in messages if msg["role"] != "system"]

    trimmed_rounds = rounds[-(max_limits * 2 + 1):]
    return [system_prompt] + trimmed_rounds if system_prompt else trimmed_rounds


async def custom_tool_interceptor(state: MessagesState, config):
    global tools, tool_node
    thread_id = config.get("configurable", {}).get("thread_id", "default_thread")
    last_message = state["messages"][-1]

    if not hasattr(last_message, "tool_calls") or not last_message.tool_calls:
        return await tool_node.ainvoke(state, config=config)

    needs_approval = any(tc["name"] in needs_approval_tool_names for tc in last_message.tool_calls)

    if needs_approval:
        confirm_prompt = "Do you approve deploying the user strategy?"
        for tool_call in last_message.tool_calls:
            if tool_call["name"] in needs_approval_tool_names:
                tool_call["args"]["thread_id"] = thread_id
                log(f"Interceptor: Injected thread_id {thread_id} into tool calls.")
                print(f"Interceptor: Injected thread_id {thread_id} into tool calls.")
                confirm_prompt = tool_call["args"]
        log(f"Interceptor: Confirmation Prompt: {confirm_prompt}")

        var_child_runnable_config.set(config)
        log(f"Interceptor: var_child_runnable_config set config {config}.")
        answer = interrupt(json.dumps(confirm_prompt))

        result = answer["decisions"][0]["type"]
        if result != "approve":
            tool_output = {}
            for tc in last_message.tool_calls:
                if tc["name"] in needs_approval_tool_names:
                    tool_output = ToolMessage(
                                        name=tc["name"],
                                        role="tool",
                                        tool_call_id=tc["id"],
                                        content=f"Operation cancelled by user.",
                                        status="error"
                                  )
            state["messages"].append(tool_output)
            return state

    return await tool_node.ainvoke(state, config=config)


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
        model=model_name,
        base_url=os.getenv('BASE_URL'),
        max_retries=2,
        callbacks=[langfuse_handler],
    ).bind_tools(tools)

    workflow = StateGraph(MessagesState)

    workflow.add_node("agent", call_model)
    workflow.add_node("tools", custom_tool_interceptor)

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
    interrupt: str


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
    try:
        query_response = await graph.ainvoke(inputs, config={"configurable": {"thread_id": thread_id},
                                                             "callbacks": [langfuse_handler]})
        log(f"Agent response is {query_response}.")
        print(f"Agent response is {query_response}.")

        if "__interrupt__" in query_response:
            interrupt_data = query_response["__interrupt__"]
            return {
                "query": query,
                "text": "You need to confirm this action.",
                "created": datetime.datetime.now().timestamp(),
                "interrupt": interrupt_data[0].value
            }

        rsp = query_response["messages"][-1].content
        res_completion = {
            "query": query,
            "text": rsp,
            "created": datetime.datetime.now().timestamp(),
            "interrupt": ""
        }
        return res_completion
    except Exception as e:
        log(f"Error: {str(e)}")
        return {
            "query": query,
            "text": "ERROR: " + str(e),
            "created": datetime.datetime.now().timestamp(),
            "interrupt": ""
        }


class RspItem(BaseModel):
    query: str
    text: str
    created: float
    interrupt: str


class ResumeItem(BaseModel):
    decision: str
    thread_id: str


@app.post("/resume")
async def resume(item: ResumeItem):
    # decisions: "approve" or "reject"
    resume_cmd = Command(resume={
        "decisions": [{"type": item.decision}]
    })

    config = {"configurable": {"thread_id": item.thread_id},
              "callbacks": [langfuse_handler]}

    try:
        query_response = await graph.ainvoke(resume_cmd, config=config)

        rsp = query_response["messages"][-1].content
        res_completion = {
            "thread_id": item.thread_id,
            "query": item.decision,
            "text": rsp,
            "created": datetime.datetime.now().timestamp(),
        }
        return res_completion
    except Exception as e:
        log(f"Error: {str(e)}")
        return {
            "thread_id": item.thread_id,
            "query": item.decision,
            "text": "ERROR: " + str(e),
            "created": datetime.datetime.now().timestamp(),
        }


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
    global max_rounds
    log(f"chat query data: {item}.")
    query = [m.model_dump() for m in item.user_input]

    if len(query) > max_rounds * 2 + 1:
        query = trim_history(query, max_rounds)

    log(f"user_input:{query}.")
    query.insert(0, {"role": "system", "content": system_prompt})
    inputs = {"messages": query}
    millis = int(time.time() * 1000)
    thread_id = f"chat-{millis}"
    try:
        query_response = await graph.ainvoke(inputs, config={"configurable": {"thread_id": thread_id},
                                                             "callbacks": [langfuse_handler]})
        log(f"Agent chat response is {query_response}.")

        if "__interrupt__" in query_response:
            interrupt_data = query_response["__interrupt__"]
            return {
                "query": query[-1]["content"],
                "text": "You need to confirm this action.",
                "created": datetime.datetime.now().timestamp(),
                "interrupt": interrupt_data[0].value
            }

        rsp = query_response["messages"][-1].content
        res_completion = {
            "query": query[-1]["content"],
            "text": rsp,
            "created": datetime.datetime.now().timestamp(),
            "interrupt": ""
        }
        return res_completion
    except Exception as e:
        log(f"Error: {str(e)}")
        return {
            "query": query[-1]["content"],
            "text": "ERROR: " + str(e),
            "created": datetime.datetime.now().timestamp(),
            "interrupt": ""
        }


if __name__ == "__main__":
    uvicorn.run("agent_service:app", host='0.0.0.0', port=int(port))
