import time
import json
import numpy as np
import skfuzzy as fuzz
import skfuzzy.control as ctrl
from kafka import KafkaConsumer, KafkaProducer

import json as js
with open("fuzzy_rules.json", "r") as f:
    fuzzy_config = js.load(f)

bootstrap_server = "localhost:9092"
auth_topic = "auth_events"
alert_topic = "anomalies_ai_based"

producer = KafkaProducer(
    bootstrap_servers=[bootstrap_server],
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

fail_count = ctrl.Antecedent(np.arange(0, 21, 1), "fail_count")
anomaly_score = ctrl.Consequent(np.arange(0, 101, 1), "anomaly_score")

fail_count["low"] = fuzz.trimf(fail_count.universe, fuzzy_config["fail_count"]["low"])
fail_count["medium"] = fuzz.trimf(fail_count.universe, fuzzy_config["fail_count"]["medium"])
fail_count["high"] = fuzz.trimf(fail_count.universe, fuzzy_config["fail_count"]["high"])

anomaly_score["low"] = fuzz.trimf(anomaly_score.universe, fuzzy_config["anomaly_score"]["low"])
anomaly_score["medium"] = fuzz.trimf(anomaly_score.universe, fuzzy_config["anomaly_score"]["medium"])
anomaly_score["high"] = fuzz.trimf(anomaly_score.universe, fuzzy_config["anomaly_score"]["high"])

rule1 = ctrl.Rule(fail_count["high"], anomaly_score["high"])
rule2 = ctrl.Rule(fail_count["medium"], anomaly_score["medium"])
rule3 = ctrl.Rule(fail_count["low"], anomaly_score["low"])

anomaly_ctrl = ctrl.ControlSystem([rule1, rule2, rule3])
anomaly_sim = ctrl.ControlSystemSimulation(anomaly_ctrl)

WINDOW_SIZE = 60
failures = {}
THRESHOLD_SCORE = fuzzy_config.get("threshold_score", 70)
alerted_bursts = set()  # Track (ip, burst_id)

def main():
    consumer = KafkaConsumer(
        auth_topic,
        bootstrap_servers=[bootstrap_server],
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        group_id="fuzzy_consumer_group"
    )
    for msg in consumer:
        event = msg.value
        if event["event_type"] == "FailedLogin":
            ip = event["ip_address"]
            burst_id = event.get("burst_id")
            now = time.time()
            failures.setdefault(ip, []).append(now)
            failures[ip] = [t for t in failures[ip] if now - t <= WINDOW_SIZE]
            count = len(failures[ip])
            anomaly_sim.input["fail_count"] = count
            anomaly_sim.compute()
            score = anomaly_sim.output["anomaly_score"]
            if score >= THRESHOLD_SCORE:
                if burst_id is not None and (ip, burst_id) in alerted_bursts:
                    continue
                alert = {
                    "ip_address": ip,
                    "burst_id": burst_id,
                    "detection_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "anomaly_score": float(f"{score:.2f}")
                }
                producer.send(alert_topic, value=alert)
                print(f"[FUZZY] Anomaly alert sent: {alert}")
                if burst_id is not None:
                    alerted_bursts.add((ip, burst_id))
                failures[ip].clear()

if __name__ == "__main__":
    main()
