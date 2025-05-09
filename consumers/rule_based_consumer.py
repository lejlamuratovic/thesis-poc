import json
import time
import statistics
import signal
import sys
from datetime import datetime, timezone
from collections import defaultdict
from kafka import KafkaConsumer

# Configuration
BOOTSTRAP = ['localhost:9092']
IN_TOPIC = 'auth_events'
FAIL_THRESHOLD = 5 # alert on 6th failure
TIME_WINDOW = 60 # seconds
TOTAL_BURSTS = 5 * 3 # BURST_COUNT * len(TEST_IPS)

# States
failed = defaultdict(list)
detected = set()
duplicates = 0
processed = 0
latencies = [] # in ms
start_time = time.time()

# Kafka setup
consumer = KafkaConsumer(
    IN_TOPIC,
    bootstrap_servers=BOOTSTRAP,
    auto_offset_reset='earliest',
    group_id='rule-combined-group',
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
)

print("Rule Combined Consumer starting… (Ctrl+C to stop)")

def shutdown(sig, frame):
    elapsed = time.time() - start_time
    throughput = processed / elapsed if elapsed > 0 else 0

    tp = len(detected)
    fp = duplicates
    fn = TOTAL_BURSTS - tp
    precision = tp/(tp+fp) if (tp+fp)>0 else 0
    recall = tp/(tp+fn) if (tp+fn)>0 else 0
    f1 = 2*(precision*recall)/(precision+recall) if (precision+recall)>0 else 0

    print("\n--- Rule-Based Accuracy ---")
    print(f"TP: {tp}, FP: {fp}, FN: {fn}")
    print(f"Precision: {precision:.3f}, Recall: {recall:.3f}, F1: {f1:.3f}")

    print("\n--- Rule-Based Performance ---")
    print(f"Processed: {processed} evs in {elapsed:.1f}s → {throughput:.1f} ev/s")

    if latencies:
        p95 = statistics.quantiles(latencies, n=100)[94]
        print(f"Latency ms: mean={statistics.mean(latencies):.1f}, "
              f"median={statistics.median(latencies):.1f}, p95={p95:.1f}")
    else:
        print("No anomalies, no latency data")

    sys.exit(0)

signal.signal(signal.SIGINT, shutdown)

for msg in consumer:
    processed += 1
    ev = msg.value
    if ev.get('event_type') != 'FailedLogin':
        continue

    burst_id = ev['burst_id']
    ip = ev['ip_address']
    ts_evt = datetime.fromisoformat(ev['timestamp'].replace('Z','')).replace(tzinfo=timezone.utc).timestamp()
    now = time.time()

    # sliding window
    failed[ip].append(ts_evt)
    failed[ip] = [t for t in failed[ip] if now - t <= TIME_WINDOW]

    if len(failed[ip]) > FAIL_THRESHOLD:
        # record accuracy
        if burst_id in detected:
            duplicates += 1
        else:
            detected.add(burst_id)
            # record latency in ms
            latencies.append((now - ts_evt) * 1000)
        # reset so next alert needs new failures
        failed[ip].clear()
