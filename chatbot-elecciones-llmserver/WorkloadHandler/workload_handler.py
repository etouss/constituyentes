from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

PORT = 8030


app = FastAPI(
    title="WorkLoad_handler",
    version="0.0.1",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import os
import uvicorn
import urllib.request

external_ip = urllib.request.urlopen('https://ident.me').read().decode('utf8')

print("Your Server external IP Address is:"+external_ip)

import socket   
hostname=socket.gethostname()   
IPAddr=socket.gethostbyname(hostname)   
print("Your Workload Name is:"+hostname)   
print("Your Workload IP Address is:"+IPAddr)
print("Your Workload ort is:"+str(PORT))

#Load Router:
from completions_router import CompletionRouter
app.include_router(CompletionRouter(prefix="/workload_handler"))
from embedings_router import EmbedingRouter
app.include_router(EmbedingRouter(prefix="/workload_handler"))
from chat_completions_router import ChatCompletionRouter
app.include_router(ChatCompletionRouter(prefix="/workload_handler"))

uvicorn.run(
    app, host=os.getenv("HOST", "localhost"), port=int(os.getenv("PORT", PORT))
)
