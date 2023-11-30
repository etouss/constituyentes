from sqlalchemy.sql import text
from sqlalchemy.orm import Session
#from datetime import datetime
import re

def retrieve_tweets(list_tweet_id, db: Session):
    #now = datetime.now()
    answer = None
    try:
        list_as_tuple = tuple(map(lambda x: int(x), list_tweet_id))
        result_proxy = db.execute(
            text("SELECT full_text,nom_region,partido,pacto FROM twitter_data WHERE tweet_id IN :list_as_tuple"),
            {
                "list_as_tuple": list_as_tuple
            }
        )
        answer = result_proxy.fetchall()
    except Exception as e:
        print("### Error: retrieve_tweets ###")
        print(e)
        db.rollback()
    #print('####### RETRIEVE TWEET #########')
    #print(datetime.now() - now)
    return answer

def execute_query(sql_query, db: Session):
    #print('###### SQL QUERY ########')
    #print(sql_query)
    #now = datetime.now()
    answer = None
    column_names=None
    i = 0
    while i < 2:
        try:
            if i == 0:
                result_proxy = db.execute(
                    text(replace_sql_attributes(sql_query))
                )
                if result_proxy.rowcount > 5000:
                    raise Exception('too many rows')
                answer = result_proxy.fetchall()
                column_names = list(result_proxy.keys())
                #print(column_names)
                break
            elif i == 1:
                result_proxy = db.execute(
                    text(sql_query)
                )
                if result_proxy.rowcount > 5000:
                    raise Exception('too many rows')
                answer = result_proxy.fetchall()
                column_names = list(result_proxy.keys())
                #print(column_names)
                break
        except Exception as e:
            i += 1
            print("### Error: execute_query ###")
            print(e)
            db.rollback()
    #print('####### SQL EXECUTE #########')
    #print(datetime.now() - now)
    return answer,column_names


def replace_sql_attributes(sql_query):
        attributes = ['nom_region','partido','nombre','pacto','profesion','description']
        for attribute in attributes:
            pattern = re.compile(r"\b{}[ ]*=[ ]*['\"]([^'\"]+)['\"]".format(attribute), re.IGNORECASE)
            sql_query = pattern.sub("{} LIKE '%\\1%'".format(attribute), sql_query)
            if "DISTINCT" not in sql_query:
                final_query = sql_query.replace("SELECT", "SELECT DISTINCT", 1)
            else:
                final_query = sql_query
        return final_query