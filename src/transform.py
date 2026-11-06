from decimal import Decimal,InvalidOperation
from datetime import datetime
def transform_records(source_records):
        validated_records=list()
        error_messages=list()
        source_codes=dict()


        for record in source_records:
            area_code=record[0]
            original_area_code=area_code
            area_name=record[1]
            if area_code is None:
                error_messages.append("area_code is None;")
                continue

            area_code=area_code.strip()
            area_code=area_code.upper()
            if len(area_code)!=2 or area_code.isalpha()==False or area_code.isascii()==False:
                error_messages.append(f"code={area_code}: area_code must contain exactly two letters A-Z;")
                continue

            if source_codes.get(area_code) is None:
                source_codes[area_code]=original_area_code
            else:
                if source_codes.get(area_code)!=original_area_code:
                    error_messages.append(f"code={area_code}: source keys '{source_codes.get(area_code)}' and '{original_area_code}' become the same after standardization.")
                    continue

            
            
            if area_name is None:
                error_messages.append(f"code={area_code}: area_name is NULL;")
                continue
            
            area_name=area_name.strip()
            if area_name=='':
                error_messages.append(f"code={area_code}: area_name is an empty string;")
                continue

            population_raw=record[2]

            if population_raw is None:
                error_messages.append(f"code={area_code}: population is NULL;")
                continue

            

            population_raw=population_raw.strip()
            if population_raw=="":
                error_messages.append(f"code={area_code}: population is empty;")
                continue


            try:
                population_decimal=Decimal(population_raw)

            except InvalidOperation:
                error_messages.append(f"code={area_code}: population is not a valid number")
                continue
            


            if population_decimal.is_finite()==False:
                error_messages.append(f"code={area_code}: population is not a finite number;")
                continue

            if population_decimal<0:
                error_messages.append(f"code={area_code}: population is less than 0;")
                continue

            if population_decimal!=population_decimal.to_integral_value():
                error_messages.append(f"code={area_code}: population is not a whole number")
                continue
            
            population=int(population_decimal)    

            reference_year=record[3]
            if reference_year!=2014:
                error_messages.append(f"code={area_code}: reference year is not 2014;")
                continue

            updated_at=record[4]

            if isinstance(updated_at,datetime)==False:
                error_messages.append(f"code={area_code}: updated_at is not a datetime;")
                continue

            if updated_at.utcoffset()==None:
                error_messages.append(f"code={area_code}:updated_at does not have timezone information;")
                continue

            new_record=(area_code,area_name,population,reference_year,updated_at)

            validated_records.append(new_record)

        return validated_records,error_messages


