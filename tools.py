import logging
from typing import ClassVar, Type

from langchain.tools import BaseTool
from langchain_openai import ChatOpenAI
from pydantic import Field, BaseModel


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TomTatThreadInput(BaseModel):
    thread: str = Field(description="Nội dung thread cần tóm tắt")

class TomTatThreadTool(BaseTool):
    """Tool giúp tóm tắt thread, chỉ dùng khi được yêu cầu tóm tắt thread"""
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
            prompt = f"""Tóm tắt cuộc hội thoại sau trong Slack. Chỉ nêu các ý chính liên quan đến công việc, bao gồm các quyết định được đưa ra, các hành động cần thực hiện, ai chịu trách nhiệm và các mốc thời gian (nếu có). Bỏ qua các đoạn trò chuyện xã giao hoặc không liên quan. Trình bày ngắn gọn, rõ ràng dưới dạng gạch đầu dòng: \n{thread}"""
            
            response = await self.model.ainvoke(prompt)
            return response.content
            
        except Exception as e:
            logger.error(f"Error in tom_tat_thread: {str(e)}")
            return "Xin lỗi, tôi không thể tóm tắt thread này."

    def _run(
        self):
        raise NotImplementedError("Does not support sync")