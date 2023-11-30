from ..GenericTransaction import GenericTransaction

class DummyTransaction(GenericTransaction):
    def __init__(self,conversation) -> None:
        super().__init__('dummy',conversation)

    def process_input(self, input:str) -> str:
        return 'HELLO-world'