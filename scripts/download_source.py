from pathlib import Path
PROJECT_ROOT=Path(__file__).resolve().parent.parent

import sys
sys.path.insert(0,str(PROJECT_ROOT))

from src import config
import requests
import csv

request_string=f'{config.SOURCE_CSV_URL}'

response=requests.get(request_string,timeout=30)

if response.raise_for_status():
    sys.exit(1)

response_content=response.text

with open(config.SOURCE_CSV_PATH,'w') as file:
    for line in response_content:
        file.write(line)

unexpected=False
total_rows=None

with open(config.SOURCE_CSV_PATH,'r') as file:
    parsed_csv=csv.DictReader(file)
    total_rows=len(list(parsed_csv))
    fieldnames=parsed_csv.fieldnames
    expected_fields=['Rank','State','Postal','Population']
    received_fields=list(fieldnames)

    for i in range(0,len(expected_fields)):
        if expected_fields[i] != received_fields[i]:
            print('Unexpected CSV header.')
            unexpected=True
    print('Expected:',", ".join(expected_fields))
    print('Received:',", ".join(received_fields))
        
    

if unexpected==True:
    sys.exit(1)
else:
    print('Successful CSV download.')
    print(f'Total rows: {total_rows}')
    sys.exit(0)   

