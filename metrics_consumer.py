import time
import json
from kafka import KafkaConsumer
from collections import defaultdict
from datetime import datetime, timezone
import csv
import threading

bootstrap_server = "localhost:9092"
auth_topic = "auth_events"
rule_alert_topic = "anomalies_rule_based"
fuzzy_alert_topic = "anomalies_ai_based"

lock = threading.Lock()

# Store event timestamps for ground truth (burst_id -> list of event timestamps)
events_by_burst = defaultdict(list)

# Store detections (detector -> list of detection dicts)
detections = defaultdict(list)

start_time = None
end_time = None

def parse_timestamp(ts_str):
    dt = datetime.strptime(ts_str, "%Y-%m-%dT%H:%M:%SZ")
    dt = dt.replace(tzinfo=timezone.utc)
    return dt.timestamp()

def consume():
    global start_time, end_time
    consumer = KafkaConsumer(
        auth_topic, rule_alert_topic, fuzzy_alert_topic,
        bootstrap_servers=[bootstrap_server],
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        group_id="metrics_consumer_group"
    )
    start_time = time.time()
    for msg in consumer:
        topic = msg.topic
        data = msg.value

        if topic == auth_topic:
            # Record event timestamp by burst_id (for synthetic only)
            burst_id = data.get("burst_id")
            if burst_id is not None:
                ts = parse_timestamp(data["timestamp"])
                with lock:
                    events_by_burst[burst_id].append(ts)

        else:
            # This is an anomaly alert
            detector = "rule" if topic == rule_alert_topic else "fuzzy"
            ip = data.get("ip_address")
            burst_id = data.get("burst_id")
            detection_ts = parse_timestamp(data.get("detection_timestamp"))
            with lock:
                detections[detector].append({
                    "ip": ip,
                    "burst_id": burst_id,
                    "detection_ts": detection_ts
                })

def compute_metrics():
    global start_time, end_time
    end_time = time.time()

    results = {}

    # Flatten burst event timestamps: get earliest event time per burst_id as ground truth
    with lock:
        ground_truth_bursts = {b: min(ts_list) for b, ts_list in events_by_burst.items()}

        for detector, det_list in detections.items():
            tp = 0
            fp = 0
            fn = 0
            latencies = []
            detected_bursts = set()

            for det in det_list:
                burst_id = det.get("burst_id")
                detection_ts = det.get("detection_ts")

                if burst_id in ground_truth_bursts:
                    tp += 1
                    detected_bursts.add(burst_id)
                    latency = (detection_ts - ground_truth_bursts[burst_id]) * 1000
                    latencies.append(latency)
                else:
                    fp += 1

            fn = len(ground_truth_bursts.keys() - detected_bursts)

            precision = tp / (tp + fp) if (tp + fp) > 0 else 0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0
            f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
            throughput = len(detections[detector]) / (end_time - start_time) if (end_time and start_time) else 0

            avg_latency = sum(latencies)/len(latencies) if latencies else None

            results[detector] = {
                "TP": tp,
                "FP": fp,
                "FN": fn,
                "Precision": precision,
                "Recall": recall,
                "F1": f1,
                "AverageLatencyMs": avg_latency,
                "ThroughputEventsPerSec": throughput
            }
    return results

def export_results(results):
    with open("metrics_summary.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["Detector", "TP", "FP", "FN", "Precision", "Recall", "F1", "AverageLatencyMs", "ThroughputEventsPerSec"])
        writer.writeheader()
        for detector, metrics in results.items():
            row = {"Detector": detector}
            row.update(metrics)
            writer.writerow(row)

if __name__ == "__main__":
    import threading
    import signal
    import sys

    consumer_thread = threading.Thread(target=consume, daemon=True)
    consumer_thread.start()

    def shutdown(signum, frame):
        print("\nShutting down metrics consumer...")
        metrics = compute_metrics()
        print("Metrics summary:", metrics)
        export_results(metrics)
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    print("Metrics consumer started. Press Ctrl+C to stop and print metrics.")
    while True:
        time.sleep(1)
