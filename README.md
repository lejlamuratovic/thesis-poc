Event-Driven Anomaly Detection PoC

Prerequisites
Ensure you have Docker and Docker Compose installed for running Kafka and ZooKeeper containers. Python 3.8+ is required, and it’s recommended to use a Python virtual environment with necessary packages installed.
```pip install -r requirements.txt```

Setup Instructions
Start Kafka and ZooKeeper
Run ```docker-compose up -d``` from the project root where the ```docker-compose.yml``` file is located. Verify containers are running with ```docker ps```.

Setup Python environment
Create and activate a virtual environment.

On Linux/macOS: ```python3 -m venv venv``` && ```source venv/bin/activate```

On Windows PowerShell: ```python -m venv venv``` && ```.\venv\Scripts\activate```
Install dependencies with ```pip install -r requirements.txt```

Run Synthetic Event Producer
Launch the synthetic event generator with:
```python producer.py --failures-per-burst 6 --fail-interval 0.1 --burst-pause 1.0```
These parameters control the size and timing of failure bursts.

Run Detection Consumers
Start the rule-based detector with ```python rule_consumer.py```
Start the fuzzy logic detector with ```python fuzzy_consumer.py```
Both consume auth_events and produce alerts on respective Kafka topics.

Run Metrics Consumer
To aggregate detection data and compute performance metrics, run ```python metrics_consumer.py```
Press Ctrl+C to stop and generate a detailed summary and CSV report.

Configuration
Adjust the fuzzy logic detector’s sensitivity via the fuzzy_rules.json configuration file.

Kafka topics used include auth_events for synthetic events, and anomalies_rule_based and anomalies_ai_based for alerts.

