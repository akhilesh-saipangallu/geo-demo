import json
import random
import time
import math
import redis
from redis.commands.json.path import Path


with open('config.json') as f:
    config = json.load(f)
    REDIS_HOST = config['redis']['host']
    REDIS_PORT = config['redis']['port']
    REDIS_USERNAME = config['redis']['username']
    REDIS_PASSWORD = config['redis']['password']

    PG_HOST = config['postgres']['host']
    PG_DB = config['postgres']['db']
    PG_USER = config['postgres']['username']
    PG_PASSWORD = config['postgres']['password']

TOTAL_DOCS = 250_000

r = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    username='default',
    password=REDIS_PASSWORD,
)


def generate_cell_id(lat, lon):
    # 1 km in degrees
    cell_size_lat = 1 / 111.0  # ≈ 0.009009°
    cell_size_lon = 1 / (111.0 * math.cos(math.radians(lat)))

    cell_x = math.floor(lat / cell_size_lat)
    cell_y = math.floor(lon / cell_size_lon)

    return f'cell_{cell_x}_{cell_y}'


def make_driver_doc(i: int):
    # simple deterministic-ish values
    driver_id = 100000 + i
    vehicle_id = 1000 + (i % 1000)

    # random-ish location around a base point (e.g., Bangalore coords)
    base_lon, base_lat = 77.641100, 12.914100
    lon = base_lon + random.uniform(-0.05, 0.05)
    lat = base_lat + random.uniform(-0.05, 0.05)
    location_str = f'{lon:.6f},{lat:.6f}'

    doc = {
        'driver_id': str(driver_id),
        'vehicle_id': vehicle_id,
        'geo_region_id': str(random.choice([1, 2, 3, 4, 5, 6])),
        'is_online': bool(random.getrandbits(1)),
        'driver_rating': round(random.uniform(1.0, 5.0), 1),
        'location': location_str,
        'vehicle': {
            'type': random.choice(['bike', 'auto', 'hatchback', 'sedan', 'business', 'xl', 'xl+', 'black']),
            'boot_space': bool(random.getrandbits(1)),
        },
        'cell_id': generate_cell_id(lat, lon),
    }

    return doc, lon, lat


def main():
    # quick ping check
    try:
        r.ping()
    except redis.exceptions.RedisError as e:
        print(f'Could not connect to Redis: {e}')
        return

    print(f'Connected to Redis, starting to insert {TOTAL_DOCS} documents...')

    start = time.time()
    pipe = r.pipeline(transaction=False)

    batch_size = 1000
    for i in range(1, TOTAL_DOCS + 1):
        key = f'driver:{i}'
        doc, lon, lat = make_driver_doc(i)

        # JSON.SET key $ <doc>
        pipe.json().set(key, Path.root_path(), doc)

        if i % batch_size == 0:
            pipe.execute()
            print(f'Inserted {i} / {TOTAL_DOCS} docs...')

    # flush remaining
    pipe.execute()

    elapsed = time.time() - start
    print(f'Done. Inserted {TOTAL_DOCS} docs in {elapsed:.2f} seconds '
          f'({TOTAL_DOCS/elapsed:.0f} docs/sec).')


if __name__ == '__main__':
    main()
