import boto3
import sys

# create Glue client
glue = boto3.client('glue')

# define Glue job properties
job_name = 'my-glue-job'
s3_bucket = 'my-source-bucket'
s3_path = 'my-source-bucket/path/to/data/'
data_format = 'json'
output_bucket = 'my-output-bucket'
output_path = 'my-output-bucket/path/to/transformed/data/'
redshift_table_name = 'my-redshift-table'

# define schema for data
schema = [
    {"name": "user_id", "type": "int"},
    {"name": "app_version", "type": "string"},
    {"name": "device_type", "type": "string"},
    {"name": "event_name", "type": "string"},
    {"name": "event_properties", "type": "array", "items": {
        "name": "property", "type": "struct", "fields": [
            {"name": "key", "type": "string"},
            {"name": "value", "type": "string"}
        ]
    }}
]

# define transformation script
transformation_script = """
    from pyspark.sql.functions import from_json, col

    # read data from source
    df = spark.read.format('{}').load('{}', schema={})

    # transform data
    df = df.select(col('user_id'), col('app_version'), col('device_type'), col('event_name'), from_json(col('event_properties'), schema[4]['items']).alias('event_properties'))

    # write transformed data to output destination
    df.write.format('parquet').mode('overwrite').save('{}')
""".format(data_format, s3_path, schema, output_path)

# define job input/output parameters
input_param = {
    'Name': 'input_path',
    'Value': 's3://{}/{}'.format(s3_bucket, s3_path)
}
output_param = {
    'Name': 'output_path',
    'Value': 's3://{}/{}'.format(output_bucket, output_path)
}
redshift_param = {
    'Name': 'redshift_table_name',
    'Value': redshift_table_name
}

# create Glue job
response = glue.create_job(
    Name=job_name,
    Role='AWSGlueServiceRoleDefault',
    Command={
        'Name': 'glueetl',
        'ScriptLocation': 's3://aws-glue-scripts-{}/glueetl/examples/{}'.format(boto3.session.Session().region_name,
                                                                                'glue-job.py')
    },
    DefaultArguments={
        '--job-bookmark-option': 'job-bookmark-disable'
    },
    Connections={
        'Connections': [
            'my-redshift-connection'
        ]
    },
    MaxRetries=0,
    Timeout=2880,
    WorkerType='Standard',
    NumberOfWorkers=2
)

# start Glue job
glue.start_job_run(
    JobName=job_name,
    Arguments={
        '--{}': '{}'.format(input_param['Name'], input_param['Value']),
        '--{}': '{}'.format(output_param['Name'], output_param['Value']),
        '--{}': '{}'.format(redshift_param['Name'], redshift_param['Value'])
    }
)
