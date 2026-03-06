import psycopg2
import json, time
import statistics


with open('config.json') as f:
    config = json.load(f)
    PG_HOST = config['postgres']['host']
    PG_DB = config['postgres']['db']
    PG_USER = config['postgres']['username']
    PG_PASSWORD = config['postgres']['password']

QUERY = '''
SELECT
driver_id,
ST_Distance(
    location,
    ST_SetSRID(ST_MakePoint(%s, %s),4326)::geography
) AS distance_meters
FROM drivers
WHERE
vehicle_type = 'xl'
AND boot_space = true
AND geo_region_id = 3
AND is_online = true
ORDER BY distance_meters
LIMIT 10;
'''

lon, lat, ITERATIONS = 77.616226, 12.906066, 200


def main():

    conn = psycopg2.connect(
        host=PG_HOST,
        dbname=PG_DB,
        user=PG_USER,
        password=PG_PASSWORD,
        sslmode='require'
    )

    cur = conn.cursor()

    latencies = []

    print('Running benchmark...')

    for i in range(ITERATIONS):

        start = time.perf_counter()

        cur.execute(QUERY, (lon, lat))
        cur.fetchall()

        end = time.perf_counter()

        latency_ms = (end - start) * 1000
        latencies.append(latency_ms)

    latencies.sort()

    p50 = statistics.median(latencies)
    p95 = latencies[int(0.95 * ITERATIONS)]
    p99 = latencies[int(0.99 * ITERATIONS) - 1]

    print('\nBenchmark Results')
    print('-----------------')
    print(f'Queries run : {ITERATIONS}')
    print(f'P50 latency : {p50:.2f} ms')
    print(f'P95 latency : {p95:.2f} ms')
    print(f'P99 latency : {p99:.2f} ms')
    print(f'Max latency : {max(latencies):.2f} ms')


if __name__ == '__main__':
    main()
