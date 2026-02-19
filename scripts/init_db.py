# initialising the database based on the schema.sql file

# sqlite3 documentation used https://docs.python.org/3/library/sqlite3.html
import sqlite3
# For managing file paths without hardcoding in paths specific to my computer, I will use the pathlib library.
# I followed https://coderivers.org/blog/file-path-python/ to learn how to use it.
from pathlib import Path

def init_db():
    dbPath = Path(__file__).parent.parent / 'data' / 'database.db'
    schemaPath = Path(__file__).parent.parent / 'data' / 'schema.sql'

    #reading the schema.sql file I used to define the structure of the database for the solution
    with open(schemaPath, 'r') as file:
        schema = file.read()

    connection = sqlite3.connect(dbPath) # creates a connection to the database which the tables are on

    # I used exception handling here because there may be errors in the schema.sql file
    try:
        cursor = connection.cursor() #database cursor is used to execute SQL statements and fetch results from SQL queries.
        cursor.executescript(schema) # executing the sql code I wrote in schema.sql
        connection.commit() # commits the actions executed to the database, so they are permanent now

        # for testing (refer to section 4):
        print("Database created successfully, test complete.")

    except sqlite3.Error as error:
        print(f"Error while creating the database: {error}")

    finally:
        connection.close() #closes the database connection

if __name__ == "__main__":
    init_db()
