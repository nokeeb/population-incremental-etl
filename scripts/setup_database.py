from pathlib import Path
PROJECT_ROOT=Path(__file__).resolve().parent.parent
import sys
sys.path.insert(0,str(PROJECT_ROOT))
from src import database,config
from datetime import datetime,timezone
import logging

def main():
    logging.basicConfig(filename=PROJECT_ROOT/'logs'/'setup_database.log')
    admin_conn=None
    admin_cur=None
    conn=None
    cur=None
    try:
        admin_conn=database.get_connection('postgres')
        admin_conn.autocommit=True
    except Exception as e:
        logging.error(f"Date: {datetime.now(tz=timezone.utc).replace(microsecond=0)} -> Database error occured. Error: {e}")
        sys.exit(1)
    admin_cur=admin_conn.cursor()
    try:
        admin_cur.execute(f"""SELECT 1 FROM pg_catalog.pg_database WHERE datname='{config.PG_DBNAME}'""")

        exists=admin_cur.fetchone()
        if not exists:
            admin_cur.execute(f"""CREATE DATABASE {config.PG_DBNAME}""")
    except Exception:
        logging.error(f"""Date: {datetime.now(timezone.utc).replace(microsecond=0)} -> Cannot create database {config.PG_DBNAME}.
        PostgreSQL user '{config.PG_USER}' does not have permission to create databases.
        Use an account with CREATEDB permission or ask the database administrator 
        to create the database""")
        sys.exit(1)
    finally:
        admin_cur.close()
        admin_conn.close()  
    conn=database.get_connection(f'{config.PG_DBNAME}')
    cur=conn.cursor()
    script=None
    with open(PROJECT_ROOT/'sql'/'001_schema.sql','r') as file:
        script=file.read()
        try:
            cur.execute(script)
            conn.commit()
        except Exception as e:
            logging.error(f"Date:{datetime.now(tz=timezone.utc).replace(microsecond=0)} -> Error occured: {e}")
        finally:
            cur.close()
            conn.close()
    sys.exit(0)

if __name__=='__main__':
    main()