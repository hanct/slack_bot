from mcp.server.fastmcp import FastMCP
from ai.retrieval import retrieve
from langchain_core.documents import Document


mcp = FastMCP()

#### Tools ####
# Add an addition tool
@mcp.tool()
def add_two_numbers(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b

@mcp.tool()
def retrieve_related_docs(query: str, k: int = 1) -> list[Document]:
    """Retrieve related documents from the vector database
    
    Args:
        query: Query to retrieve related documents
        k: Number of documents to retrieve
        
    Returns:
        Content of the related documents
    """
    docs = retrieve(query, k = k)

    return docs

# More tools can be added here

#### Resources ####
# Add a static resource
@mcp.resource("resource://some_static_resource")
def get_static_resource() -> str:
    """Static resource data"""
    return "Any static data can be returned"


# Add a dynamic greeting resource
@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Get a personalized greeting"""
    return f"Hello, {name}!"


#### Prompts ####
@mcp.prompt()
def review_code(code: str) -> str:
    return f"Please review this code:\n\n{code}"


@mcp.prompt()
def debug_error(error: str) -> list[tuple]:
    return [
        ("user", "I'm seeing this error:"),
        ("user", error),
        ("assistant", "I'll help debug that. What have you tried so far?"),
    ]


def get_tools():
    # Only include tools that are working
    base_tools = [add_two_numbers, retrieve_related_docs]
    
    return base_tools

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='sse')