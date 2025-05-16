from psycopg2 import Error
import os
import psycopg2 as pg
from dotenv import load_dotenv

load_dotenv()

def create_connection():
    try:
        conn = pg.connect(
            host=os.getenv('DB_HOST'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD')
        )
        print("Connected to PostgreSQL database")
        return conn

    except Error as e:
        print(f"Error : {e}")
        return None

def create_table():
    try:
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("""CREATE TABLE IF NOT EXISTS raw_articles (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255),
    description TEXT,
    publishedAt TIMESTAMP
);
""")
        print("Table created successfully")
        conn.commit()
        print("Successfully created table")
        conn.close()
    except Error as e:
        print(f"Error: {e}")
