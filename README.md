# thesis-poc

--- AI-Based Accuracy ---
TP: 15, FP: 0, FN: 0
Precision: 1.000, Recall: 1.000, F1: 1.000

--- AI-Based Performance ---
Processed: 90 evs in 36.5s → 2.5 ev/s
Latency ms: mean=124.1, median=6.3, p95=905.2

--- Rule-Based Accuracy ---
TP: 15, FP: 0, FN: 0
Precision: 1.000, Recall: 1.000, F1: 1.000

--- Rule-Based Performance ---
Processed: 90 evs in 43.9s → 2.1 ev/s
Latency ms: mean=6.2, median=5.9, p95=11.6

# anomaly-poc

---

## Prerequisites

* Docker & Docker Compose
* Python 3.9+
* Git (or download the project ZIP)

---

## Installation

```bash
git clone <YOUR_REPO_URL> anomaly-poc
cd anomaly-poc

python3 -m venv venv
source venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt
```

---

## Usage

### 1. Start Kafka & ZooKeeper

```bash
docker-compose up -d
```

Verify services:

```bash
docker-compose ps
```

### 2. Create Kafka Topics

```bash
docker-compose exec kafka \
  kafka-topics --bootstrap-server localhost:9092 \
               --create --topic auth_events \
               --partitions 1 --replication-factor 1

docker-compose exec kafka \
  kafka-topics --bootstrap-server localhost:9092 \
               --create --topic anomalies_rule_based \
               --partitions 1 --replication-factor 1

docker-compose exec kafka \
  kafka-topics --bootstrap-server localhost:9092 \
               --create --topic anomalies_ai_based \
               --partitions 1 --replication-factor 1
```

### 3. Run the Consumers


```bash
python rule_combined_consumer.py
```

```bash
python ai_combined_consumer.py
```

Each will listen on `auth_events` and, on **Ctrl+C**, print combined accuracy (TP/FP/FN, Precision/Recall/F₁) and performance (throughput & latency).

### 4. Generate Test Events

```bash
python multi_burst_producer.py
```

This script sends controlled bursts of failed-login events to `auth_events`.

### 5. View Results

After producer finishes, press **Ctrl+C** in each consumer terminal to display:

1. **Accuracy**

   * True Positives, False Positives, False Negatives
   * Precision, Recall, F₁

2. **Performance**

   * Total events processed & elapsed time
   * Throughput (events/sec)
   * Latency (mean, median, p95 in ms)

