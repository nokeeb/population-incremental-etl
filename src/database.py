import psycopg2
import config

def get_connection(database_name):
    conn=psycopg2.connect(
        dbname=database_name,
        user=config.PG_USER,
        password=config.PG_PASSWORD,
        host=config.PG_HOST,
        port=config.PG_PORT
    )
    return conn