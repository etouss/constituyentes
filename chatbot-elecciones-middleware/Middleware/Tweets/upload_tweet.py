import csv
import psycopg2 # Or any other Python database library that you are using
# Connect to the database
conn = psycopg2.connect(
    host="db-postgresql-nyc1-26343-do-user-9263663-0.b.db.ondigitalocean.com",
    port="25060",
    database="elections",
    user="jreutter",
    password="AVNS_UM4p-njPfaQ6q823wvN"
)
# Open the CSV file and read its contents
with open('data.csv', 'r') as csvfile:
    reader = csv.reader(csvfile, delimiter=';')
    # Skip the header row
    next(reader)
    # Construct the SQL statement
    sql = "INSERT INTO mytable (name, age, email) VALUES (%s, %s, %s)"
    # Loop over the remaining rows
    for row in reader:
        # Insert the data into the database
        cursor = conn.cursor()
        cursor.execute(sql, row)
        conn.commit()
        cursor.close()

# Close the database connection
conn.close()
