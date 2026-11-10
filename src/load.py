def stage_records(conn,run_id,validated_records):
    inserted_rows=0
    cur=conn.cursor()
    try:
        for record in validated_records:
            record_to_insert=(run_id,record[0],record[1],record[2],record[3],record[4])
            cur.execute("""INSERT INTO staging.area_population(run_id,area_code,area_name,population,reference_year,source_updated_at)
                            VALUES(%s,%s,%s,%s,%s,%s)""",record_to_insert)
            inserted_rows=inserted_rows+1
        return inserted_rows
    finally:
        cur.close()




def classify_changes(conn,run_id):
    cur=conn.cursor()

    try: 
        cur.execute("""SELECT
        sap.area_code,
        sap.area_name AS source_name,
        aap.area_name AS target_name,
        sap.population AS source_population,
        aap.population AS target_population,
        sap.reference_year AS source_refyear,
        aap.reference_year AS target_refyear
        FROM
        STAGING.AREA_POPULATION AS SAP
        JOIN ANALYTICS.AREA_POPULATION AS AAP ON SAP.AREA_CODE = AAP.AREA_CODE
        WHERE sap.run_id=%s AND
        sap.source_updated_at=aap.source_updated_at
        AND 
        (sap.area_name IS DISTINCT FROM aap.area_name
        OR sap.population IS DISTINCT FROM aap.population
        OR sap.reference_year IS DISTINCT FROM aap.reference_year
        )""",(str(run_id),))
        
        if cur.rowcount>0:
            rows=cur.fetchall()
            error_messages=list()
            for row in rows:
                error_messages.append(f"area_code={row[0]}: some business fields with same updated_at are different")
            raise ValueError(','.join(error_messages))

        else:
            cur.execute("""WITH
                            CHANGE_TYPES AS (
                                SELECT
                                    SAP.AREA_CODE AS CODES,
                                    CASE
                                        WHEN AAP.AREA_CODE IS NULL THEN 'inserted'
                                        WHEN SAP.SOURCE_UPDATED_AT > AAP.SOURCE_UPDATED_AT THEN 'updated'
                                        ELSE 'unchanged'
                                    END AS CHANGE_TYPE
                                FROM
                                    STAGING.AREA_POPULATION AS SAP
                                    LEFT JOIN ANALYTICS.AREA_POPULATION AS AAP ON SAP.AREA_CODE = AAP.AREA_CODE
                                    WHERE sap.run_id=%s
                            )
                            SELECT
                            CHANGE_TYPE,
                            COUNT(CHANGE_TYPE)
                            FROM
                            CHANGE_TYPES
                            GROUP BY
                            CHANGE_TYPE;""",(str(run_id),))
            change_types=cur.fetchall()

            counters=dict()
            counters['inserted']=0
            counters['updated']=0
            counters['unchanged']=0
            for record in change_types:
                counters[record[0]]=record[1]
            return counters
    finally:
        cur.close()

def upsert_records(conn,run_id):
    cur=conn.cursor()
    try:
        cur.execute("""INSERT INTO analytics.area_population AS target(area_code,area_name,population,reference_year,source_updated_at,loaded_at,last_run_id)
                        SELECT area_code,area_name,population,reference_year,source_updated_at,NOW(),run_id
                        FROM staging.area_population
                        WHERE run_id=%s
                        ON CONFLICT(area_code)
                        DO UPDATE SET
                        area_name=EXCLUDED.area_name,
                        population=EXCLUDED.population,
                        reference_year=EXCLUDED.reference_year,
                        source_updated_at=EXCLUDED.source_updated_at,
                        loaded_at=NOW(),
                        last_run_id=EXCLUDED.last_run_id
                        WHERE target.source_updated_at<EXCLUDED.source_updated_at
                        """,(str(run_id),))
    finally:
        cur.close()
    

def validate_loaded_records(conn,run_id):
    cur=conn.cursor()
    try:
        cur.execute("""SELECT sap.area_code,aap.area_code,sap.source_updated_at,aap.source_updated_at,sap.area_name,aap.area_name,sap.population,aap.population,sap.reference_year,aap.reference_year
                        FROM staging.area_population AS sap
                        LEFT JOIN analytics.area_population AS aap
                        ON sap.area_code=aap.area_code
                        WHERE sap.run_id=%s
                        """,(str(run_id),))
        rows=cur.fetchall()
        error_messages=list()
        for row in rows:
            if row[1] is None:
                error_messages.append(f"code:{row[0]}: staging row was not inserted into target;")
                continue
            if row[2]>row[3]:
                error_messages.append(f"code:{row[0]}: newer source version was not applied;")
            if row[2]==row[3] and (row[4]!=row[5] or row[6]!=row[7] or row[8]!=row[9]):
                error_messages.append(f"code:{row[0]}: target does not match the source version")
        if len(error_messages)>0:
            raise ValueError(','.join(error_messages))
    finally:
        cur.close()
