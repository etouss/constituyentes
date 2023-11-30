from src.process_pipeline.conversation import Conversation
from abc import ABC, abstractmethod


class GenericTransaction(ABC):
    def __init__(self,name: str, conversation: Conversation) -> None:
        super().__init__()
        self.name = name
        self.conversation = conversation
        self.tx_id = self.conversation.create_transaction(self.name)
        #self.conv_id = self.conversation.conv_id

    @abstractmethod
    def process_input(self, input: str):
        pass

    def process_request(self, input: dict):
        #save input in DB, in right conversation_id, if not create one.
        #create new tx_id
        #Retrieve conversation info
        #Create transaction
        
        #SaveInput
        self.conversation.save_input(self.tx_id, input)
        #Process the input
        output = self.process_input(input)
        #Save the output
        self.conversation.save_output(self.tx_id, output)
        return { "output": output, "tx_id": self.tx_id }
    