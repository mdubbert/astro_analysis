%flink.ssql(type=update)

CREATE TABLE sbdb_table (
                spk_id VARCHAR(18),
                full_name VARCHAR(96),
                gravitational_mass DOUBLE,
                kind VARCHAR(2),
                is_neo BOOLEAN,
                processing_timestamp TIMESTAMP(3),
                WATERMARK FOR processing_timestamp AS processing_timestamp - INTERVAL '5' SECOND

              )
              PARTITIONED BY (spk_id)
              WITH (
                'connector' = 'kinesis',
                'stream' = 'astro-stream',
                'aws.region' = 'us-east-1',
                'scan.stream.initpos' = 'LATEST',
                'format' = 'json',
                'json.timestamp-format.standard' = 'ISO-8601'
              )