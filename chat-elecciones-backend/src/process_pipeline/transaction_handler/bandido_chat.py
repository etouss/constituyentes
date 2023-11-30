from src.process_pipeline.generic_transaction import GenericTransaction
from src.process_pipeline.transaction_chain import TransactionChain
from src.process_pipeline.transaction_chain_chat import TransactionChainChat
from src.process_pipeline.tools.ann import similarity_tweet
from src.process_pipeline.tools.sql_execute import retrieve_tweets
from src.process_pipeline.tools.sql_execute import execute_query
from sqlalchemy.orm import Session



class BandidoChat(GenericTransaction):
    def __init__(self, conversation, vector_list, db_chatdata: Session, db_elections: Session) -> None:
        super().__init__('BandidoChat',conversation)
        self.db_chatdata = db_chatdata
        self.db_elections = db_elections
        self.txc = TransactionChain(self.tx_id, self.db_chatdata)
        self.tx_c_chain = TransactionChainChat(self.tx_id, self.db_chatdata)
        self.user_input = ""
        self.sql_response = "No disponible"
        self.semanthic_response = "No disponible"
        # here you can change between completion or chat end responses, completions are better but may be incomplete
        self.use_completion_model = False
        self.vector_list = vector_list

    def process_input(self, input:str) -> str:
        print("Flows used:")
        self.user_input = input
        context, response = self.initial_input_process(input, previous_context="")
        #print("initial_context:\n\n"+context)
        #print("\n\n"+response)
        return response
    
    def initial_input_process(self, input, previous_context):
        print("---initial_input_process---")

        context = f"""Contexto: Eres un bot que dado un requerimiento en formato 
        de texto, es capaz de entregar información sobre las elecciones constituyentes 
        y los candidatos a las elecciones de constituyentes en Chile, año 2023.
        Tienes acceso a 2 tipos de información: 1: data estructurada oficial del
        sistema electoral chileno en una tabla cuyo esquema es 
        candidatos(nombre, twitter_account, twitter_account_id, sexo, edad, profesion, num_region, nom_region, financiamiento, description, partido, pacto), la cual contiene
        información de los candidatos constituyentes que participarán en el proceso de elecciones, un ejemplo de la data que contiene es . sexo toma valores "mujer" o "hombre". nom_region puede tomar valores Coquimbo, Ohiggins, Ñuble, Valparaíso, Tarapacá, Atacama, Biobio, Maule,Arica y Parinacota,Antofagasta,Metropolitana. Partido puede tomar valores PC, PDG, RN, PL, IND, AH, PR, PPD, UDI, RD, PS, COM, REP, EVO, DC, CS, FRVS'. 
        2: Data no estructurada de textos de Twitter escritos por los candidatos constituyentes, 
        con lo que puedes mostrar información que refleje las tendencias ideológicas u opiniones de
        cada candidato, además de información del proceso constituyente. Y puede interpretar opiniones Si te llega este requerimiento:
        "{self.user_input}" Pregunta: Qué fuente de información usarías? 
        Respuesta (responde solamente con "1", "2", 
        "Aunque sea relevante para las elecciones, eso es una opinion personal",
        "No puedo responder, la pregunta no es relevante para las elecciones"):
        """

        response = self.txc.process_input(context)

        if "1" in response.lower():
            return self.flow_only_sql_or_add_twitter(input=input, previous_context=context)
        
        elif "2" in response.lower() or "opinion" in response.lower():
            return self.flow_only_twitter_or_add_sql(input=response, previous_context=context)

        else:
            return self.exit_flow(input="", previous_context=context)
        
    def flow_only_sql_or_add_twitter(self, input, previous_context):
        print("---flow_only_sql_or_add_twitter---")
        question = f"""Responde con "1" si puedes responder solamente con data estructurada de
                    las tablas o con un "3" si necesitas agregar información de la data no estructurada
                    de twitter? Respuesta (responde solamente con "1", "3"):"""
        
        context = previous_context+"1\n"+question

        response = self.txc.process_input(context)

        if "1" in response.lower():
            return self.flow_create_sql_query(input=self.user_input, previous_context=context)
        
        elif "3" in response.lower():
            return self.flow_separate_in_sql_and_semanthic_tweet(input=self.user_input, previous_context=context)
        
    def flow_separate_in_sql_and_semanthic_tweet(self, input, previous_context):
        print("---flow_separate_in_sql_and_semanthic_tweet---")
        question = f"""# Chile, año 2023. #Examen de procesamiento de datos 
            avanzado #Requerimiento: "{self.user_input}". #Pregunta: Quieres crear 
            dos frases, la primera para usar busqueda semantica para filtrar la data 
            no estructurada de los tweets, y la segunda para usarla sobre la data estructurada
              de las tablas usando SQL para obetener respuestas deterministicamente. Para esto: 
              a) Divide el requerimiento en dos frases, una que contiene la parte semantica 
              y la otra la parte a ser usada por SQL. Por ejemplo, la frase "que opinan 
              los candidatos de Valparaiso sobre las AFPs" debe dividirse en "opinion AFPs" 
              y "candidatos hombres de Valparaiso". La frase "Candidato más ecologista" 
              debe dividirse en "ecología" y "candidato hombre". Escribe la dos frase a 
              continuación, primero la primera frase (semantica), un guión -, y 
              luego la segunda frase (para usar SQL):"""
            
        context = previous_context+"3\n"+question
            
        response = self.txc.process_input(context)

        semanthic = response.split("-")[0]
        sql_deterministic = response.split("-")[1]

        question_sql_filter = f"""Chile, año 2023. #Examen de procesamiento de datos 
        #avanzado
        #Tablas en postgreSQL: #twitter_data(tweet_id, date, twitter_account, twitter_account_id, text_content, likes, retweets, is_retweet, img_url, img_storage_path)
        #candidatos(nombre, twitter_account, twitter_account_id, sexo, edad, profesion, num_region, nom_region, financiamiento, description, partido, pacto), sexo toma valores "mujer" o "hombre". nom_region puede tomar valores Coquimbo, Ohiggins, Ñuble, Valparaíso, Tarapacá, Atacama, Biobio, Maule,Arica y Parinacota,Antofagasta,Metropolitana. Partido puede tomar valores PC, PDG, RN, PL, IND, AH, PR, PPD, UDI, RD, PS, COM, REP, EVO, DC, CS, FRVS'. 
        #comunas(comuna,region) #Para la query utiliza unicamente el Requerimiento: "{sql_deterministic}". 
        #Pregunta: Escribe una consulta SQL que te permita encontrar los candidatos y los tweet_id de los tweet que ha dicho, la consulta debe retornar unicamente y solamente un columna tweet_id: SELECT"""
        
        context_sql_filter = context+sql_deterministic+question_sql_filter
        response_sql_filter = self.txc.process_input(context_sql_filter)
        promt_with_sql_query = context_sql_filter+response_sql_filter
        sql_response = self.get_sql_response(promt_with_sql_query)

        if sql_response is None:
            return self.exit_flow("", previous_context=promt_with_sql_query)
        
        tweet_id_list = self.str_to_int_list(sql_response)
        #print(tweet_id_list)
        list_ids = similarity_tweet(semanthic, candidates_id=tweet_id_list, limit=10, vector_list=self.vector_list)
        tweets = retrieve_tweets(list_ids, self.db_elections)
        tweets_promt = ""
        for tweet in tweets:
                tweets_promt += tweet[0]+'\n'

        question_sql_data_only = f"""Dame la misma query anterior pero exluye los atributos relacionados tweet e incluye solamente los relevantes de candidatos, haciendo un DISTINCT candidatos.nombre o lo que necesites para evitar tuplas repetidas. El Requerimiento: {sql_deterministic}. Query:"""
        context_sql_only = promt_with_sql_query+question_sql_data_only
        response_sql_only = self.txc.process_input(context_sql_only)
        #print(response_sql_only)
        sql_response_sql_only = self.get_sql_response(response_sql_only)
        #print(sql_response_sql_only)

        # TODO: aqui se podria encontrar una mejor forma de darle la info de sql
        return self.flow_final_answer(sql_response=sql_response_sql_only, semanthic_response=tweets_promt, previous_context=input+"\n"+tweets_promt)
    
    def str_to_int_list(self, string):
        # Remove the parentheses and commas from the string
        string = string.replace("(", "").replace(")", "").replace(",", " ")
        # Split the string into individual numbers
        numbers = string.split()
        # Convert each number from a string to an integer
        int_list = [int(num) for num in numbers]
        return int_list

    def flow_create_sql_query(self, input, previous_context):
        print("---flow_create_sql_query---")
        question = f"""Escribe una consulta SQL que responda el Requerimiento:
                   {self.user_input} usando la tabla candidatos(nombre, twitter_account, twitter_account_id, sexo, edad, profesion, num_region, nom_region, financiamiento, description, partido, pacto), sexo toma valores "mujer" o "hombre". nom_region puede tomar valores Coquimbo, Ohiggins, Ñuble, Valparaíso, Tarapacá, Atacama, Biobio, Maule,Arica y Parinacota,Antofagasta,Metropolitana. Partido puede tomar valores PC, PDG, RN, PL, IND, AH, PR, PPD, UDI, RD, PS, COM, REP, EVO, DC, CS, FRVS'.:\nSELECT"""
        
        context = previous_context+"1\n"+question

        response = self.txc.process_input(context)

        promt_with_sql_query = context+response
        sql_response = self.get_sql_response(promt_with_sql_query)

        if sql_response is None:
            return self.exit_flow("", previous_context=promt_with_sql_query)
        
        else:
            return self.flow_final_answer(sql_response, None, previous_context=promt_with_sql_query)
    
    def flow_final_answer(self, sql_response, semanthic_response, previous_context):
        if self.use_completion_model:
            return self.flow_final_answer_completion_like(sql_response, semanthic_response, previous_context)
        else:
            return self.flow_final_answer_chat_like(sql_response, semanthic_response, previous_context)

    def flow_final_answer_completion_like(self, sql_response, semanthic_response, previous_context):
        print("---flow_final_answer_completion_like---")
        if sql_response:
            self.sql_response = sql_response
        if semanthic_response:
            self.semanthic_response = semanthic_response
        
        raw_context = f"Requerimiento: {self.user_input}. Información SQL: {self.sql_response}. Información Semántica Tweeter: {self.semanthic_response}. Escribe una respuesta que responda el requerimiento, dado el contexto de las elecciones de constituyentes en Chile, año 2023"
        context = self.prepare_context_lenght(raw_context)
        try:
            response = self.txc.process_input(context)
        except:
            self.semanthic_response = semanthic_response[:int(len(semanthic_response)/2)]
            return self.flow_final_answer(self.sql_response, self.semanthic_response, previous_context)
        return context, response
    
    def flow_final_answer_chat_like(self, sql_response, semanthic_response, previous_context):
        print("---flow_final_answer_chat_like---")
        if sql_response:
            self.sql_response = sql_response
        if semanthic_response:
            self.semanthic_response = semanthic_response
        
        raw_context = f"Eres un asistente Chileno para informar sobre los procesos de elecciones constituyentes en Chile 2023 y tienes que responder preguntas a ciudadanos utilizando la siguiente información que ya ha sido previamente seleccionada para que respondas, asi que debes usarla. Información deterministica de data estructurada sobre candidatos: {self.sql_response}. Información Semántica de Tweeter: {self.semanthic_response}. Escribe una respuestas que ayuden a la gente a responder sus preguntas."
        context = self.prepare_context_lenght(raw_context)
        try:
            messages=[
                {"role": "system", "content": context},
                {"role": "user", "content": self.user_input}
            ]
            response = self.tx_c_chain.process_input(messages)
        except:
            self.semanthic_response = semanthic_response[:int(len(semanthic_response)/2)]
            return self.flow_final_answer_chat_like(self.sql_response, self.semanthic_response, previous_context)
        return context, response

    def prepare_context_lenght(self, context):
        token_max = 3800
        context_tokens_list = context.split(" ")
        #print(context)
        #print(len(context_tokens_list))
        semanthic_response_tokens_list = self.semanthic_response.split(" ")
        sql_response_tokens_list = self.sql_response.split(" ")
        if len(context_tokens_list)>token_max:
            if len(sql_response_tokens_list)>token_max:
                self.sql_response = "output demasiado largo"
                return f"Requerimiento: {self.user_input}. Información SQL: {self.sql_response}. Información Semántica Tweeter: {self.semanthic_response}. Escribe una respuesta que responda el requerimiento, dado el contexto de las elecciones de constituyentes en Chile, año 2023"
            if len(semanthic_response_tokens_list)>token_max:
                self.semanthic_response = " ".join(semanthic_response_tokens_list[:token_max])
                self.prepare_context_lenght(f"Requerimiento: {self.user_input}. Información SQL: {self.sql_response}. Información Semántica Tweeter: {self.semanthic_response}. Escribe una respuesta que responda el requerimiento, dado el contexto de las elecciones de constituyentes en Chile, año 2023")
            else:
                self.semanthic_response = " ".join(semanthic_response_tokens_list[:-50])
                self.prepare_context_lenght(f"Requerimiento: {self.user_input}. Información SQL: {self.sql_response}. Información Semántica Tweeter: {self.semanthic_response}. Escribe una respuesta que responda el requerimiento, dado el contexto de las elecciones de constituyentes en Chile, año 2023")
        else:
            return f"Requerimiento: {self.user_input}. Información SQL: {self.sql_response}. Información Semántica Tweeter: {self.semanthic_response}. Escribe una respuesta que responda el requerimiento, dado el contexto de las elecciones de constituyentes en Chile, año 2023"
            # limit tweets

    def get_sql_response(self, promt_with_sql_query):
        index = promt_with_sql_query.find("SELECT")
        
        if index == -1:
            return None
        
        sql_query = promt_with_sql_query[index:]
        sql_query = sql_query.replace('"', "'")
        rows = execute_query(sql_query, self.db_elections)
        if rows is None:
            return None

        result = ""
        for row in rows:
            result = result + " " + str(row) 
        
        if result == "":
            return None
        
        return result
        
    def exit_flow(self, input, previous_context):
        print("---exit_flow---")
        response = "No puedo responder, la pregunta no es relevante para las elecciones"
        context = previous_context
        return context, response
    
    def flow_only_twitter_or_add_sql(self, input, previous_context):
        print("---flow_only_twitter_or_add_sql---")
        question = f"""Responde con "2" si puedes responder solamente con data no estructurada
                    de twitter o con un "3" si necesitas agregar información de la data estructurada de
                    las tablas? Respuesta (responde solamente con "2", "3"):"""
        
        context = previous_context+input+"\n"+question

        response = self.txc.process_input(context)

        if "2" in response.lower():
            return self.flow_only_semanthic_twitter(input=context+response, previous_context=context)

        elif "3" in response.lower():
            return self.flow_separate_in_sql_and_semanthic_tweet(input=self.user_input, previous_context=context)
    
    def flow_only_semanthic_twitter(self, input, previous_context):
        print("---flow_only_semanthic_twitter---")
        list_ids = similarity_tweet(self.user_input, limit=10, vector_list=self.vector_list)
        tweets = retrieve_tweets(list_ids, self.db_elections)
        tweets_promt = ""
        for tweet in tweets:
                tweets_promt += tweet[0]+'\n'
        return self.flow_final_answer(sql_response=None, semanthic_response=tweets_promt, previous_context=input+"\n"+tweets_promt)
