import psycopg2

# Connect to the PostgreSQL database
conn = psycopg2.connect(
    host="db-postgresql-nyc1-26343-do-user-9263663-0.b.db.ondigitalocean.com",
    port="25060",
    database="chatdata",
    user="chatdata",
    password="AVNS_AHdFDceQspT81IXGQ0w"
)


class Conversation():

    #@abstractmethod
    #def process_input(self,input:str):
    #    pass

    def __init__(self,session_id) -> None:
        super().__init__()
        self.session_id = session_id
        self.conv_id = self.get_or_create_conversation(self.session_id)
        self.last_tx_id = ''



    def get_history(self,tx_id = None):
        if tx_id == None:
            tx_id = self.last_tx_id
        # Retrieve the conv_id and sequence of the transaction
        cur = conn.cursor()
        cur.execute("SELECT conv_id, sequence FROM transaction WHERE tx_id = %s", (tx_id,))
        result = cur.fetchone()

        # Check if the result is not None
        if result is not None:
            conv_id, sequence = result
            # Retrieve all previous transactions' tx_id, input_value, and output_value for the same conversation ordered by sequence
            cur.execute(
                "SELECT transaction.tx_id, input_value, output_value "
                "FROM transaction "
                "JOIN input_transaction ON transaction.tx_id = input_transaction.tx_id "
                "JOIN output_transaction ON transaction.tx_id = output_transaction.tx_id "
                "WHERE transaction.conv_id = %s AND transaction.sequence < %s "
                "ORDER BY transaction.sequence ASC",
                (conv_id, sequence)
            )
            results = cur.fetchall()
            cur.close()
            return results
        else:
            cur.close()
            return None

    def get_previous_transaction(self,tx_id = None):
        if tx_id == None:
            tx_id = self.last_tx_id
        # Retrieve the conv_id and sequence of the transaction
        cur = conn.cursor()
        cur.execute("SELECT conv_id, sequence FROM transaction WHERE tx_id = %s", (tx_id,))
        result = cur.fetchone()
        # Check if the result is not None
        if result is not None:
            conv_id, sequence = result
            if sequence != 1:
                # Retrieve the input_value and output_value of the transaction with sequence equal to sequence - 1
                cur.execute("SELECT input_transaction.tx_id, input_value, output_value FROM input_transaction JOIN output_transaction ON input_transaction.tx_id = output_transaction.tx_id WHERE input_transaction.tx_id = (SELECT tx_id FROM transaction WHERE conv_id = %s AND sequence = %s)", (conv_id, sequence-1))
                result = cur.fetchone()
                cur.close()
                return result 
        else:
            cur.close()
            return None
        # Close the cursor and connection



    def get_or_create_conversation(self,session_id):
        cur = conn.cursor()
        # Check if conversation exists
        cur.execute("SELECT conv_id FROM conversation WHERE session_id = %s", (session_id,))
        existing_conv = cur.fetchone()
        if existing_conv:
            # Conversation exists, return the conversation ID
            conv_id = existing_conv[0]
        else:
            # Conversation does not exist, create a new entry
            cur.execute("INSERT INTO conversation (session_id, token) VALUES (%s, '') RETURNING conv_id", (session_id,))
            new_conv = cur.fetchone()
            conn.commit()
            # Return the new conversation ID
            conv_id = new_conv[0]
        # Close the cursor
        cur.close()
        # Return the conversation ID
        return conv_id


    def create_transaction(self, pipeline_name):
        cur = conn.cursor()
        # Insert a new transaction into the transaction table
        cur.execute("INSERT INTO transaction (conv_id, timestamp, pipeline_name) VALUES (%s, NOW(), %s) RETURNING tx_id", (self.conv_id, pipeline_name))
        new_tx = cur.fetchone()
        conn.commit()
        # Close the cursor
        cur.close()
        # Return the new transaction ID
        self.last_tx_id = new_tx[0]
        return new_tx[0]

    def save_input(self, tx_id, input_value):
        cur = conn.cursor()
        # Insert a new input transaction into the input_transaction table
        cur.execute("INSERT INTO input_transaction (tx_id, input_value) VALUES (%s, %s)", (tx_id, input_value))
        conn.commit()
        # Close the cursor
        cur.close()

    def save_output(self, tx_id, output_value):
        cur = conn.cursor()
        # Insert a new output transaction into the output_transaction table
        cur.execute("INSERT INTO output_transaction (tx_id, output_value) VALUES (%s, %s)", (tx_id, output_value))
        conn.commit()
        # Close the cursor
        cur.close()