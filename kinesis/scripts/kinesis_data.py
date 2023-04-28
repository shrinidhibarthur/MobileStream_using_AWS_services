import boto3
import pyarrow as pa
import pyarrow.parquet as pq
import json

# Set up boto3 Kinesis client
kinesis = boto3.client('kinesis', region_name='ap-south-1')

# Set up Parquet schema for event properties
event_properties_schema = pa.schema([
    pa.field('key', pa.string()),
    pa.field('value', pa.string())
])

# Set up Parquet schema
schema = pa.schema([
    pa.field('user_id', pa.int32()),
    pa.field('app_version', pa.string()),
    pa.field('device_type', pa.string()),
    pa.field('event_name', pa.string()),
    pa.field('event_properties', pa.list_(pa.struct(event_properties_schema)))
])

# Read data from Parquet file
table = pq.read_table('mobile_app_data.parquet')
records = []
for i in range(table.num_rows):
    record = {}
    for field_name in schema.names:
        record[field_name] = str(table[field_name][i].as_py())
    records.append(record)

# Send records to Kinesis stream
for record in records:
    response = kinesis.put_record(
        StreamName='my-stream',
        Data=str(record),
        PartitionKey=str(record['user_id'])
    )
    print(response)

