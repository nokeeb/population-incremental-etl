from pathlib import Path
import sys
import psycopg2
PROJECT_ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(PROJECT_ROOT))
from src import database,config,extract,transform,load
from uuid import uuid4
from datetime import datetime,timezone,timedelta
import logging
def main():
    
    run_id=uuid4()
    (PROJECT_ROOT/'logs').mkdir(parents=True,exist_ok=True)
    logging.basicConfig(filename=PROJECT_ROOT/'logs'/'pipeline.log',level=logging.INFO,encoding='utf-8',format='%(asctime)s %(levelname)s %(message)s')

    target_conn=None
    target_cur=None
    watermark_before=None
    extracted_count=0
    transformed_count=0
    invalid_count=0
    changes_classified={'inserted':0,'updated':0,'unchanged':0}
    audit_created=False
    logging.info(f"run_id:{run_id} -> event=RUN_STARTED")
    try:
        target_conn=database.get_connection(config.PG_DBNAME)
        target_cur=target_conn.cursor()

        target_cur.execute("""SELECT last_watermark FROM etl.pipeline_state
                              WHERE pipeline_name=%s
        """,(config.PG_DBNAME,)) 

        pipeline_state=target_cur.fetchone()
        if pipeline_state is None:
            raise ValueError(f"The state row for this pipeline ({config.PG_DBNAME}) doesn't exist")
        
        watermark_before=pipeline_state[0]
        if watermark_before is None:
            logging.info(f"run_id:{run_id} -> event=FULL_LOAD (no watermark_before))")
        else:
            logging.info(f"run_id:{run_id} -> event=RECEIVED_LAST_WATERMARK | watermark_before: {watermark_before})")
            logging.info(f"run_id:{run_id} -> event=CALCULATED_LOOCKBACK | lookback bound: {(watermark_before-timedelta(hours=24))}")

        target_cur.execute("""INSERT INTO etl.pipeline_runs(run_id,started_at,status,watermark_before) VALUES (%s,%s,%s,%s)""",
(str(run_id),datetime.now(timezone.utc),'RUNNING',watermark_before))
        
        target_conn.commit()
        logging.info(f"run_id:{run_id} -> event=RUNNING_AUDIT_COMMITTED")
        audit_created=True
        extracted,upper_bound=extract.extract_records(watermark_before)
        extracted_count=len(extracted)

        transformed,transform_errors=transform.transform_records(extracted)
        transformed_count=len(transformed)

        invalid_count=extracted_count-transformed_count
        logging.info(f"run_id:{run_id} -> event=TRANSFORMED | extracted_count:{extracted_count}, transformed_count:{transformed_count}, invalid_count:{invalid_count}")

        if len(transform_errors)>0:
            raise ValueError(transform_errors)


        inserted_staging_rows=load.stage_records(target_conn,run_id,transformed)
        changes_classified=load.classify_changes(target_conn,run_id)

        logging.info(f"run_id:{run_id} -> event=CLASSIFIED | planned_inserted={changes_classified['inserted']}, planned_updated={changes_classified['updated']}, planned_unchanged={changes_classified['unchanged']}"
        )

        total_rows=0
        for key,value in changes_classified.items():
            total_rows+=value

        if inserted_staging_rows!=transformed_count or total_rows!= transformed_count:
            raise ValueError(f"Reconciliation failed: valid={transformed_count}, staged={inserted_staging_rows}, classified={total_rows} ")



        load.upsert_records(target_conn,run_id)

        load.validate_loaded_records(target_conn,run_id)

        if config.ETL_TEST_FAIL_BEFORE_COMMIT is True:
            logging.warning(f"run_id:{run_id} -> EVENT=INTENTIONAL_FAIL")
            raise RuntimeError("Intentional failure before commit")

        logging.info(f"run_id:{run_id} -> event=SUCCESSFUL_VALIDATION | planned watermark_after:{upper_bound}")



        target_cur.execute("""UPDATE etl.pipeline_state
                                SET last_watermark=%s
                                WHERE pipeline_name=%s""",(upper_bound,config.PG_DBNAME))
        if target_cur.rowcount!=1:
            raise Exception(f"State update failed: expected 1 affected row, got {target_cur.rowcount}")
        
        record_to_insert=(datetime.now(timezone.utc),'SUCCESS',upper_bound,extracted_count,transformed_count,invalid_count,changes_classified['inserted'],changes_classified['updated'],changes_classified['unchanged'],str(run_id))
        target_cur.execute("""UPDATE etl.pipeline_runs SET
                                    finished_at=%s,
                                    status=%s,
                                    watermark_after=%s,
                                    extracted_count=%s,
                                    valid_count=%s,
                                    invalid_count=%s,
                                    inserted_count=%s,
                                    updated_count=%s,
                                    unchanged_count=%s
                                    WHERE run_id=%s""",record_to_insert)
        if target_cur.rowcount!=1:
            raise Exception(f"Audit row update failed: expected 1 affected row, got {target_cur.rowcount}")
        target_conn.commit()
        logging.info(f"run_id:{run_id} -> event=LOAD_COMMITED | final status: {record_to_insert[1]}")
        
        return 0

    except Exception as e:
        logging.exception(f"run_id:{run_id}")
        try:
            if target_conn:
                target_conn.rollback()
                logging.info(f"run_id:{run_id} -> event=LOAD_ROLLED_BACK")
            if audit_created==True:
                record_to_insert=(datetime.now(timezone.utc),'FAILED',extracted_count,transformed_count,invalid_count,0,0,0,f"{e}",str(run_id))
                target_cur.execute("""UPDATE etl.pipeline_runs SET
                                            finished_at=%s,
                                            status=%s,
                                            watermark_after=watermark_before,
                                            extracted_count=%s,
                                            valid_count=%s,
                                            invalid_count=%s,
                                            inserted_count=%s,
                                            updated_count=%s,
                                            unchanged_count=%s,
                                            error_message=%s
                                            WHERE run_id=%s""",record_to_insert)     
                if target_cur.rowcount!=1:
                    raise Exception(f"Audit row update failed: expected 1 affected row, got {target_cur.rowcount} ")
                target_conn.commit()
                logging.info(f"run_id:{run_id} -> event=FAILED_AUDIT_COMMITED")
        except Exception as e:
            logging.exception(f"run_id:{run_id}")
        logging.info(f"run_id:{run_id} -> event=EXIT_CODE_1 | final status: 'FAILED'")
        return 1


    
    finally:
        try:
            if target_cur:
                target_cur.close()
        except Exception as e:
            logging.exception(f"run_id:{run_id}")
        try:
            if target_conn:
                target_conn.close()
        except Exception as e:
            logging.exception(f"run_id:{run_id}")
        logging.info("-------------------------------------------------------\n")