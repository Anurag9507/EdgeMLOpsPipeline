# IoT Edge MLOps Pipeline

This project is a fully automated, secure, and self-healing End-to-End MLOps Pipeline designed for Edge IoT scenarios. It demonstrates the complete lifecycle of data ingestion, drift detection, automatic retraining, and deployment using Kubernetes.

## Key Features

*   **Orchestration:** Microservices (Broker, App, MLflow, ELK) running on Kubernetes (Minikube).
*   **Security:** Sensitive configuration is encrypted using Ansible Vault.
*   **Automation:**
    *   **Makefile:** Streamlined one-command deployment and port forwarding.
    *   **Jenkins:** CI/CD pipeline with automated testing, Vault decryption, and deployment.
*   **Self-Healing AI:** The Edge Inference service detects model drift and triggers automatic retraining without human intervention.
*   **Scalability:** Dedicated Horizontal Pod Autoscaling (HPA) configuration to handle load spikes.
*   **Observability:**
    *   **ELK Stack:** Centralized logging via Logstash (MQTT) to Elasticsearch and Kibana.
    *   **MLflow:** Experiment tracking and model versioning.
    *   **Streamlit:** Real-time dashboard for sensor data and prediction visualization.

## Project Structure

*   **Makefile** - Automation script for deploying, checking status, and port forwarding.
*   **ansible/**
    *   **inventory.ini** - Localhost inventory definition.
    *   **deploy.yml** - Main Playbook.
    *   **secrets.yml** - Encrypted Vault file containing sensitive credentials.
    *   **roles/** - Modular Ansible roles for infrastructure, apps, and monitoring.
*   **k8s/**
    *   **app-deployment.yaml** - Main Application Pod (Publisher, Inference, Dashboard).
    *   **hpa.yaml** - Horizontal Pod Autoscaler configuration.
    *   **elk-stack.yaml** - Elasticsearch and Kibana.
    *   **logstash.yaml** - Custom Logstash deployment with MQTT support.
    *   **mosquitto.yaml** - MQTT Broker.
    *   **mlflow.yaml** - MLflow Tracking Server.
*   **app/** - Edge Inference logic with Drift Detection.
*   **cloud/** - Model training scripts.
*   **dashboard/** - Streamlit visualization.
*   **Jenkinsfile** - The CI/CD pipeline definition.

## Prerequisites

1.  Docker Engine & Minikube
2.  Ansible (with kubernetes.core collection)
3.  Make
4.  Jenkins

## Quick Start (Makefile)

We have included a Makefile to automate the entire setup process.

### 1. Start Infrastructure
Ensure Minikube is running and memory is configured correctly for the ELK stack.

```bash
minikube start --driver=docker --memory=4096 --cpus=2
sudo sysctl -w vm.max_map_count=262144
```

### 2. Deploy and Run
Run the following command to deploy the infrastructure and start port forwarding automatically.

```bash
make up
```
*Note: The default Ansible Vault password for this project is `1234`.*

### 3. Verification
You can check the status of the pods using:

```bash
make status
```

## Security and Secrets

This project uses Ansible Vault to secure sensitive data.
*   **Encrypted File:** `ansible/secrets.yml`
*   **Local Usage:** The Makefile prompts for the password interactively.
*   **CI/CD Usage:** The Jenkins pipeline decrypts the file automatically using the `VAULT_PASS` credential stored in the Jenkins Credential Store.

## Accessing the Services

If you used `make up`, the following services are available immediately:

*   **Streamlit Dashboard:** http://localhost:8501
*   **MLflow UI:** http://localhost:5001
*   **Kibana (ELK):** http://localhost:5601

## ELK Stack Configuration

To view the logs in Kibana:
1.  Navigate to http://localhost:5601
2.  Go to **Stack Management** -> **Index Patterns**.
3.  Create a new index pattern named: `edge-mlops-*`
4.  Select `@timestamp` as the time field.
5.  Go to the **Discover** tab to view live MQTT logs.

## Jenkins Automation

The CI/CD pipeline is defined in the `Jenkinsfile`.
*   **Build:** Creates Docker images tagged with the specific Build Number.
*   **Test:** Runs syntax and logic checks.
*   **Push:** Uploads images to Docker Hub.
*   **Security:** Decrypts Ansible Vault secrets securely.
*   **Deploy:** Updates the Kubernetes cluster using the Ansible playbook.

## Scalability

Horizontal Pod Autoscaling is defined in `k8s/hpa.yaml`. It monitors the `spe-app` deployment and scales replicas between 1 and 5 based on CPU utilization (Target: 50%).

You can verify the scaling status by running:
```bash
kubectl get hpa
```