from fastapi import APIRouter
from pydantic import BaseModel, create_model_from_typeddict , Field
from typing import List, Optional, Literal, Union, Iterator, Dict
from typing_extensions import TypedDict, NotRequired, Literal
import requests
from sse_starlette.sse import EventSourceResponse
from completions_router import CompletionUsage


USE_OPEN = True
OPENAI = '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'
OPENAIMODEL = "gpt-3.5-turbo"

ENTRY_POINTS = [
    "https://api.openai.com/v1/chat/completions",
    "http://localhost:8020/LLamaCPU/completions"
    # Add more entry points as needed
]

class ChatCompletionRequestMessage(BaseModel):
    role: Union[Literal["system"], Literal["user"], Literal["assistant"]]
    content: str
    user: Optional[str] = None


class CreateChatCompletionRequest(BaseModel):
    model: Optional[str]
    messages: List[ChatCompletionRequestMessage]
    temperature: float = 0.8
    top_p: float = 0.95
    stream: bool = False
    stop: Optional[List[str]] = []
    max_tokens: int = 128

    # ignored or currently unsupported
    model: Optional[str] = Field(None)
    n: Optional[int] = 1
    presence_penalty: Optional[float] = 0
    frequency_penalty: Optional[float] = 0
    logit_bias: Optional[Dict[str, float]] = Field(None)
    user: Optional[str] = Field(None)

    # llama.cpp specific parameters
    repeat_penalty: float = 1.1

    class Config:
        schema_extra = {
            "example": {
                "messages": [
                    ChatCompletionRequestMessage(
                        role="system", content="You are a helpful assistant."
                    ),
                    ChatCompletionRequestMessage(
                        role="user", content="What is the capital of France?"
                    ),
                ]
            }
        }



class ChatCompletionMessage(TypedDict):
    role: Union[Literal["assistant"], Literal["user"], Literal["system"]]
    content: str
    user: NotRequired[str]


class ChatCompletionChoice(TypedDict):
    index: int
    message: ChatCompletionMessage
    finish_reason: Optional[str]


class ChatCompletion(TypedDict):
    id: str
    object: Literal["chat.completion"]
    created: int
    model: str
    choices: List[ChatCompletionChoice]
    usage: CompletionUsage


class ChatCompletionChunkDelta(TypedDict):
    role: NotRequired[Literal["assistant"]]
    content: NotRequired[str]


class ChatCompletionChunkChoice(TypedDict):
    index: int
    delta: ChatCompletionChunkDelta
    finish_reason: Optional[str]


class ChatCompletionChunk(TypedDict):
    id: str
    model: str
    object: Literal["chat.completion.chunk"]
    created: int
    choices: List[ChatCompletionChunkChoice]


class ChatCompletionRouter(APIRouter):

    def __init__(self,prefix = '') -> None:
        super().__init__(prefix = prefix)
        CreateChatCompletionResponse = create_model_from_typeddict(ChatCompletion)

        @self.post("/chat/completions")
        def chatcompletions(request: dict):            
            headers = {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer '+OPENAI
            }

            data = dict(request)

            #Dirty change the init of request to fit openai !! 
            if USE_OPEN:
                data["model"] = OPENAIMODEL 
                if 'top_k' in data:
                    data.pop('top_k')
                if 'repeat_penalty' in data:
                    data.pop('repeat_penalty')
                if 'user' in data:
                    data.pop('user')
                if 'stop' in data:
                    data.pop('stop')


            response = requests.post(ENTRY_POINTS[0], headers=headers, json=data)

            
            if response.ok:
                return response.json()
            else:
                response.raise_for_status()

            
    #def chatcompletion(self,request: CreateChatCompletionRequest):
        #handle workload later
        #check if specific model required 
        #right now: OPENAI BUT THROUGH FAST API
        #response = requests.post("http://localhost:8030/openai/embeddings", json=request)
      #  response = requests.post("http://localhost:8030/LLamaCPU/chat/completions", json=request)
        #response = requests.post("http://localhost:8030/HuggingFace/embeddings", json=request)
     #   return response


    