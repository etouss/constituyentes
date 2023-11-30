import psycopg2

# Connect to the PostgreSQL database
conn = psycopg2.connect(
    host="db-postgresql-nyc1-26343-do-user-9263663-0.b.db.ondigitalocean.com",
    port="25060",
    database="chatdata",
    user="chatdata",
    password="AVNS_AHdFDceQspT81IXGQ0w"
)

# Open the schema file and read the SQL commands
with open("sql_schema.sql", "r") as f:
    sql = f.read()

# Execute the SQL commands to create the tables
with conn.cursor() as cur:
    cur.execute(sql)
    conn.commit()

# Close the database connection
conn.close()
