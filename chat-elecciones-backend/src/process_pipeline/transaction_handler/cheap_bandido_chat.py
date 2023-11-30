from src.process_pipeline.generic_transaction import GenericTransaction
from src.process_pipeline.transaction_chain import TransactionChain
from src.process_pipeline.transaction_chain_chat import TransactionChainChat
from src.process_pipeline.transaction_chain_edit import TransactionChainEdit

from src.process_pipeline.tools.ann import similarity_tweet
from src.process_pipeline.tools.sql_execute import retrieve_tweets
from src.process_pipeline.tools.sql_execute import execute_query
from sqlalchemy.orm import Session
import ast
import re


#PUT MANY TRY AND CATCH SO YOU GO BACK TO SEM IF PROBLEM !!



class CheapBandidoChat(GenericTransaction):
    def __init__(self, conversation, vector_list, db_chatdata: Session, db_elections: Session) -> None:
        super().__init__('BandidoChat',conversation)
        self.db_chatdata = db_chatdata
        self.db_elections = db_elections
        self.txc = TransactionChain(self.tx_id, self.db_chatdata)
        self.tx_c_chain = TransactionChainChat(self.tx_id, self.db_chatdata)
        #self.tx_c_edit = TransactionChainEdit(self.tx_id, self.db_chatdata)
        self.user_input = ""
        self.sql_query = "No disponible"
        self.sql_response = "No disponible"
        self.semanthic_response = "No disponible"
        # here you can change between completion or chat end responses, completions are better but may be incomplete
        self.use_completion_model = False
        self.vector_list = vector_list
        self.old_user_input = None
        self.only_sql = False 
        

    def process_input(self, input:str) -> str:

        #print(self.conversation.get_history())

        print("Flows used:")
        input = input.rstrip()
        self.user_input = input
        context, response = self.initial_input_process(input, previous_context="")
        #print("initial_context:\n\n"+context)
        #print("\n\n"+response)
        return response
    
    def initial_input_process(self, input, previous_context):
        print("---initial_input_process---")


        edit_text = f"""Contexto: Eres un bot que dado un requerimiento en formato de texto, es capaz de entregar información sobre las elecciones constituyentes y los candidatos a las elecciones de constituyentes en Chile, año 2023.
Tienes acceso a 2 tipos de información: 
1: data estructurada oficial del sistema electoral chileno en una tabla cuyo esquema es candidatos(nombre, twitter_account, twitter_account_id, sexo, edad, profesion, num_region, nom_region, financiamiento, description, partido, pacto), la cual contiene información de los candidatos constituyentes que participarán en el proceso de elecciones. un ejemplo de la data que contiene es . sexo toma valores "mujer" o "hombre". nom_region puede tomar valores Coquimbo,Ohiggins,Ñuble,Valparaíso,Los Rios,Magallanes,Tarapacá,Los Lagos,Arica y Parinacota,Antofagasta, Araucania,Aysen,Atacama,Biobio,Maule,Metropolitana. Partido puede tomar valores PC, PDG, RN, PL, IND, AH, PR, PPD, UDI, RD, PS, COM, REP, EVO, DC, CS, FRVS.
2: Data no estructurada de textos de Twitter escritos por los candidatos constituyentes, con lo que puedes mostrar información que refleje las tendencias ideológicas u opiniones de cada candidato, además de información del proceso constituyente. Y puede interpretar opiniones. 
Si te llega este requerimiento:"{self.user_input}
" 
Responde las preguntas a), b) y c) usando solamente el string "1" si es verdad, o "0" si es falso. 
a) Sirve usar la información 1 para este requerimiento? Respuesta: [?]
b) Sirve usar la información 2 para este requerimiento? Respuesta: [?]
c) Necesitas agregar información que refleje las tendencias ideológicas u opiniones de cada candidato, además de información del proceso constituyente. Y puede interpretar opiniones? Respuesta: [?]
d) Necesitas agregar información de la data estructurada de las tablas Respuesta: [?]
Ahora responde las preguntas e), f) y g) como si fueras un experto en geografía Chilena.
e) Si el requerimiento menciona un lugar geográfico especifico de chile, escribelo. Si no menciona un lugar, escribe el string " ". Respuesta: [?]
f) Si la respuesta a e) es "", escribe "". Si no, escribe la región administrativa de Chile (Coquimbo,Ohiggins,Ñuble,Valparaíso,Los Rios,Magallanes,Tarapacá,Los Lagos,Arica y Parinacota,Antofagasta, Araucania,Aysen,Atacama,Biobio,Maule,Metropolitana) a la que se refiere ese lugar.  Respuesta: [?]
g) reescribe el requerimiento para que mencione la región en vez del lugar. Respuesta: [?]

 Replace each occurrence of the string "[?]" with the best answer to the question. 
Then return a python ordered list containing your answers. The format for the answer is [1/0,1/0,1/0,1/0,'<string>','<string>','<string>']"""


        messages=[
                {"role": "system", "content": edit_text},
                {"role": "assistant", "content": '['}
            ]
        response = self.tx_c_chain.process_input(messages)

        pattern = r'\[.*?\]'
        # Use the re.findall() function to find all matches of the pattern in the input string
        matches = re.findall(pattern, '['+response)
        #print(matches[0])
        #response = self.tx_c_edit.process_input(edit_text, 'Replace each occurrence of the string "[?]" with the best answer to the question.',)

        
        try:
            processed_list = ast.literal_eval(matches[0])
        except ValueError as e:
            # handle the exception here
            #print("An error occurred while parsing the response:", e)
            return self.flow_separate_in_sql_and_semanthic_tweet()
        except SyntaxError as e:
            #print("An error occurred while parsing the response:", e)
            return self.flow_separate_in_sql_and_semanthic_tweet()
        #print("#####RESPONSE#######")
        #print(processed_list)
        #print(response)

        for i in range(0,4):
            processed_list[i] = int(processed_list[i])

        modify = True
        for i in range(4,7):
            if processed_list[i] == '' or processed_list[i] == ' ':
                modify = False
                break
        if modify:
            self.old_user_input = self.user_input
            self.user_input = processed_list[6]


        sql = False
        semantic = True
        if processed_list[0] + processed_list[3] > 0:
            sql = True
            if processed_list[1] + processed_list[2] == 0:
                semantic = False

        if (sql and semantic):
            return self.flow_separate_in_sql_and_semanthic_tweet()
        elif(sql):
            return self.flow_create_sql_query()
        else:
            return self.flow_only_semanthic_twitter()
        
        
        
    def flow_separate_in_sql_and_semanthic_tweet(self):
        print("---flow_separate_in_sql_and_semanthic_tweet---")

        system = f"""#Chile 2 mayo 2023.
#Examen de procesamiento de datos avanzado.
#Tablas en postgreSQL: 
#tweets(date,user_real_name,username,text,likes,retweets, is_retweet,bio) 
#candidatos (nombre,sexo,edad,profesion,pacto,partido, twitter_account,num_region,nom_region,financiamiento,description)" 
#comunas(comuna,region)
#Pregunta: Quieres usar busqueda semantica para filtrar por campos text y SQL para filtrar deterministicamente los otros campos. Divide el requerimiento en dos frases completamente distinctas, una que contiene la parte de SQL, y otra la parte semantica. Tu respuesta debe venir como un vector. 
Por ejemplo, la respuesta a "que opinan los candidatos de Valparaiso sobre las pensiones el en septiembre" es ['que opinan los candidatos de Valparaiso','pensiones'].
La respuesta a "Busco candidatas feministas de mas de 30 anos en Santiago" es ['busco candidatas en santiago de mas de 30 anos','feminismo'].
La respuesta a "que opino Juan Sequedda sobre delinquencia" es ['que opino Juan Sequedda','delinquencia'].
La respuesta a "quien es la persona mas ecologista la ultima semana" es ['quien es la persona la ultima semana','ecologia'].
La respuesta a "quien defiende a la empresa en el Maule ayer" es ['quien en el Maule ayer','empresa'].
La respuesta a "cuales son los ideas por subir las pensiones" es ['NA','idea por subir las pensiones'].
La respuesta a "candidatos que se oponen a subir pensiones ayer" es ['candidatos ayer','oponen a subir pensiones'].
La respuesta a "{self.user_input}" es [?]

You must replace the [?] with the most relevant answer."""

        messages=[
                {"role": "system", "content": system},
                {"role": "assistant", "content": '[\''}
            ]
        #print(system)
        #response = self.txc.process_input(context)
        response = self.tx_c_chain.process_input(messages)
        response = '[\''+response
        response = response.replace("\n", " ")
        #print(response)

        try:
            processed_list = ast.literal_eval(response)
            semanthic = processed_list[1]
            sql_deterministic = processed_list[0]
        except ValueError as e:
            # handle the exception here
            #print("An error occurred while parsing the response:", e)
            return self.flow_create_sql_query()
        except SyntaxError as e:
            # handle the exception here
            #print("An error occurred while parsing the response:", e)
            return self.flow_create_sql_query()
        except IndexError as e:
            # handle the exception here
            #print("An error occurred while parsing the response:", e)
            return self.flow_create_sql_query()
            
        #print(response)
        #pattern = r'\[.*?\]'
        # Use the re.findall() function to find all matches of the pattern in the input string
        #matches = re.findall(pattern, '['+response)
        #print(matches[0])
       

        #print("####### SQL - SEM ########")
        #print(processed_list)

        if (semanthic == 'NA' or semanthic == '' or semanthic == ' '):
            return self.flow_create_sql_query()

        
    
        system = f"""#Examen de procesamiento de datos avanzado
#Tablas en postgreSQL: 
#twitter_data(tweet_id, date, twitter_account_id)
#candidatos(nombre, twitter_account, twitter_account_id, sexo, edad, profesion, num_region, nom_region, financiamiento, description, partido, pacto), sexo toma valores "mujer" o "hombre". nom_region puede tomar valores Coquimbo,Ohiggins,Ñuble,Valparaíso,Los Rios,Magallanes,Tarapacá,Los Lagos,Arica y Parinacota,Antofagasta, Araucania,Aysen,Atacama,Biobio,Maule,Metropolitana. Partido puede tomar valores PC, PDG, RN, PL, IND, AH, PR, PPD, UDI, RD, PS, COM, REP, EVO, DC, CS, FRVS'. Los partidos de izquierda son PC, PL, AH, PR, PPD, PS, COM, RD. Los partidos de  centro son PDG, DC, FRVS. Los partidos de derecha son RN, EVO, UDI, REP. 
#Requerimiento: "{sql_deterministic}". 
#Pregunta a): Escribe una consulta SQL que te permita encontrar los candidatos y los tweet_id de los tweet que ha dicho, la consulta debe retornar unicamente y solamente un columna tweet_id. 
#Pregunta b): Escribe una consulta SQL igual a la de la parte a), solo que en vez de seleccionar tweet_id seleccionas la información de la tabla candidatos relevante. 

Escribe tu respuesta como un vector :[<respuesta a a)>,<respuesta a b)>]"""

        messages=[
                {"role": "system", "content": system},
                {"role": "assistant", "content": '["SELECT'}
            ]
        #print(system)
        #response = self.txc.process_input(context)
        response = self.tx_c_chain.process_input(messages)
        response = '["SELECT ' + response
        response = response.replace("\n", " ")
        #print(response)
        try:
            processed_list = ast.literal_eval(response)
        except ValueError as e:
            # handle the exception here
            #print("An error occurred while parsing the response:", e)
            return self.flow_create_sql_query()
        except SyntaxError as e:
            #print("An error occurred while parsing the response:", e)
            return self.flow_create_sql_query()
        #print(response_sql_filter)

        sql_query = processed_list[0]
        #print("####### SQL Query ########")
        #print(sql_query)
        sql_response,_ = self.get_sql_response(sql_query)

        #print(self.sql_response)

        if sql_response is None or len(sql_response) == 0:
            self.sql_response = "No disponible"
            return self.flow_only_semanthic_twitter()

        


        tweet_id_list = self.row_list_to_int_list(sql_response)

        list_ids = similarity_tweet(semanthic, candidates_id=tweet_id_list, limit=16, vector_list=self.vector_list)
        tweets = retrieve_tweets(list_ids, self.db_elections)
        tweets_promt = ""
        id = 0
        for tweet in tweets:
                #tweets_promt += 'TWEET_ID ='+str(id)+" TWEET="+str(tweet[0])+'\n'
                tweets_promt += "TWEET="+' <SEP> REGION: '+tweet[1]+' <SEP> PARTIDO:'+tweet[2]+' <SEP> PACTO:'+tweet[3]+' <SEP> '+str(tweet[0])+'\n'
                id += 1
        self.semanthic_response = tweets_promt

        self.sql_query = processed_list[1]

        sql_response,column_names = self.get_sql_response(self.sql_query)

        if( sql_response is None):
            self.sql_query = "No disponible"
            #self.sql_response = "Mas que 30 resultados"
        
            #dicarded = len(sql_response) - 40
            #sql_response = sql_response[0:39]
        if len(sql_response) > 80:
            if len(sql_response) > 500:
                sql_response = sql_response[:500]
            nombre = self.get_index_column(column_names,'nombre')
            partido = self.get_index_column(column_names,'partido')
            pacto = self.get_index_column(column_names,'pacto')
            nom_region = self.get_index_column(column_names,'nom_region')

            indexes = []
            if nombre!= -1:
                indexes += [nombre]
            if partido!= -1:
                indexes += [partido]
            if pacto!= -1:
                indexes += [pacto]
            if nom_region != -1:
                indexes += [nom_region]

            indexes = sorted(indexes)

            self.sql_response = ''
            for index in indexes:
                self.sql_response += column_names[index]+','
            self.sql_response= str(self.sql_response[0:-1]) + '\n'
            #self.sql_response = list(set(self.sql_response))

            for row in sql_response:
                temp = ''
                for index in indexes:
                    temp += row[index]+','
                self.sql_response += str(temp[0:-1]) + '\n'

        else: 
            self.sql_response = str(column_names)
            self.sql_response= str(self.sql_response) + '\n'
            for row in sql_response:
                self.sql_response += str(row)+'\n'

        return self.flow_final_answer_chat_like()

    
    def row_list_to_int_list(self, rows):
        # Convert each number from a string to an integer
        int_list = [int(row[0]) for row in rows]
        return int_list

    def flow_create_sql_query(self):
        print("---flow_create_sql_query---")
        question = f"""Escribe una consulta SQL que responda el Requerimiento:
 {self.user_input} usando las tablas
#candidatos(nombre, twitter_account, twitter_account_id, sexo, edad, profesion, num_region, nom_region, financiamiento, description, partido, pacto).
sexo toma valores "mujer" o "hombre". 
nom_region puede tomar valores Coquimbo,Ohiggins,Ñuble,Valparaíso,Los Rios,Magallanes,Tarapacá,Los Lagos,Arica y Parinacota,Antofagasta, Araucania,Aysen,Atacama,Biobio,Maule,Metropolitana.
partido puede tomar valores PC, PDG, RN, PL, IND, AH, PR, PPD, UDI, RD, PS, COM, REP, EVO, DC, CS, FRVS'.
 """

        system = f"""#Examen de procesamiento de datos avanzado
#Tablas en postgreSQL: 
#twitter_data(tweet_id, date, twitter_account_id)
#candidatos(nombre, twitter_account, twitter_account_id, sexo, edad, profesion, num_region, nom_region, financiamiento, description, partido, pacto), sexo toma valores "mujer" o "hombre". nom_region puede tomar valores Coquimbo,Ohiggins,Ñuble,Valparaíso,Los Rios,Magallanes,Tarapacá,Los Lagos,Arica y Parinacota,Antofagasta, Araucania,Aysen,Atacama,Biobio,Maule,Metropolitana. Partido puede tomar valores PC, PDG, RN, PL, IND, AH, PR, PPD, UDI, RD, PS, COM, REP, EVO, DC, CS, FRVS'. Los partidos de izquierda son PC, PL, AH, PR, PPD, PS, COM, RD. Los partidos de  centro son PDG, DC, FRVS. Los partidos de derecha son RN, EVO, UDI, REP. 
#Requerimiento: "{self.user_input}". 
#Pregunta: Escribe una consulta SQL que te permita encontrar la information. 

Escribe tu consulta SQL: """

        messages=[
                {"role": "system", "content": system},
                {"role": "assistant", "content": 'SELECT'}
            ]

       #print(self.user_input)
        #messages=[
        #        {"role": "system", "content": question},
        #        {"role": "assistant", "content": 'SELECT'}
        #    ]
        response = self.tx_c_chain.process_input(messages)
        index = response.find("SELECT")
        if response.find("SELECT") == -1 or  index > 5:
            response = 'SELECT '+response
        response = response.replace("\n", " ")
        #print(response)
        #print(response_sql_filter)
        self.sql_query = response

       #print(response)
        #response = self.tx_c_edit.process_input(edit_text, 'Replace each occurrence of the string "[?]" with the best answer to the question.',)


        #context = "1\n"+question

        #response = self.txc.process_input(context)

        #print(response)

        #promt_with_sql_query = context+response
        sql_response,column_names = self.get_sql_response(self.sql_query)

        if sql_response is None or len(sql_response) == 0:
            #GO TO SEMSEARCH
            return self.flow_only_semanthic_twitter()

        if (len(sql_response) > 40):
            if len(sql_response) > 500:
                sql_response = sql_response[:500]

            nombre = self.get_index_column(column_names,'nombre')
            partido = self.get_index_column(column_names,'partido')
            pacto = self.get_index_column(column_names,'pacto')
            nom_region = self.get_index_column(column_names,'nom_region')

            indexes = []
            if nombre!= -1:
                indexes += [nombre]
            if partido!= -1:
                indexes += [partido]
            if pacto!= -1:
                indexes += [pacto]
            if nom_region != -1:
                indexes += [nom_region]

            indexes = sorted(indexes)

            self.sql_response = ''
            for index in indexes:
                self.sql_response += column_names[index]+','
            self.sql_response= str(self.sql_response[0:-1]) + '\n'

            for row in sql_response:
                temp = ''
                for index in indexes:
                    temp += row[index]+','
                self.sql_response += str(temp[0:-1]) + '\n'
        else: 
            self.sql_response = str(column_names)
            self.sql_response= self.sql_response + '\n'
            for row in sql_response:
                self.sql_response += str(row)+'\n'

        self.only_sql = True
        return self.flow_only_semanthic_twitter(number = 5)
        #return self.flow_final_answer_chat_only_sql()

    def get_index_column(self,column_names,string):
        for i, name in enumerate(column_names):
            if string == name:
                return i
        return -1        



    
    def flow_final_answer_chat_like(self):
        print("---flow_final_answer_chat_like---")
        #if sql_response:
        #    self.sql_response = sql_response
        #if semanthic_response:
        #    self.semanthic_response = semanthic_response
        system = f"""Hoy dia es el 3 de mayo 2023. Eres un asistente Chileno para informar sobre los procesos de elecciones constituyentes en Chile 2023 que solo responde la pregunta utilizando la información contenida en los tweets de los canditatos o la respuesta que te envia el servel, si no puedes responder la pregunta, trata de contestar algo cercano, si no simplemente indica que no puedes hacerlo, explica brevemente porque, y luego intenta resumir la información que se te entrega. Es importante entregar información citando los nombres de los candidatos que dicen eso en sus tweets."""
        system += f"""
PREGUNTA USUARIO: {self.user_input} """
        system  +=  f"""
TWEETS DE CANDIDATOS:
{self.semanthic_response}"""
        if not(self.sql_query == "No disponible" or self.sql_response == "No disponible" or self.sql_query == "" or self.sql_response == ""):
            system  +=  f"""
Datos SERVEL header: {self.get_sql_attributes(self.sql_query)}
Datos SERVEL answers: {self.sql_response}"""

        #print(system)
        messages=[
                {"role": "system", "content": system},
                #{"role": "user", "content": self.user_input}
                {"role": "user", "content": ""}
            ]
        response = self.tx_c_chain.process_input(messages)
        return '', response

    def flow_final_answer_chat_only_sql(self):
        print("---flow_final_answer_chat_only_sql---")
        #if sql_response:
        #    self.sql_response = sql_response
        #if semanthic_response:
        #    self.semanthic_response = semanthic_response
        system = f"""Hoy dia es el 3 de mayo 2023. Eres un asistente Chileno para informar sobre los procesos de elecciones constituyentes en Chile 2023 que solo elabora una respuesta en base a los datos consultados al servel. Si no puedes responder, explica brevemente por que. Si lo encuentras pertinente, hemos incluido algunos tweets para que complementes tu respuesta """
        system += f"""
PREGUNTA USUARIO: {self.user_input} """
        system  +=  f"""
Consulta al SERVEL {self.get_sql_attributes(self.user_input)}        
Datos SERVEL header: {self.get_sql_attributes(self.sql_query)}
Datos SERVEL answers: {self.sql_response}"""
        system  +=  f"""
TWEETS DE CANDIDATOS: {self.semanthic_response}"""

        #print(system)
        messages=[
                {"role": "system", "content": system},
                #{"role": "user", "content": self.user_input}
                {"role": "user", "content": ""}
            ]
        response = self.tx_c_chain.process_input(messages)
        return '', response


    def get_sql_response(self, promt_with_sql_query):
        index = promt_with_sql_query.find("SELECT")
        
        if index == -1:
            return None
        
        sql_query = promt_with_sql_query[index:]
        sql_query = sql_query.replace('"', "'")
        rows,column_names = execute_query(sql_query, self.db_elections)
        if rows is None:
            return None,None

        return rows,column_names

    
    def flow_only_semanthic_twitter(self,number = 20):
        print("---flow_only_semanthic_twitter---")
        if self.old_user_input != None:
            self.user_input = self.old_user_input
        list_ids = similarity_tweet(self.user_input, limit=number, vector_list=self.vector_list)
        tweets = retrieve_tweets(list_ids, self.db_elections)
        if tweets == None:
            return self.flow_final_answer_chat_like()
        tweets_promt = ''
        id = 0
        for tweet in tweets:
                #tweets_promt += 'TWEET_ID ='+str(id)+" TWEET="+str(tweet[0])+'\n'
                tweets_promt += "TWEET="+' <SEP> REGION: '+tweet[1]+' <SEP> PARTIDO:'+tweet[2]+' <SEP> PACTO:'+tweet[3]+' <SEP> '+str(tweet[0])+'\n'
                id += 1
        self.semanthic_response = tweets_promt
        if self.only_sql: 
            return self.flow_final_answer_chat_only_sql()
        return self.flow_final_answer_chat_like()

    def get_sql_attributes(self, query:str):

        # Regular expression to match the first SELECT clause of the query
        select_pattern = r"(?i)\bSELECT\b(.*?)(?:(?:(?<=FROM)|(?<=UNION))(?!.*\bSELECT\b))"

        # Extract the selected attributes from the query using the regular expression
        matches = re.search(select_pattern, query)

        if matches:
            # Get the matched string and split it into individual attributes
            selected_attributes = matches.group(1)
            selected_attributes = selected_attributes.replace("DISTINCT","")
            selected_attributes = selected_attributes.replace("UNION","")
            selected_attributes = selected_attributes.replace("FROM","")
            attribute_list = selected_attributes.split(",")
            final_list = []
            for attr in attribute_list:
                final_list.append(attr.strip().split(".")[-1])
            if "*" in final_list[0]:
                return "[nombre, twitter_account, twitter_account_id, sexo, edad, profesion, num_region, nom_region, financiamiento, description, partido, pacto]"
            return str(final_list)
        else:
            return query.replace("SQL","")