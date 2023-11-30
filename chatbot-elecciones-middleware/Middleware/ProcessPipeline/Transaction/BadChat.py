from ..Conversation import Conversation
from ..GenericTransaction import GenericTransaction
from ..TransactionChainChat import TransactionChainChat


class BadChat(GenericTransaction):
    def __init__(self,conversation:Conversation) -> None:
        super().__init__('BadChat',conversation)

    def process_input(self,input:str) -> str:
        new_input = ''
        history = self.conversation.get_history()
        for tx_id,input_h,output_h in history:
            new_input += 'USER: '+input_h+'\n'
            new_input += 'ASSISTANT: '+output_h+'\n'
        new_input += 'USER: '+input+'\n'
        new_input += 'ASSISTANT: '

        print(new_input)

        txc = TransactionChainChat(self.tx_id)
        return txc.process_input(new_input)
        