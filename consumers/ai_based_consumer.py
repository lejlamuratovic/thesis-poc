import json
import time
import statistics
import signal
import sys
from datetime import datetime, timezone
from collections import defaultdict
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl
from kafka import KafkaConsumer

# Configuration
BOOTSTRAP = ['localhost:9092']
IN_TOPIC = 'auth_events'
TIME_WINDOW = 60
ANOMALY_THRESHOLD = 70.0
TOTAL_BURSTS = 5 * 3 # BURST_COUNT * len(TEST_IPS)

# Fuzzy setup
fc = ctrl.Antecedent(np.arange(0,21,1), 'fail_count')
an = ctrl.Consequent(np.arange(0,101,1), 'anomaly')

fc['low'] = fuzz.trimf(fc.universe, [0,0,1])
fc['medium'] = fuzz.trimf(fc.universe, [1,3,5])
fc['high'] = fuzz.trimf(fc.universe, [5,6,20])
an['low'] = fuzz.trimf(an.universe, [0,0,50])
an['medium'] = fuzz.trimf(an.universe, [30,50,70])
an['high'] = fuzz.trimf(an.universe, [60,100,100])

rules = [
    ctrl.Rule(fc['high'], an['high']),
    ctrl.Rule(fc['medium'], an['medium']),
    ctrl.Rule(fc['low'], an['low'])
]
system = ctrl.ControlSystem(rules)

# Metrics measuring setup
failed = defaultdict(list)
detected = set()
duplicates = 0
processed = 0
latencies = []
start_time = time.time()

# Kafka setup
consumer = KafkaConsumer(
    IN_TOPIC,
    bootstrap_servers=BOOTSTRAP,
    auto_offset_reset='earliest',
    group_id='ai-combined-group',
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
)

print("AI Combined Consumer starting… (Ctrl+C to stop)")

def shutdown(sig, frame):
    elapsed    = time.time() - start_time
    throughput = processed / elapsed if elapsed > 0 else 0

    tp = len(detected)
    fp = duplicates
    fn = TOTAL_BURSTS - tp
    precision = tp/(tp+fp) if (tp+fp)>0 else 0
    recall = tp/(tp+fn) if (tp+fn)>0 else 0
    f1 = 2*(precision*recall)/(precision+recall) if (precision+recall)>0 else 0

    print("\n--- AI-Based Accuracy ---")
    print(f"TP: {tp}, FP: {fp}, FN: {fn}")
    print(f"Precision: {precision:.3f}, Recall: {recall:.3f}, F1: {f1:.3f}")

    print("\n--- AI-Based Performance ---")
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
    ip       = ev['ip_address']
    ts_evt = datetime.fromisoformat(ev['timestamp'].replace('Z','')).replace(tzinfo=timezone.utc).timestamp()
    now    = time.time()

    failed[ip].append(ts_evt)
    failed[ip] = [t for t in failed[ip] if now - t <= TIME_WINDOW]

    cnt = len(failed[ip])
    sim = ctrl.ControlSystemSimulation(system)
    sim.input['fail_count'] = cnt
    sim.compute()

    if sim.output.get('anomaly', 0.0) >= ANOMALY_THRESHOLD:
        if burst_id in detected:
            duplicates += 1
        else:
            detected.add(burst_id)
            latencies.append((now - ts_evt) * 1000)
        failed[ip].clear()
