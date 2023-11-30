from sqlalchemy.sql import text
from sqlalchemy.orm import Session

class Conversation():

    def __init__(self, session_id, db: Session) -> None:
        self.session_id = session_id
        self.db = db
        self.conv_id = self.get_or_create_conversation(self.session_id)
        self.last_tx_id = ''

    def get_history(self, tx_id=None):
        if tx_id == None:
            tx_id = self.last_tx_id
        
        # Retrieve the conv_id and sequence of the transaction
        result_proxy = self.db.execute(
            text("SELECT conv_id, sequence FROM transaction WHERE tx_id = :tx_id"),
            { "tx_id": tx_id }
        )
        result = result_proxy.fetchone()

        # Check if the result is not None
        if result is not None:
            conv_id, sequence = result
            # Retrieve all previous transactions' tx_id, input_value, and output_value for the same conversation ordered by sequence
            result_proxy = self.db.execute(
                text(
                    "SELECT transaction.tx_id, input_value, output_value "
                    "FROM transaction "
                    "JOIN input_transaction ON transaction.tx_id = input_transaction.tx_id "
                    "JOIN output_transaction ON transaction.tx_id = output_transaction.tx_id "
                    "WHERE transaction.conv_id = :conv_id AND transaction.sequence < :sequence "
                    "ORDER BY transaction.sequence ASC"
                ),
                {
                    "conv_id": conv_id,
                    "sequence": sequence
                }
            )
            results = result_proxy.fetchall()
            return results
        else:
            return None

    def get_previous_transaction(self, tx_id=None):
        if tx_id == None:
            tx_id = self.last_tx_id
        
        # Retrieve the conv_id and sequence of the transaction
        result_proxy = self.db.execute(
            text("SELECT conv_id, sequence FROM transaction WHERE tx_id = :tx_id"), 
            { "tx_id": tx_id }
        )
        result = result_proxy.fetchone()
        # Check if the result is not None
        if result is not None:
            conv_id, sequence = result
            if sequence != 1:
                # Retrieve the input_value and output_value of the transaction with sequence equal to sequence - 1
                result_proxy = self.db.execute(
                    text(
                        "SELECT input_transaction.tx_id, input_value, output_value "
                        "FROM input_transaction JOIN output_transaction "
                        "ON input_transaction.tx_id = output_transaction.tx_id "
                        "WHERE input_transaction.tx_id = "
                        "(SELECT tx_id FROM transaction WHERE conv_id = :conv_id AND sequence = :sequence)"
                    ), 
                    { 
                        "conv_id": conv_id,
                        "sequence": sequence-1
                    }
                )
                result = result_proxy.fetchone()
                return result 
        else:
            return None



    def get_or_create_conversation(self, session_id):
        result_proxy = self.db.execute(
            text("SELECT conv_id FROM conversation WHERE session_id = :session_id"), 
            { "session_id": session_id }
        )
        existing_conv = result_proxy.fetchone()
        if existing_conv:
            # Conversation exists, return the conversation ID
            conv_id = existing_conv[0]
        else:
            # Conversation does not exist, create a new entry
            result_proxy = self.db.execute(
                text("INSERT INTO conversation (session_id, token) VALUES (:session_id, '') RETURNING conv_id"), 
                { "session_id": session_id }
            )
            new_conv = result_proxy.fetchone()
            self.db.commit()
            # Return the new conversation ID
            conv_id = new_conv[0]
        # Return the conversation ID
        return conv_id


    def create_transaction(self, pipeline_name):
        # Insert a new transaction into the transaction table
        result_proxy = self.db.execute(
            text("INSERT INTO transaction (conv_id, timestamp, pipeline_name) VALUES (:conv_id, NOW(), :pipeline_name) RETURNING tx_id"),
            {
                "conv_id": self.conv_id,
                "pipeline_name": pipeline_name
            }
        )
        new_tx = result_proxy.fetchone()
        self.db.commit()
        # Return the new transaction ID
        self.last_tx_id = new_tx[0]
        return new_tx[0]

    def save_input(self, tx_id, input_value):
        # Insert a new input transaction into the input_transaction table
        result_proxy = self.db.execute(
            text("INSERT INTO input_transaction (tx_id, input_value) VALUES (:tx_id, :input_value)"), 
            {
                "tx_id": tx_id,
                "input_value": input_value
            }
        )
        self.db.commit()

    def save_output(self, tx_id, output_value):
        # Insert a new output transaction into the output_transaction table
        result_proxy = self.db.execute(
            text("INSERT INTO output_transaction (tx_id, output_value) VALUES (:tx_id, :output_value)"), 
            {
                "tx_id": tx_id,
                "output_value": output_value
            }
        )
        self.db.commit()
