# Makefile for Edge MLOps Pipeline

# 1. Deploy Infrastructure with Ansible
deploy:
	@echo "Deploying with Ansible (Enter Vault Password: 1234)..."
	cd ansible && ansible-playbook -i inventory.ini deploy.yml --ask-vault-pass -e "ansible_python_interpreter=$$(which python)"

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