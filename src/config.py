from pathlib import Path
from dotenv import load_dotenv
import os

PROJECT_ROOT=Path(__file__).resolve().parent.parent

SOURCE_CSV_PATH=PROJECT_ROOT/"data"/"source"/"2014_usa_states.csv"

PIPELINE_LOG_PATH=PROJECT_ROOT/"logs"/"pipeline.log"

load_dotenv(PROJECT_ROOT/".env")

PG_HOST=os.getenv('PG_HOST','localhost')
PG_PORT=os.getenv('PG_PORT','5432')
PG_ADMIN_DB=os.getenv('PG_ADMIN_DB','postgres')
PG_DBNAME=os.getenv('PG_DBNAME','population_incremental')
PG_USER=os.getenv('PG_USER','postgres')
PG_PASSWORD=os.getenv('PG_PASSWORD','replace_me')

SOURCE_CSV_URL=os.getenv('SOURCE_CSV_URL')
ETL_TEST_FAIL_BEFORE_COMMIT=(os.getenv('ETL_TEST_FAIL_BEFORE_COMMIT','0')=="1")
