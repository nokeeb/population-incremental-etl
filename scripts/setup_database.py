from pathlib import Path
PROJECT_ROOT=Path(__file__).resolve().parent.parent
import sys
sys.path.insert(0,str(PROJECT_ROOT))
from src import database,config

def main():
    admin_conn=None
    admin_cur=None
    conn=None
    cur=None
    try:
        admin_conn=database.get_connection('postgres')
        admin_conn.autocommit=True
    except Exception as e:
        print(f"Error occured: {e}")
        sys.exit(1)

    admin_cur=admin_conn.cursor()
    try:
        admin_cur.execute(f"""SELECT 1 FROM pg_catalog.pg_database WHERE datname='{config.PG_DBNAME}'""")

        exists=admin_cur.fetchone()
        if not exists:
            admin_cur.execute(f"""CREATE DATABASE {config.PG_DBNAME}""")
    except Exception as e:
        print(f'Error occurred:{e}')
        print(f"""Cannot create database {config.PG_DBNAME}.
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
            print(f"Error occured: {e}")
            conn.rollback()
            sys.exit(1)
        finally:
            cur.close()
            conn.close()
    sys.exit(0)

if __name__=='__main__':
    main()