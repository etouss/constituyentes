from src.process_pipeline.generic_transaction import GenericTransaction
from src.process_pipeline.transaction_chain import TransactionChain

class DummyTransaction(GenericTransaction):
    def __init__(self, conversation, db) -> None:
        super().__init__('dummy', conversation)
        self.db = db

    def process_input(self, input: str) -> str:
        tx = TransactionChain(self.tx_id, self.db)
        answer = tx.process_input(input)
        return answer
