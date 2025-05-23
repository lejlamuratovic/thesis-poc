
# Proof of Concept: Rule-Based vs AI-Based Anomaly Detection

This PoC demonstrates the comparison between Rule-Based and AI-Based (Fuzzy Logic) anomaly detection in an event-driven user authentication pipeline using Kafka.

## Setup Instructions

### 1. Docker Setup

To start the Kafka and Zookeeper services, use the following command:

```bash
docker-compose up
```

This will start the required services for Kafka communication. Make sure that Docker is installed and running on your machine.

### 2. Python Environment Setup

Create a Python virtual environment:

```bash
python3 -m venv venv
```

Activate the virtual environment:

- For Linux/macOS: `source venv/bin/activate`
- For Windows: `venv\Scriptsctivate`

Install the required dependencies:

```bash
pip install -r requirements.txt
```

### 3. Running the Pipeline

You can start the Kafka consumers and producers using the Python scripts provided.

1. **Start the Kafka Producer (Synthetic Data Generation)**:
   Run the script to simulate authentication events and push them to Kafka.

2. **Start the Rule-Based Consumer**:
   This will listen for events from Kafka and process them based on fixed rules for anomaly detection.

3. **Start the AI-Based (Fuzzy Logic) Consumer**:
   This will listen for events and apply fuzzy logic inference for anomaly scoring.

### 4. Experiment and Metrics Collection

Once the pipeline is running, you can trigger synthetic events and evaluate the performance of both detection systems (latency, throughput, accuracy).

