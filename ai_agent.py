import os
import asyncio
from pydantic import BaseModel, Field
from contextlib import asynccontextmanager

from langgraph.graph import StateGraph, END, START, MessagesState
from langgraph.prebuilt import ToolNode

from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate
from langchain_core.messages import AIMessage
from langchain_mcp_adapters.tools import load_mcp_tools
from mcp import ClientSession
from mcp.client.sse import sse_client


class Answer(BaseModel):
    analysis: str = Field(description="Analysis before answering")
    answer: str = Field(description="Final answer")

answer_parser = PydanticOutputParser(pydantic_object=Answer)
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=os.getenv("OPENAI_API_KEY"))


def get_system_prompt():
    system_prompt = """
    You are a BotAI assistant in Slack for a project. Use the following tools to answer user's question:
    - add_two_numbers: Add two numbers
    - retrieve_related_docs: Retrieve related documents to a query

    Format instructions: {format_instructions}
    Conversation: {conversation}
    """

    system_prompt += "\nYou should always answer in same language as user's ask."

    return system_prompt

def create_chatbot(tools):
    prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(get_system_prompt()),
    ])
    llm_with_tools = llm.bind_tools(tools=tools)
    chain = prompt | llm_with_tools

    def chatbot(state: MessagesState):
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
            graph_builder = StateGraph(MessagesState)
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
        result = await agent.ainvoke({"messages": "what's 123123123+2143125?"})
        # Get only the answer from the result
        answer = answer_parser.parse(result["messages"][-1].content)
        print(answer.answer)

if __name__ == "__main__":
    asyncio.run(main())
