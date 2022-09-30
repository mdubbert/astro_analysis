import boto3
import json
import logging
# import os
import random
import requests

from datetime import datetime
from uuid import uuid4

logging.basicConfig(level=logging.INFO)

region = 'us-east-1'
stream_name = 'astro-stream'

# stream_name = os.environ['TARGET_STREAM']
# region = os.environ['AWS_REGION']

# JPL Small-Body Database
SBDB_QUERY_URL = 'https://ssd-api.jpl.nasa.gov/sbdb_query.api'
SBDB_QUERY_FIELDS = 'spkid,full_name,GM,kind,neo,pha'
SBDB_RECORDS_PER_QUERY = 500
SBDB_BATCHES_PER_RUN = 8

STRING_TO_BOOLEAN_MAP = {
    'Y': True,
    'N': False
}

def main():
    session = boto3.session.Session()
    kinesis_client = session.client('kinesis', region_name=region)

    batch_count = 0
    starting_record_position = random.randrange(0, 125000, 1) 

    while batch_count < SBDB_BATCHES_PER_RUN:
        records = get_source_data(starting_record_position)
        formatted_records = format_payload(records)
        send_to_kinesis(kinesis_client, formatted_records)
        batch_count += 1
        starting_record_position += SBDB_RECORDS_PER_QUERY


def get_source_data(starting_position=0) -> dict:
    logging.info(f'Requesting source data: {starting_position}-{starting_position + SBDB_RECORDS_PER_QUERY}')
    query_params = {
        'fields': SBDB_QUERY_FIELDS,
        'limit': SBDB_RECORDS_PER_QUERY,
        'limit-from': starting_position,
        'sb-kind': 'a'                     # asteroids
        # 'sb-group': 'pha'                # potentially hazardous asteroids. seems sparse.
    }

    response = requests.get(SBDB_QUERY_URL, params=query_params)
    response.raise_for_status()
    return response.json()

def format_payload(records) -> list:
    formatted_records = []
    current_timestamp = datetime.now().isoformat()

    # TODO: dynamically assign field names

    for record in records['data']:
        spk_id, full_name, gravitational_mass, kind, neo, pha = record

        trimmed = {
            'spk_id': spk_id,
            'full_name': full_name.strip(),
            'gravitational_mass': gravitational_mass,
            'kind': kind,
            'is_neo': to_boolean(neo),
            'is_pha': to_boolean(pha),
            'processing_timestamp': current_timestamp
        }

        record_payload = {
            'Data': json.dumps(trimmed),
            'PartitionKey': str(uuid4())
        }

        formatted_records.append(record_payload)
    
    return formatted_records


def send_to_kinesis(client, record_list) -> int:
    if len(record_list) == 0:
        logging.warning('No records to send')
        return

    response = client.put_records(
        Records=record_list,
        StreamName=stream_name
    )

    # TODO: better response checking / logging
    failed_count = response.get('FailedRecordCount', -1)

    if failed_count > 0:
        raise EnvironmentError(f'Failed to send {failed_count} records to stream')

    logging.info(f'Successfully pushed {len(record_list)} records to stream')  

def to_boolean(input_str: str) -> bool:
    try:
        return STRING_TO_BOOLEAN_MAP[input_str]
    except KeyError:
        raise NotImplementedError(f'Unexpected input value. Expecting one of {STRING_TO_BOOLEAN_MAP.keys()}')

if __name__ == "__main__":
    main()