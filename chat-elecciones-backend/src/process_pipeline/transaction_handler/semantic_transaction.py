from src.process_pipeline.generic_transaction import GenericTransaction
from src.process_pipeline.transaction_chain import TransactionChain
from src.process_pipeline.transaction_chain_chat import TransactionChainChat
from src.process_pipeline.tools.ann import similarity_tweet
from src.process_pipeline.tools.sql_execute import retrieve_tweets
from sqlalchemy.orm import Session

class SemanticTransaction(GenericTransaction):
    def __init__(self, conversation, vector_list, db_chatdata: Session, db_elections: Session) -> None:
        super().__init__('Semantic',conversation)
        self.db_chatdata = db_chatdata
        self.db_elections = db_elections
        self.vector_list = vector_list

    def process_input(self, input: str) -> str:
        
        list_ids = similarity_tweet(input, vector_list=self.vector_list)
        #query_str,candidates_id=None,limit=20

        #SQL Call retrieve tweet_text : list_ids
        #print(list_ids)

        tweets = retrieve_tweets(list_ids, self.db_elections)

        tx_c_chain = TransactionChainChat(self.tx_id, self.db_chatdata)

        system_prompt = 'You are a helpful Chilean assistant which only answer the question using the information contained in the given tweets, if you can not answer the question simply state you can not answer.\n'
        print(tweets)

        for tweet in tweets:
            system_prompt += tweet[0]+'\n'

        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": input}
        ]

        #print(messages)

        answer = tx_c_chain.process_input(messages)
        return answer
