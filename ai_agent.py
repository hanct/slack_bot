import os
from typing import Annotated

from typing_extensions import TypedDict

from langgraph.graph import StateGraph, END, START
from langgraph.graph.message import add_messages
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import ToolNode, tools_condition

class State(TypedDict):
    messages: Annotated[list, add_messages]


llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=os.getenv("OPENAI_API_KEY"))

def create_tool_calling_agent(tools, prompt):
    llm_with_tools = llm.bind_tools(tools)
    
    def supervisor(state: State):
        message = llm_with_tools.invoke(state["messages"])
        return {"messages": [message]}

    graph_builder = StateGraph(State)
    graph_builder.add_node("supervisor", supervisor)
    tool_node = ToolNode(tools=tools)
    graph_builder.add_node("tools", tool_node)
    graph_builder.add_conditional_edges(
        "supervisor",
        tools_condition,
    )

    graph_builder.add_edge(START, "supervisor")
    graph_builder.add_edge("tools", END)

    return graph_builder.compile()


from IPython.display import Image, display

try:
    graph = create_tool_calling_agent([], "")
    # Save the diagram to a file
    graph.get_graph().draw_mermaid_png(output_file_path="agent_graph.png")
    print("Diagram saved as agent_graph.png")
except Exception as e:
    # This requires some extra dependencies and is optional
    print(f"Error generating diagram: {e}")