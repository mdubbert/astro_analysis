import boto3
import json
import logging
import os
import requests

from datetime import datetime
# from decimal import Decimal
from uuid import uuid4

logging.basicConfig(level=logging.INFO)

region = 'us-east-1'
stream_name = 'astro-stream'

# stream_name = os.environ['TARGET_STREAM']
# region = os.environ['AWS_REGION']

# JPL Small-Body Database
SBDB_QUERY_URL = 'https://ssd-api.jpl.nasa.gov/sbdb_query.api'
SBDB_QUERY_FIELDS = 'spkid,full_name,GM,kind,neo'
SBDB_QUERY_LIMIT = 5


def main():
    session = boto3.session.Session()
    kinesis_client = session.client('kinesis', region_name=region)

    records = get_source_data()
    formatted_records = format_payload(records)
    failed_count = send_to_kinesis(kinesis_client, formatted_records)

    if failed_count > 0:
        raise EnvironmentError(f'Failed to send {failed_count} records to stream')

    logging.info(f'Successfuly pushed {len(formatted_records)} records to stream')        


def get_source_data():
    logging.info('Requesting source data')
    query_params = {
        'fields': SBDB_QUERY_FIELDS,
        'limit': SBDB_QUERY_LIMIT
    }

    response = requests.get(SBDB_QUERY_URL, params=query_params)
    response.raise_for_status()
    return response.json()

def format_payload(records):
    formatted_records = []
    current_timestamp = datetime.now().isoformat()

    # TODO: dynamically assign field names

    for record in records['data']:
        spk_id, full_name, gravitational_mass, kind, neo = record

        trimmed = {
            'spk_id': spk_id,
            'full_name': full_name.strip(),
            # 'gravitational_mass': Decimal(gravitational_mass),
            'gravitational_mass': gravitational_mass,
            'kind': kind,
            'is_neo': to_boolean(neo),
            'processing_timestamp': current_timestamp
        }

        record_payload = {
            'Data': json.dumps(trimmed),
            'PartitionKey': str(uuid4())
        }

        formatted_records.append(record_payload)
    
    return formatted_records


def send_to_kinesis(client, record_list) -> int:
    response = client.put_records(
        Records=record_list,
        StreamName=stream_name
    )

    # TODO: better response checking / logging

    return response.get('FailedRecordCount', -1)

def to_boolean(input_str: str) -> bool:
    if input_str == 'Y':
        return True
    elif input_str == 'N':
        return False
    
    raise NotImplementedError('Unexpected input value')

if __name__ == "__main__":
    main()