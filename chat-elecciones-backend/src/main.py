from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from src.config import (
    session_local, session_chatdata, 
    session_elections, get_vector_list)
from src.process_pipeline.conversation import Conversation
from src.process_pipeline.tools.feedback import register_feedback

from src.process_pipeline.transaction_handler.cheap_bandido_chat import CheapBandidoChat


vector_list = get_vector_list()

app = FastAPI(
    title="MiddlewareEntry",
    version="0.0.1",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db_local():
    db = session_local()
    try:
        yield db
    finally:
        db.close()

def get_db_chatdata():
    db = session_chatdata()
    try:
        yield db
    finally:
        db.close()

def get_db_elections():
    db = session_elections()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
async def root():
    markdown_response = '''Vaya a votar :)'''
    return {"message": markdown_response}

@app.post("/call/input", response_model=dict)
def create_answer(
    request: dict,
    db_chatdata: Session = Depends(get_db_chatdata),
    db_elections: Session = Depends(get_db_elections)
):
    conversation = Conversation(
        session_id=100, db=db_chatdata
    )
    
    transaction = CheapBandidoChat(
        conversation,
        vector_list,
        db_chatdata,
        db_elections
    )
    # Process request dict
    # request['session_id'] = 0
    answer = transaction.process_request(request['input'])
    return answer

@app.post("/call/feedback", response_model=dict)
def create_feedback(request: dict, db_chatdata: Session = Depends(get_db_chatdata)):
    question = request["question"]
    answer = request["answer"]
    tx_id = request["tx_id"]
    user_feedback = request["user_feedback"]
    register_feedback(tx_id, question, answer, user_feedback, db_chatdata)
    return {"status": "ok"}
