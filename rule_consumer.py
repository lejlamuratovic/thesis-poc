import time
import json
from kafka import KafkaConsumer, KafkaProducer

WINDOW_SIZE = 60
THRESHOLD = 6

bootstrap_server = "localhost:9092"
auth_topic = "auth_events"
alert_topic = "anomalies_rule_based"

producer = KafkaProducer(
    bootstrap_servers=[bootstrap_server],
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

def main():
    consumer = KafkaConsumer(
        auth_topic,
        bootstrap_servers=[bootstrap_server],
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        group_id="rule_consumer_group"
    )
    failures = {}
    alerted_bursts = set()  # Track (ip, burst_id) tuples alerted

    for msg in consumer:
        event = msg.value
        if event["event_type"] == "FailedLogin":
            ip = event["ip_address"]
            burst_id = event.get("burst_id")
            now = time.time()
            failures.setdefault(ip, []).append(now)
            failures[ip] = [t for t in failures[ip] if now - t <= WINDOW_SIZE]

            if len(failures[ip]) >= THRESHOLD:
                if burst_id is not None and (ip, burst_id) in alerted_bursts:
                    # Already alerted for this burst and IP
                    continue

                alert = {
                    "ip_address": ip,
                    "burst_id": burst_id,
                    "detection_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "fail_count": len(failures[ip]),
                }
                producer.send(alert_topic, value=alert)
                print(f"[RULE] Anomaly alert sent: {alert}")

                if burst_id is not None:
                    alerted_bursts.add((ip, burst_id))
                failures[ip].clear()

if __name__ == "__main__":
    main()
