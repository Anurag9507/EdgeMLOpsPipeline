# Makefile for Edge MLOps Pipeline

ifneq (,$(wildcard .env))
    include .env
    export
endif

# Default Variables
DOCKER_USER ?= anurag9507
IMAGE_NAME = spe-mlops

# 0. Build Docker Image
build:
	@echo "Building image for user: $(DOCKER_USER)..."
	docker build -t $(DOCKER_USER)/$(IMAGE_NAME):latest .
	docker push $(DOCKER_USER)/$(IMAGE_NAME):latest

test:
	@echo "Running tests..."
	python tests/test_logic.py

# 1. Deploy Infrastructure with Ansible	
deploy:
	@echo "Deploying with Ansible (Enter Vault Password: 1234)..."
	sed -i 's|DOCKER_USER_PLACEHOLDER|$(DOCKER_USER)|g' k8s/*.yaml
	cd ansible && ansible-playbook -i inventory.ini deploy.yml --ask-vault-pass -e "ansible_python_interpreter=$$(which python)"
	sed -i 's|$(DOCKER_USER)|DOCKER_USER_PLACEHOLDER|g' k8s/*.yaml

# 2. Check Pod Status
status:
	kubectl get pods

# 3. Auto-Forward
forward:
	@echo "Starting Port Forwarding..."
	@echo "Dashboard: http://localhost:8501"
	@echo "MLflow:    http://localhost:5001"
	@echo "Kibana:    http://localhost:5601"
	@nohup kubectl port-forward svc/dashboard 8501:8501 > /dev/null 2>&1 &
	@nohup kubectl port-forward svc/mlflow 5001:5001 > /dev/null 2>&1 &
	@nohup kubectl port-forward svc/elk 5601:5601 > /dev/null 2>&1 &

# 4. Stop Forwarding
stop-forward:
	@echo "Stopping all port forwards..."
	pkill -f "kubectl port-forward"

# 5. One Command to Deploy and Forward
up: deploy forward

buildup: build deploy forward

buildtestup: build test deploy forward

# 6. Fix Kubeconfig for Jenkins
fix-jenkins:
	@echo " Syncing Kubeconfig to Jenkins..."
	kubectl config view --flatten > config_temp
	sudo mv config_temp /var/lib/jenkins/.kube/config
	sudo chown jenkins:jenkins /var/lib/jenkins/.kube/config