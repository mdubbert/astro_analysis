%flink.ssql(type=update)

SELECT
    kind,
    SUM(gravitational_mass) AS total_mass
FROM sbdb_table
WHERE gravitational_mass IS NOT NULL
GROUP BY TUMBLE(processing_timestamp, INTERVAL '10' second), kind;