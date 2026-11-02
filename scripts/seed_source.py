import psycopg2
import sys
from pathlib import Path
PROJECT_ROOT=Path(__file__).resolve().parent.parent
import csv
sys.path.insert(0,str(PROJECT_ROOT))
from src import database,config
import datetime
from datetime import timezone
content=None

with open(PROJECT_ROOT/'data'/'source'/'2014_usa_states.csv','r') as file:
    parsed_file=csv.DictReader(file)
    print(parsed_file)
    try:
        conn=database.get_connection(config.PG_DBNAME)
        cur=conn.cursor()
    except Exception as e:
        print(f'Error occurred:{e}')
        sys.exit(1)
    for line in parsed_file:
        if int(line['Rank'])<=50:
            cur.execute(("""INSERT INTO source.area_population(area_code,area_name,population_raw,reference_year,updated_at)
            VALUES(%s,%s,%s,%s,%s) ON CONFLICT(area_code) DO NOTHING"""),[line['Postal'],line['State'],line['Population'],2014,datetime.datetime.now(tz=timezone.utc)])
            
    conn.commit()
    sys.exit(0)

