import os
import asyncio
from typing import TypedDict, Annotated
from contextlib import asynccontextmanager

import langchain
from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import ToolNode
from langgraph.graph.message import AnyMessage, add_messages
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate
from langchain_core.messages import AIMessage
from langchain_mcp_adapters.tools import load_mcp_tools
from mcp import ClientSession
from mcp.client.sse import sse_client

from src.utils.tools import TomTatThreadTool
from src.utils.parser import answer_parser

langchain.debug = True

class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=os.getenv("OPENAI_API_KEY"))

def get_system_prompt():
    system_prompt = """
    You are BotAI - an assistant in Slack for a project. 
    Below is the conversation in a thread, you need to respond to the last message where you were mentioned (@BotAI).
    To answer the question, always analyze first to decide if you need to use any tools.
    Only provide factual information supported by verified sources or clearly indicate when you're unsure. Do not make up names, dates, statistics, or quotes. If you don't know the answer, respond with "I don't know".
    Format instructions: {format_instructions}
    Conversation: {conversation}
    """

    system_prompt += "\nYou should always answer in same language as user's ask."

    return system_prompt

def create_chatbot(tools):
    prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(get_system_prompt()),
    ])
    llm_with_tools = llm.bind_tools(tools=tools, tool_choice="auto")
    chain = prompt | llm_with_tools

    def chatbot(state: State):
        # Ensure messages are in the right format
        if isinstance(state["messages"], str):
            from langchain_core.messages import HumanMessage
            messages = [HumanMessage(content=state["messages"])]
        else:
            messages = state["messages"]

        response = chain.invoke({"conversation": messages, "format_instructions": answer_parser.get_format_instructions()})

        return {"messages": messages + [response]}

    return chatbot


def router(state):
    messages = state["messages"]
    last_message = messages[-1]
    
    # Check for existing tool calls
    has_tool_calls = False
    if isinstance(last_message, AIMessage):
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            has_tool_calls = True
        elif hasattr(last_message, "additional_kwargs") and last_message.additional_kwargs.get("tool_calls"):
            has_tool_calls = True
    
    return "tools" if has_tool_calls else "end"

@asynccontextmanager
async def create_agent():
    async with sse_client(url="http://localhost:8000/sse") as streams:
        async with ClientSession(*streams) as session:
            await session.initialize()
            
            tools = await load_mcp_tools(session)
            tools.append(TomTatThreadTool(llm))
            graph_builder = StateGraph(State)
            tool_node = ToolNode(tools)

            chatbot_node = create_chatbot(tools)
            graph_builder.add_node("chatbot", chatbot_node)
            graph_builder.add_node("tools", tool_node)

            graph_builder.add_edge(START, "chatbot")
            graph_builder.add_conditional_edges(
                "chatbot",
                router,
                {
                    "tools": "tools",
                    "end": END
                }
            )
            graph_builder.add_edge("tools", "chatbot")
            graph = graph_builder.compile()
            
            try:
                yield graph
            finally:
                pass


async def main():
    async with create_agent() as agent:
        result = await agent.ainvoke({"messages": """@botAI Capital of japan? """})
        # Get only the answer from the result
        print(result)

if __name__ == "__main__":
    asyncio.run(main())
