from src.process_pipeline.generic_transaction import GenericTransaction
from src.process_pipeline.transaction_chain import TransactionChain
from src.process_pipeline.transaction_chain_chat import TransactionChainChat
from src.process_pipeline.tools.ann import similarity_tweet
from src.process_pipeline.tools.sql_execute import retrieve_tweets
from src.process_pipeline.tools.sql_execute import execute_query
from sqlalchemy.orm import Session

class HakushuChat(GenericTransaction):
    def __init__(self, conversation, vector_list, db_chatdata: Session, db_elections: Session) -> None:
        super().__init__('MarceloTxChat', conversation)
        self.db_chatdata = db_chatdata
        self.db_elections = db_elections
        self.vector_list = vector_list

    def process_input(self, input: str) -> str:

        txc = TransactionChain(self.tx_id, self.db_chatdata)

        start = f"""Tengo esta descripcion de API: El bot de elecciones está entrenado para entregar información 
        sobre candidatos a las elecciones en Chile, sobre lo que ha dicho cada persona 
        especifica en este mundo, y sobre contingencia Chilena. Y tengo este requerimiento: "{input}" 
        Pregunta: se puede usar la API para resolver este requerimiento? Responde 1 si tu respuesta es si, o 0 si tu respuesta es no. Respuesta: 
        """ 


        flow1 = txc.process_input(start)

        if "1" not in flow1 :
            return "Disculpa, soy un robot prototpio que solo está entrenado para responder consultas dobre las elecciones del próximo 7 de Mayo. ¿Quizás entendí algo mal? Prueba específicando mejor tu pregunta."

        #official = f"""# Eres el servicio electoral de Chile, puedes informar sobre los candidatos, la unica informacion que puedes divulgar es la informacion publica y oficial. 
        ## Requerimiento: {input}
        ## Pregunta. Puedes responder esto? escribe solo 1 por "si" o 0 por "no":
        #"""
        official = f"""# Eres el servicio electoral de Chile, puedes informar y contestar preguntas sobre los candidatos, la unica informacion que puedes divulgar es: nombre, sexo, edad, profesion, region, partido y pacto.
        # Requerimiento: {input}
        # Pregunta. Puedes responder esto? escribe solo 1 por "si" o 0 por "no": 
        """

        flow2 = txc.process_input(official)
        if "1" in flow2: 
            print("entrando a parte de info candidatos nomas")

            query = f"""Estas en Chile, Mayo del año 2023. Examen de base de datos avanzado. Tienes una tabla 
            candidatos (nombre, twitter_account, twitter_account_id, sexo, edad, profesion, num_region, nom_region, financiamiento, partido, pacto). sexo toma valores "mujer" o "hombre". nom_region puede tomar valores Coquimbo, Ohiggins, Ñuble, Valparaíso, Tarapacá, Atacama, Biobio, Maule,Arica y Parinacota,Antofagasta,Metropolitana. Partido puede tomar valores PC, PDG, RN, PL, IND, AH, PR, PPD, UDI, RD, PS, COM, REP, EVO, DC, CS, FRVS'. 
            Tienes el siguiente requermiento: {input}. Pregunta: 
            a) Si el requerimiento menciona un lugar geográfico de chile, escribe la región administrativa de Chile a la que se refiere ese lugar. Por ejemplo, "lota" se refiere a la región del bío bío. Si no menciona un lugar específico, escribe "". 
            b) reemplaza el requerimiento para que ahora mencione a la región en vez del lugar (si existe)
            c) escribe una consulta SQL que te permita responder al requerimiento en b). Recuerda usar like para comparar stirngs. 
            """


            sqlofficial = txc.process_input(query)

            print(sqlofficial)
            index = sqlofficial.find("c)")
            if index == -1:
                return "Disculpa, soy un robot prototpio Y algo hize mal. Prueba otra vez y seguro aprendo!"
            cleansql= sqlofficial[index+len("c)"):]

            print(cleansql)

            rows = execute_query(cleansql, self.db_elections)
            result = ""
            for row in rows:
                result = result + " " + str(row) 
            if result == "": 
                return "Disculpa, soy un robot prototpio, no encontre datos. Prueba otra vez y seguro aprendo!"

            print(result)

            response = "Requerimiento" + input + ". Informacion: " + result + "Escribe un codigo markdown con un resumen sencillo que responda al requerimiento"

            return txc.process_input(response + "Ten en cuenta que la única información oficial es la del Servicio Electoral.")

        else: 
            print("entrando a parte semantica")

            persona = """Es verdad que este requerimiento solo tiene que ver con lo que dice una persona? 
            {input}. Responde escribe solo 1 por "si" o 0 por "no"
            """

            #return "not yet!"

            divide = f"""# Chile, año 2023. 
#Examen de procesamiento de datos avanzado
#Tablas en postgreSQL: 
#tweets(date,user_real_name,username,text,likes,retweets, is_retweet,bio) 
 #candidatos (nombre,sexo,edad,profesion,pacto,partido, twitter_account,num_region,nom_region,financiamiento,descripcion)" 
#comunas(comuna,region)
 #Requerimiento: "{input}". 
#Pregunta: Quieres usar busqueda semantica para filtrar por campos text, bio y descripcion, y SQL para filtrar deterministicamente los otros campos. Para esto: 
a) Divide el requerimiento en dos frases, una que contiene la parte de SQL, y otra la parte semantica. Por ejemplo, la frase "que opinan los candidatos de Valparaiso sobre las AFPs" debe dividirse en "que opinan los candidatos de Valparaiso" y "AFPs". La frase "Busco candidatas feministas en Santiago" debe dividirse en "busco candidatas en santiago" y "feminismo". 
Escribe la dos frase a continuación, primero la primera frase (para usar SQL), un guion - , y luego la segunda frase(semantica): """

            answerdivide = txc.process_input(divide)

            print(answerdivide)

            lines = answerdivide.split("-")

            first_line = lines[0].replace('"', '')
            second_line = lines[1].replace('"', '')
            print(first_line)
            print(second_line)

            #### HACK ###
            #### Cuando se refiere a un candidato, pone al candidato abajo, y lo quiero sacar. PEro hay que hacerlo mejor. 

            if second_line in first_line or 'opin' in second_line or 'dic' in second_line:
                second_line = ""

            print(first_line)
            print(second_line)
  

            if second_line == "":
                print("entrando a nombre")
                construct = f""" # Chile, año 2023. 
                          Examen de SQL avanzado. Tablas en postgreSQL: 
                        twitter_data(tweet_id, date, twitter_account, twitter_account_id, text_content, likes, retweets)
                        candidatos(nombre, twitter_account_id, sexo, edad, profesion, nom_region, description, partido, pacto)
                        sexo toma valores "mujer" o "hombre". nom_region puede tomar valores Coquimbo, Ohiggins, Ñuble, Valparaíso, Tarapacá, Atacama, Biobio, Maule, Arica y Parinacota,Antofagasta,Metropolitana. Partido puede tomar valores PC, PDG, RN, PL, IND, AH, PR, PPD, UDI, RD, PS, COM, REP, EVO, DC, CS, FRVS.
                        # Requerimiento: "{first_line}"
                        # Pregunta: 
                        a) Si el requerimiento menciona un lugar geográfico de chile, escribe la región administrativa de Chile a la que se refiere ese lugar. Por ejemplo, "lota" se refiere a la región del bío bío. 
                        b) Si a no es "", reemplaza el requerimiento para que ahora mencione a la región en vez del lugar 
                        c) Escribe una consulta SQL que te permita resolver el requerimiento de la parte b), usando likes para ordenar los tweets. 
                        d) Reemplaza todas las instancias tipo atributo = 'string' por atributo like '%string%'
                        Respuesta:"""

                sqlconstruct = txc.process_input(construct)

                index = sqlconstruct.find("d)")
                if index == -1:
                    return "Disculpa, soy un robot prototpio Y algo hize mal. Prueba otra vez y seguro aprendo!"

                cleansql= sqlconstruct[index+len("d)"):]
                rows = execute_query(cleansql, self.db_elections)
                count = 0
                result = ""
                for row in rows:
                    if count < 20:
                        result = result + " " + str(row) 
                        count += 1
                    else: 
                        break

                if result == "": 
                    return "Disculpa, soy un robot prototpio, no encontre datos. Prueba otra vez y seguro aprendo!"
                else: 
                    response = "Requerimiento" + input + ". Informacion: " + result + "Escribe un codigo markdown con un resumen sencillo que responda al requerimiento"
                    return txc.process_input(response)


            #### aca Marcelo hace su gracia con cur y second line
            construct = f""" # Chile, año 2023. 
                          Examen de SQL avanzado. Tablas en postgreSQL: 
                        twitter_data(tweet_id, date, twitter_account, twitter_account_id, text_content, likes, retweets)
                        candidatos(nombre, twitter_account_id, sexo, edad, profesion, nom_region, description, partido, pacto)
                        sexo toma valores "mujer" o "hombre". nom_region puede tomar valores Coquimbo, Ohiggins, Ñuble, Valparaíso, Tarapacá, Atacama, Biobio, Maule, Arica y Parinacota,Antofagasta,Metropolitana. Partido puede tomar valores PC, PDG, RN, PL, IND, AH, PR, PPD, UDI, RD, PS, COM, REP, EVO, DC, CS, FRVS.
                        # Requerimiento: "{first_line}"
                        # Pregunta: 
                        a) Si el requerimiento menciona un lugar geográfico de chile, escribe la región administrativa de Chile a la que se refiere ese lugar. Por ejemplo, "lota" se refiere a la región del bío bío. 
                        b) Si a no es "", reemplaza el requerimiento para que ahora mencione a la región en vez del lugar 
                        c) Escribe una consulta SQL que te entregue solo los tweet_ids de los tweets necesarios para resolver el requerimiento de la parte b), usando likes para ordenar los tweets. 
                        d) Reemplaza todas las instancias tipo atributo = 'string' por atributo like '%string%'
                        Respuesta:"""
            

            sqlconstruct = txc.process_input(construct)

            index = sqlconstruct.find("d)")
            if index == -1:
                return "Disculpa, soy un robot prototpio Y algo hize mal. Prueba otra vez y seguro aprendo!"

            cleansql= sqlconstruct[index+len("d)"):]
            rows = execute_query(cleansql, self.db_elections)
            candidates = []
            if len(rows) == 0:
                print(cleansql)
                return "Disculpa, soy un robot prototpio Y algo hize mal. Prueba otra vez y seguro aprendo!"

                
            for row in rows:
                candidates += [row[0]]

            list_ids = similarity_tweet(second_line, candidates, vector_list=self.vector_list)

            tweets = retrieve_tweets(list_ids)

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


