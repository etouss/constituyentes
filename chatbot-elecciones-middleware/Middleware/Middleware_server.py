DEBUG = False

PORT = 8000
PORT_ETIENNE = 8001
PORT_MARCELO = 8002
PORT_JUAN = 8003
PORT_ADRIAN = 8004

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ProcessPipeline.Conversation import Conversation
from ProcessPipeline.Transaction.PlatineTx import PlatineTx


app = FastAPI(
    title="MiddleWareEntry",
    version="0.0.1",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


#The dict format: Token?,Session?,input?

@app.post("/call/input", response_model=str)
def create_answer(request: dict):
    if DEBUG:
        print(request)  # Print the request body to the console

    #Check if valid token/ session_id

    conversation = Conversation(session_id = 12)
    transaction = PlatineTx(conversation)
    #Process request dict
    #request['session_id'] = 0
    return transaction.process_request(request['input'])



#Add middleware service : identification, session, encription, token, DDOS security.


import uvicorn
import os
import urllib.request

external_ip = urllib.request.urlopen('https://ident.me').read().decode('utf8')

print("Your MiddelWare external IP Address is:"+external_ip)

import socket   
hostname=socket.gethostname()   
IPAddr=socket.gethostbyname(hostname)   
print("Your MiddelWare Name is:"+hostname)   
print("Your MiddelWare IP Address is:"+IPAddr)
print("Your MiddelWare IP Port is:"+str(PORT_ETIENNE))

uvicorn.run(
    app, host="0.0.0.0", port=int(os.getenv("PORT", PORT_ETIENNE))
)