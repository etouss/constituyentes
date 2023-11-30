from fastapi import APIRouter
from pydantic import BaseModel, create_model_from_typeddict
from typing import Union,Optional,TypedDict,Literal,List
import requests

class CreateEmbeddingRequest(BaseModel):
    model: Optional[str]
    input: str
    user: Optional[str]

    class Config:
        schema_extra = {
            "example": {
                "input": "The food was delicious and the waiter...",
            }
        }

class EmbeddingUsage(TypedDict):
    prompt_tokens: int
    total_tokens: int


class EmbeddingData(TypedDict):
    index: int
    object: str
    embedding: List[float]


class Embedding(TypedDict):
    object: Literal["list"]
    model: str
    data: List[EmbeddingData]
    usage: EmbeddingUsage


class EmbedingRouter(APIRouter):

    def __init__(self,prefix = '') -> None:
        super().__init__(prefix = prefix)
        CreateEmbeddingResponse = create_model_from_typeddict(Embedding)

        @self.post(
            "/embeddings",
            response_model=CreateEmbeddingResponse,
        )
        def request_embedding(
            request: dict
        ) -> Embedding:
            if 'string' in request.keys():
                request = CreateEmbeddingRequest(model=None, input=request['string'], user=None)
            return self.embedding(request = request)
    
    def embedding(self,request: CreateEmbeddingRequest):
        #handle workload later
        #check if specific model required 
        #right now: OPENAI BUT THROUGH FAST API
        #response = requests.post("http://localhost:8040/openai/embeddings", json=request)
        response = requests.post("http://localhost:8040/LLamaCPU/embeddings", json=request)
        #response = requests.post("http://localhost:8040/HuggingFace/embeddings", json=request)
        return response


    