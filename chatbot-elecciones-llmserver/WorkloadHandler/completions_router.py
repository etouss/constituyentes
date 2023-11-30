from fastapi import APIRouter,Depends,Request
from pydantic import BaseModel, create_model_from_typeddict , Field
from typing import List, Optional, Literal, Union, Iterator, Dict
from typing_extensions import TypedDict, NotRequired, Literal
import requests
from contextlib import asynccontextmanager

USE_OPEN = True
OPENAI = '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'
OPENAIMODEL = "text-davinci-003"
#os.environ["OPENAI_API_KEY"] = OPENAI # can be anything

ENTRY_POINTS = [
    "https://api.openai.com/v1/completions",
    "http://localhost:8020/LLamaCPU/completions"
    # Add more entry points as needed
]


class CompletionRouter(APIRouter):
    def __init__(self, prefix='') -> None:
        super().__init__(prefix=prefix)
        
        @self.post("/completions")
        def completions(request: CreateCompletionRequest):

            
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

            
    



async def select_entry_point() -> str:
    # Implement your entry point selection logic here, e.g., round-robin, random, etc.
    # For simplicity, this example just selects the first entry point in the list
    return ENTRY_POINTS[0]




class CreateCompletionRequest(BaseModel):
    prompt: Union[str, List[str]]
    suffix: Optional[str] = Field(None)
    max_tokens: int = 16
    temperature: float = 0.8
    top_p: float = 0.95
    echo: bool = False
    stop: Optional[List[str]] = []
    stream: bool = False

    # ignored or currently unsupported
    model: Optional[str] = Field(None)
    n: Optional[int] = 1
    logprobs: Optional[int] = Field(None)
    presence_penalty: Optional[float] = 0
    frequency_penalty: Optional[float] = 0
    best_of: Optional[int] = 1
    logit_bias: Optional[Dict[str, float]] = Field(None)
    user: Optional[str] = Field(None)

    # llama.cpp specific parameters
    top_k: int = 40
    repeat_penalty: float = 1.1

    class Config:
        schema_extra = {
            "example": {
                "prompt": "\n\n### Instructions:\nWhat is the capital of France?\n\n### Response:\n",
                "stop": ["\n", "###"],
            }
        }


class CompletionLogprobs(TypedDict):
    text_offset: List[int]
    token_logprobs: List[float]
    tokens: List[str]
    top_logprobs: List[Dict[str, float]]


class CompletionChoice(TypedDict):
    text: str
    index: int
    logprobs: Optional[CompletionLogprobs]
    finish_reason: Optional[str]


class CompletionUsage(TypedDict):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class CompletionChunk(TypedDict):
    id: str
    object: Literal["text_completion"]
    created: int
    model: str
    choices: List[CompletionChoice]


class Completion(TypedDict):
    id: str
    object: Literal["text_completion"]
    created: int
    model: str
    choices: List[CompletionChoice]
    usage: CompletionUsage
