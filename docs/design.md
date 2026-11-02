# Design notes

## Source data

The initial dataset is the public `2014_usa_states.csv` file 
from the Plotly datasets repository.

Source URL:
https://raw.githubusercontent.com/plotly/datasets/master/2014_usa_states.csv

The CSV contains the following columns:

- Rank
- State
- Postal
- Description
  
The dataset contains 52 areas, including the District of Columbia
and Puerto Rico. For this reason, the projects uses the term 
"areas" rather than referring to all records as US states.

Population values in the original dataset refer to 2014.

## Local source file 

The download script saves the CSV to:

data/source/2014_usa_states.csv

This file is used to initialize the PostgreSQL source table.
The running pipeline will read from that source table, not 
download the CSV on every execution.

## Real data versus simulated changes 

The original CSV provides the initial area names, codes,
and population values.

The CSV does not provide an `updated_at` column.
The project introduces simulated source timestamps to demonstrate
incremental loading.

Later test records will introduce new source records and 
modify selected population values. These modifications are
controlled test data, not real demographic updates.

## Initial load and later scenarios

The initial source seed will use records with Rank <= 50.

The remaining two records will be introduced in a later test
to demonstrate loading new records.

Other scenarios will demonstrate updates, late-arriving changes,
invalid records, and recovery after a failed run.

## Database model
![alt text](image.png)

**Database:** population_incremental

## **Schemas:**
### - source (source system)
##### **Table(s):**

**area_population**:
- area_code
- area_name
- population_raw
- reference_year
- updated_at
 
**Grain** : 1 row represents 1 raw state of an area.

### - etl (represents pipeline info)
##### **Table(s):**
**pipeline_runs**:
- run_id
- started_at
- finished_at
- status
- watermark_before
- watermark_after
- extracted_count
- valid_count
- invalid_count
- inserted_count
- updated_count
- unchanged_count
- error_message

**Grain:** 1 row represents 1 pipeline run in 1 period of time.

**pipeline_state:**
- pipeline_name
- last_watermark 

**Grain:**: 1 row represents one pipeline, saving its last sucessful watermark.
### - staging (final station before cleaning and loading the data)
##### **Table(s):**
**area_population**:
- run_id
- area_code
- area_name
- population
- reference_year
- source_updated_at 

**Grain:** one row represents one last state of an area before ETL.


### - analytics (target system, cleaned and loaded data)
##### Tables(s):
**area_population**
- area_code
- area_name 
- population
- reference_year
- source_updated_at
- loaded_at
- last_run_id 

**Grain:** one row represents the last successful processed version of an area

## Relationships

`analytics.area_population` **1 : N** `etl.pipeline_runs` 

(1 pipeline run can contain several areas)