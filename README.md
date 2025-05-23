# Event-Driven Anomaly Detection PoC

This proof-of-concept (PoC) project compares **rule-based** and **AI-based (fuzzy logic)** anomaly detection methods applied to an event-driven user authentication system. Synthetic failed login bursts are generated and processed through Kafka topics to evaluate detection accuracy, latency, and throughput.

---

## Prerequisites

- Docker and Docker Compose installed  
- Python 3.8+ installed  
- Python virtual environment (recommended)  
- Required Python packages installed (see below)  

---

## Setup Instructions

### 1. Start Kafka and ZooKeeper

From the project root directory where `docker-compose.yml` is located, run:

```bash
docker-compose up -d
```

This will start Kafka and ZooKeeper containers required for the messaging system.

Confirm containers are running:

```bash
docker ps
```

### 2. Setup Python Environment
Create and activate a Python virtual environment and install requirements:

```bash
python -m venv venv
source venv/bin/activate    # On Linux/macOS
venv\Scripts\activate       # On Windows PowerShell
pip install -r requirements.txt
```

### 3. Run Synthetic Event Producer
Generate synthetic bursts of failed login events:

```bash
python producer.py --failures-per-burst 6 --fail-interval 0.1 --burst-pause 1.0
```

--failures-per-burst: Number of failed logins per burst (default 6)

--fail-interval: Seconds between failures within a burst (default 0.1)

--burst-pause: Seconds pause between bursts (default 1.0)

### 4. Run Detection Consumers
Start the rule-based detector consumer:

```bash
python rule_consumer.py
```

Start the fuzzy logic detector consumer:

```bash
python fuzzy_consumer.py
```

Both listen to auth_events topic and emit anomaly alerts to their respective Kafka topics.


### 5. Run Metrics Consumer
To monitor, aggregate, and export detection metrics, run:

```bash
python metrics_consumer.py
```

Press Ctrl+C to gracefully stop the metrics consumer and print a summary of detection accuracy, latency, and throughput. Metrics are also exported to metrics_summary.csv.

