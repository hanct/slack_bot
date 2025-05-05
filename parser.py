from pydantic import BaseModel, Field
from langchain_core.output_parsers import PydanticOutputParser


class Answer(BaseModel):
    analysis: str = Field(description="Analysis before answering")
    answer: str = Field(description="Final answer")

answer_parser = PydanticOutputParser(pydantic_object=Answer)