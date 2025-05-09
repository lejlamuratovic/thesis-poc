import json
import time
from datetime import datetime
from kafka import KafkaProducer

# Configuration
BOOTSTRAP_SERVERS = ['localhost:9092']
TOPIC = 'auth_events'

TEST_IPS = [
    '203.0.113.42',
    '198.51.100.7',
    '10.0.0.5'
]

BURST_COUNT = 5 # how many bursts per IP
FAILURES_PER_BURST = 6 # number of failures in each burst
FAIL_INTERVAL = 0.1 # seconds between failures
BURST_PAUSE = 1.0 # seconds between bursts for same IP

# Kafka Producer
producer = KafkaProducer(
    bootstrap_servers=BOOTSTRAP_SERVERS,
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# Generate Bursts
burst_id = 0
for ip in TEST_IPS:
    print(f"\n=== bursts for IP {ip} ===")
    for b in range(1, BURST_COUNT+1):
        burst_id += 1
        print(f"Burst {b}/{BURST_COUNT} (burst_id={burst_id}): sending {FAILURES_PER_BURST} failures")
        for i in range(1, FAILURES_PER_BURST+1):
            evt = {
                "burst_id": burst_id,
                "event_type": "FailedLogin",
                "username": "test_user",
                "ip_address": ip,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }

            producer.send(TOPIC, evt)
            print(f"[Fail {i}] → {evt}")

            time.sleep(FAIL_INTERVAL)
        producer.flush()
        time.sleep(BURST_PAUSE)

producer.close()
print("\nBursts complete")
