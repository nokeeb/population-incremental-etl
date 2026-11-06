import database, config
from datetime import timedelta

def extract_records(watermark_before):
    conn=None
    cur=None
    try:
        conn=database.get_connection(config.PG_DBNAME)
        cur=conn.cursor()
        if watermark_before is None:
                cur.execute("""SELECT area_code,area_name,population_raw,reference_year,updated_at 
                                FROM source.area_population
                                ORDER BY updated_at,area_code""")
        else:
        
            lower_bound=watermark_before-timedelta(hours=24)
            cur.execute("""SELECT area_code,area_name,population_raw,reference_year,updated_at 
                            FROM source.area_population
                            WHERE updated_at>=%s
                            ORDER BY updated_at,area_code""",(lower_bound,))
        source_records=cur.fetchall()
        batch_upper_bound=watermark_before
        for record in source_records:
            if batch_upper_bound is None or batch_upper_bound<record[4]:
                batch_upper_bound=record[4]
        

            
        return source_records,batch_upper_bound


    
    finally:
        if cur:    
            cur.close()
        if conn:            
            conn.close()

