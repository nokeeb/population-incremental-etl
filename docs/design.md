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