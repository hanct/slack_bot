import dotenv
import os
import logging
from typing import Any, Dict, ClassVar

from langchain_openai import ChatOpenAI
from mcp import ClientSession
import asyncio
from langgraph.prebuilt import create_react_agent
from mcp.client.sse import sse_client
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain.tools import BaseTool
from pydantic import Field
import langchain

langchain.debug = True

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TomTatThreadTool(BaseTool):
    """Tool giúp tóm tắt thread"""
    name: ClassVar[str] = "tom_tat_thread"
    description: ClassVar[str] = "Sử dụng để tóm tắt thread"
    model: ChatOpenAI = Field(description="Mô hình ngôn ngữ sử dụng cho việc tóm tắt thread")
    
    def __init__(self, model: ChatOpenAI) -> None:
        super().__init__(model=model)
        
    async def _arun(self, thread: str) -> str:
        """Tóm tắt thread
        
        Args:
            thread: Nội dung thread cần tóm tắt
            
        Returns:
            str: Nội dung tóm tắt thread
        """
        try:
            logger.info("Sử dụng tool tom_tat_thread")
            prompt = f"""Hãy tóm tắt thread sau: \n{thread}"""
            
            response = await self.model.ainvoke(prompt)
            return response.content
            
        except Exception as e:
            logger.error(f"Error in tom_tat_thread: {str(e)}")
            return "Xin lỗi, tôi không thể tóm tắt thread này."

    def _run(
        self):
        raise NotImplementedError("Does not support sync")

class MCPAgentRunner:
    """A class to run MCP (Multi-Component Platform) agents using OpenAI's language models.
    
    This class handles the initialization and execution of MCP agents with OpenAI integration.
    It manages the connection to the MCP server and provides methods to run agent interactions.
    """
    
    def __init__(self, model_name: str = "gpt-4o-mini", temperature: float = 0.5) -> None:
        """Initialize the MCPAgentRunner.
        
        Args:
            model_name: The name of the OpenAI model to use
            temperature: The temperature parameter for the model (controls randomness)
        """
        dotenv.load_dotenv()
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.mcp_url = os.getenv("MCP_URL")
        
        if not self.openai_api_key or not self.mcp_url:
            raise ValueError("OPENAI_API_KEY and MCP_URL must be set in environment variables")
            
        self.model = ChatOpenAI(
            model=model_name,
            temperature=temperature,
            api_key=self.openai_api_key
        )
        logger.info(f"Initialized MCPAgentRunner with model {model_name}")

    async def run(self, messages: str) -> Dict[str, Any]:
        """Run the agent with the given messages.
        
        Args:
            messages: The input messages for the agent
            
        Returns:
            The agent's response
            
        Raises:
            Exception: If there's an error during agent execution
        """
        try:
            async with sse_client(url=self.mcp_url) as streams:
                async with ClientSession(*streams) as session:
                    await session.initialize()
                    tools = await load_mcp_tools(session)
                    tools.append(TomTatThreadTool(self.model))
                    agent = create_react_agent(self.model, tools)
                    logger.info("Agent initialized successfully")
                    response = await agent.ainvoke({"messages": messages})
                    return response['messages'][-1].content

        except Exception as e:
            logger.error(f"Error running agent: {str(e)}")
            raise

def main() -> None:
    """Main function to demonstrate the MCPAgentRunner usage."""
    try:
        runner = MCPAgentRunner()
        answer = asyncio.run(runner.run("""Tóm tắt thread"""))
        print(answer)
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        raise

if __name__ == "__main__":
    main()
