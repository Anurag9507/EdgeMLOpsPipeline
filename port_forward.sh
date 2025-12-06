#!/bin/bash

echo "🔌 Stopping any existing port-forwards..."
pkill -f "kubectl port-forward"

echo "🚀 Starting Port Forwards..."

# 1. Streamlit Dashboard (Background)
nohup kubectl port-forward svc/dashboard 8501:8501 --address 0.0.0.0 > /dev/null 2>&1 &
echo "✅ Dashboard: http://localhost:8501"

# 2. MLflow (Background)
nohup kubectl port-forward svc/mlflow 5001:5001 --address 0.0.0.0 > /dev/null 2>&1 &
echo "✅ MLflow:    http://localhost:5001"

# 3. ELK Stack (Background)
# Wait for ELK to be ready first
echo "⏳ Waiting for ELK to be ready..."
kubectl wait --for=condition=ready pod -l app=elk --timeout=60s > /dev/null 2>&1
nohup kubectl port-forward svc/elk 5601:5601 --address 0.0.0.0 > /dev/null 2>&1 &
echo "✅ Kibana:    http://localhost:5601"

echo "🎉 All services are accessible! (Press Ctrl+C to exit script, connections will stay open)"