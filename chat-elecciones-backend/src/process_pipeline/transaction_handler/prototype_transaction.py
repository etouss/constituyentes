from src.process_pipeline.generic_transaction import GenericTransaction
from src.process_pipeline.transaction_chain import TransactionChain
from src.process_pipeline.transaction_chain_chat import TransactionChainChat
from src.process_pipeline.tools.sql_parser import parse_sql_query
from src.process_pipeline.tools.ann import similarity_tweet
from src.process_pipeline.tools.sql_execute import retrieve_tweets
from src.process_pipeline.tools.sql_execute import execute_query
from sqlalchemy.orm import Session

class ProtoTransaction(GenericTransaction):
    def __init__(self, conversation, vector_list, db_chatdata: Session, db_elections: Session) -> None:
        super().__init__('Proto',conversation)
        self.db_chatdata = db_chatdata
        self.db_elections = db_elections
        self.vector_list = vector_list

    def process_input(self, input:str) -> str:
        tx_c = TransactionChain(self.tx_id, self.db_chatdata)

        prompt = """### Postgres SQL tables, with their properties:
#
# ACCOUNT = (twitter_account_id INTEGER, realname, num_region).
# Region (num_region, nom_region)
# twitter_data(id_tweet INTEGER,twitter_account_id INTEGER, tweet_likes,tweet_retweets,tweet_date,id_account).
#
### Today is the 29th of April 2023 and we are in Chile
### You can use a custom PSQL boolean function on the tweets to check for semantic similarity in text: similar('subject')
### A query to extract the relevant tweet_ids to answer the question """
        prompt += input
        prompt +="""
SELECT"""

        print("##########PROMPT############")
        print(prompt)
        sql_query_string = tx_c.process_input(prompt)
        #tx_c.close
        sql_query_string = 'SELECT'+sql_query_string

        print("##########SQL############")
        print(sql_query_string)

        new_sql_query, similar_clauses = parse_sql_query(sql_query_string)

        #Add some if for empty query, no similar clause

        #SQL Call

        candidate_ids = execute_query(new_sql_query, self.db_elections)
        candidate_list = []
        for row in candidate_ids:
            candidate_list+= [row[0]]

        list_ids = similarity_tweet(similar_clauses, candidate_list, vector_list=self.vector_list)
        #query_str,candidates_id=None,limit=20

        #SQL Call retrieve tweet_text : list_ids
        tweets = retrieve_tweets(list_ids, self.db_elections)

        tx_c_chain = TransactionChainChat(self.tx_id, self.db_chatdata)

        system_prompt = 'You are a helpful Chilean assistant which only answer the question using the information contained in the given tweets, if you can not answer the question simply state you can not answer.\n'
        

        print("##########TWEETS############")
        print(tweets)

        for tweet in tweets:
            system_prompt += tweet[0]+'\n'

        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": input}
        ]

        answer = tx_c_chain.process_input(messages)
        return answer
