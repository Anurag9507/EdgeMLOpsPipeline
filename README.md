# IoT Edge MLOps Pipeline

This project is a fully automated, secure, and self-healing End-to-End MLOps Pipeline designed for Edge IoT scenarios. It demonstrates the complete lifecycle of data ingestion, drift detection, automatic retraining, and deployment using Kubernetes.

## Key Features

*   **Orchestration:** Microservices (Broker, App, MLflow, ELK) running on Kubernetes (Minikube).
*   **Security:** Sensitive configuration is encrypted using Ansible Vault.
*   **Collaboration:** Dynamic configuration allows multiple users to use the same pipeline with their own credentials.
*   **Automation:**
    *   **Makefile:** Streamlined commands for local development, building, and deployment.
    *   **Jenkins:** CI/CD pipeline with Robust Testing (Unit + Security SAST), Vault decryption, and deployment.
*   **Self-Healing AI:** The Edge Inference service detects model drift and triggers automatic retraining without human intervention.
*   **Scalability:** Dedicated Horizontal Pod Autoscaling (HPA) configuration to handle load spikes.
*   **Observability:** ELK Stack (Logging), MLflow (Experiments), Streamlit (Dashboard).

## Project Structure

*   **Makefile**: Automation script for building, deploying, fixing config, and port forwarding.
*   **ansible/**: Contains Modular Roles (`k8s_deploy`), Inventory, and Encrypted Secrets.
*   **k8s/**: Kubernetes Manifests parameterized with placeholders for collaboration.
*   **app/**: Edge Inference logic with Drift Detection.
*   **cloud/**: Model training scripts.
*   **tests/**: Unit and Integration tests (`test_core.py`).
*   **Jenkinsfile**: The CI/CD pipeline definition.
*   **.env**: Local user configuration (Git ignored).

## Prerequisites

1.  Docker Engine and Minikube installed.
2.  Ansible (with `kubernetes.core` collection installed).
3.  Make tool.
4.  Jenkins (Running locally on port 8080).

## Initial Configuration (First Time Setup)

To run this project, you must configure your local environment and Docker Hub registry.

### 1. Docker Hub Setup
You must have a repository on Docker Hub to store the artifacts.
1.  Log in to Docker Hub.
2.  Create a **Public Repository** named `spe-mlops`.

### 2. Local Environment Configuration
Create a file named `.env` in the root directory of the project. This file is ignored by Git to prevent conflicts.

**File:** `.env`
```
DOCKER_USER=your_dockerhub_username
USER_EMAIL=your_email@gmail.com
```

### 3. Jenkins Configuration
For the CI/CD pipeline to function correctly, Jenkins requires global properties to identify the user.

1.  Navigate to **Manage Jenkins** > **System**.
2.  Scroll to **Global properties** and check **Environment variables**.
3.  Add the following two variables:
    *   **Name:** `MY_DOCKER_USER` | **Value:** `your_dockerhub_username`
    *   **Name:** `MY_EMAIL` | **Value:** `your_email@gmail.com`
4.  Click **Save**.

### 4. Jenkins Credentials
Navigate to **Manage Jenkins** > **Credentials** > **System** > **Global credentials** and add:
1.  **ID:** `dockerhub-creds` (Username with Password for Docker Hub).
2.  **ID:** `vault-pass-secret` (Secret Text). Enter the Ansible Vault password: `1234`.

### 5. Install Python Dependencies
If you plan to run tests or scripts locally (outside of Docker), install the required Python libraries:

```bash
pip install -r requirements.txt
```

## Execution Guide (Makefile)

We utilize a Makefile to abstract complex commands. Run these commands from the project root.

### 1. Start Infrastructure
Ensure Minikube is running with sufficient resources to host the ELK stack.

```bash
minikube start --driver=docker --memory=6144 --cpus=4
sudo sysctl -w vm.max_map_count=262144
```

### 2. Run the Pipeline
Select the command appropriate for your workflow:

**Option A: Full Build and Deploy**
Builds the Docker image, pushes it to your registry, runs tests, and deploys to Kubernetes.
```bash
make buildtestup
```

**Option B: Quick Deploy**
If the image is already on Docker Hub and you only need to provision the infrastructure.
```bash
make up
```

**Option C: Sync Jenkins Connectivity**
If Jenkins fails to connect to Kubernetes after a Minikube restart, run this to sync the credentials.
```bash
make fix-jenkins
```

---

## Accessing the Services

Once deployed, the Makefile automatically forwards ports. You can access the services at:

*   **Streamlit Dashboard:** http://localhost:8501
    *   *Displays real-time sensor data and drift status.*
*   **MLflow UI:** http://localhost:5001
    *   *Tracks model training runs and artifacts.*
*   **Kibana (ELK):** http://localhost:5601
    *   *Go to Stack Management > Index Patterns > Create pattern `edge-mlops-*` to view logs in Discover tab.*

## Validation of Advanced Features

*   **Scalability:** To verify Horizontal Pod Autoscaling (HPA) is active:
    ```bash
    kubectl get hpa
    ```
*   **Security:** To verify Ansible Vault encryption:
    ```bash
    cat ansible/secrets.yml
    ```
*   **Automation:** Push a change to GitHub to trigger the Jenkins Pipeline automatically via Webhook.

## Contributors

- **[IMT2022035 Sanchit Kumar Dogra:](https://github.com/meikenofdarth)** 
- **[IMT2022103 Anurag Ramaswamy:](https://github.com/Anurag9507)** 