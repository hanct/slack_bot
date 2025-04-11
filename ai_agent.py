import os
import dotenv
import logging
from typing import Any, Dict

from tools import TomTatThreadTool

from mcp import ClientSession
from mcp.client.sse import sse_client
import langchain
from langchain_openai import ChatOpenAI
from langchain.agents import create_tool_calling_agent
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain_core.prompts import PromptTemplate
from langchain.agents import AgentExecutor
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import Field, BaseModel
import asyncio


langchain.debug = True

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CauTrucCauTraLoi(BaseModel):
    phan_tich: str = Field(description="Phân tích trước khi trả lời")
    cau_tra_loi: str = Field(description="Câu trả lời cuối cùng")


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
        self.system_prompt = self.create_system_prompt()
        self.answer_parser = PydanticOutputParser(pydantic_object=CauTrucCauTraLoi)
    
    def create_system_prompt(self):
        template = """Bạn là BotAI hỗ trợ trong Slack, hãy trả lời tin nhắn của người dùng. Hãy phân tích yêu cầu người dùng trước và quyết định xem có cần sử dụng đến tool không, không sử dụng tool nếu không thực sự cần. 
        {input}
        {format_instructions}        
        Hãy format câu trả lời để hiển thị đẹp trong Slack.
        {agent_scratchpad}
        """
        return PromptTemplate.from_template(template)

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
                    agent = create_tool_calling_agent(self.model, tools=tools, prompt=self.system_prompt)
                    agent_executor = AgentExecutor(agent=agent, tools=tools)
                    logger.info("Agent initialized successfully")
                    response = await agent_executor.ainvoke({"input": messages, "format_instructions": self.answer_parser.get_format_instructions()})
                    output = response.get("output", "Xin lỗi, tôi không thể xử lý yêu cầu này.")
                    return self.answer_parser.parse(output).cau_tra_loi

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
