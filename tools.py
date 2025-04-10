from typing import ClassVar, Type
import logging

from langchain.tools import BaseTool
from pydantic import Field, BaseModel
from langchain_openai import ChatOpenAI


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TomTatThreadInput(BaseModel):
    thread: str = Field(description="Nội dung thread cần tóm tắt")

class TomTatThreadTool(BaseTool):
    """Tool giúp tóm tắt thread"""
    name: ClassVar[str] = "tom_tat_thread"
    description: ClassVar[str] = "Sử dụng để tóm tắt thread"
    model: ChatOpenAI = Field(description="Mô hình ngôn ngữ sử dụng cho việc tóm tắt thread")
    args_schema: Type[BaseModel] = TomTatThreadInput
    
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