import time
import json
import argparse
from kafka import KafkaProducer

def generate_synthetic_events(producer, topic, args):
    burst_id = 1
    while True:
        for _ in range(args.failures_per_burst):
            event = {
                "burst_id": burst_id,
                "username": args.username,
                "ip_address": args.ip,
                "event_type": "FailedLogin",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            }
            producer.send(topic, value=event)
            time.sleep(args.fail_interval)
        burst_id += 1
        time.sleep(args.burst_pause)

def main():
    parser = argparse.ArgumentParser("synthetic_producer")
    parser.add_argument("--bootstrap-server", default="localhost:9092")
    parser.add_argument("--topic", default="auth_events")
    parser.add_argument("--failures-per-burst", type=int, default=6)
    parser.add_argument("--fail-interval", type=float, default=0.1)
    parser.add_argument("--burst-pause", type=float, default=1.0)
    parser.add_argument("--username", default="attack_user")
    parser.add_argument("--ip", default="203.0.113.99")
    args = parser.parse_args()

    producer = KafkaProducer(
        bootstrap_servers=[args.bootstrap_server],
        value_serializer=lambda v: json.dumps(v).encode("utf-8")
    )
    print(f"Producing synthetic events to {args.topic} on {args.bootstrap_server}")
    generate_synthetic_events(producer, args.topic, args)

if __name__ == "__main__":
    main()
