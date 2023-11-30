
CREATE TABLE conversation (
  conv_id SERIAL PRIMARY KEY,
  session_id INT NOT NULL,
  token VARCHAR(255) NOT NULL,
  UNIQUE (session_id, token)
);

CREATE TABLE transaction (
  tx_id SERIAL NOT NULL,
  conv_id INT NOT NULL,
  timestamp TIMESTAMP NOT NULL,
  sequence INT NOT NULL DEFAULT 0,
  pipeline_name VARCHAR(50) NOT NULL,
  PRIMARY KEY (tx_id),
  UNIQUE (conv_id, sequence),
  FOREIGN KEY (conv_id) REFERENCES conversation(conv_id)
);

CREATE FUNCTION update_transaction_sequence() RETURNS TRIGGER AS $$
DECLARE max_sequence INT;
BEGIN
  SELECT COALESCE(MAX(sequence), 0) INTO max_sequence
  FROM transaction
  WHERE conv_id = NEW.conv_id;
  NEW.sequence = max_sequence + 1;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_transaction
BEFORE INSERT ON transaction
FOR EACH ROW
EXECUTE FUNCTION update_transaction_sequence();

CREATE TABLE input_transaction (
  id_input SERIAL NOT NULL,
  tx_id INT NOT NULL,
  input_value TEXT NOT NULL,
  PRIMARY KEY (id_input),
  FOREIGN KEY (tx_id) REFERENCES transaction(tx_id),
  UNIQUE (tx_id)
);

CREATE TABLE output_transaction (
  id_output SERIAL NOT NULL,
  tx_id INT NOT NULL,
  output_value TEXT NOT NULL,
  PRIMARY KEY (id_output),
  FOREIGN KEY (tx_id) REFERENCES transaction(tx_id),
  UNIQUE (tx_id)
);

CREATE TABLE transaction_chain (
  txc_id SERIAL NOT NULL,
  tx_id INT NOT NULL,
  timestamp TIMESTAMP NOT NULL,
  sequence INT NOT NULL DEFAULT 0,
  agent_name VARCHAR(50) NOT NULL,
  PRIMARY KEY (txc_id),
  UNIQUE (tx_id, sequence),
  FOREIGN KEY (tx_id) REFERENCES transaction(tx_id)
);

CREATE FUNCTION update_transaction_chain_sequence() RETURNS TRIGGER AS $$
DECLARE max_sequence INT;
BEGIN
  SELECT COALESCE(MAX(sequence), 0) INTO max_sequence
  FROM transaction_chain
  WHERE tx_id = NEW.tx_id;
  NEW.sequence = max_sequence + 1;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_transaction_chain
BEFORE INSERT ON transaction_chain
FOR EACH ROW
EXECUTE FUNCTION update_transaction_chain_sequence();

CREATE TABLE input_transaction_chain (
  id_input SERIAL NOT NULL,
  txc_id INT NOT NULL,
  input_value TEXT NOT NULL,
  PRIMARY KEY (id_input),
  FOREIGN KEY (txc_id) REFERENCES transaction_chain(txc_id),
  UNIQUE (txc_id)
);

CREATE TABLE output_transaction_chain (
  id_output SERIAL NOT NULL,
  txc_id INT NOT NULL,
  output_value TEXT NOT NULL,
  PRIMARY KEY (id_output),
  FOREIGN KEY (txc_id) REFERENCES transaction_chain(txc_id),
  UNIQUE (txc_id)
);
