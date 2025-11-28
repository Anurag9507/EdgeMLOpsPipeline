pipeline {
    agent any

    environment {
        DOCKER_IMAGE = "anurag9507/spe-mlops"
        REGISTRY_CREDS = credentials('dockerhub-creds')
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    // Build with a unique tag (Build Number) and 'latest'
                    sh "docker build -t ${DOCKER_IMAGE}:${BUILD_NUMBER} ."
                    sh "docker tag ${DOCKER_IMAGE}:${BUILD_NUMBER} ${DOCKER_IMAGE}:latest"
                }
            }
        }

        stage('Automated Test') {
            steps {
                script {
                    echo "Running Syntax Checks..."
                    // This checks if the Python files are valid without running the infinite loop
                    sh "docker run --rm ${DOCKER_IMAGE}:${BUILD_NUMBER} python -m py_compile cloud/train.py app/edge_infer.py devices/publisher.py"
                    echo "Syntax Check Passed!"
                }
            }
        }

        stage('Push to Docker Hub') {
            steps {
                script {
                    // Login using the credentials variable
                    sh "echo $REGISTRY_CREDS_PSW | docker login -u $REGISTRY_CREDS_USR --password-stdin"
                    
                    // Push both specific version and latest
                    sh "docker push ${DOCKER_IMAGE}:${BUILD_NUMBER}"
                    sh "docker push ${DOCKER_IMAGE}:latest"
                }
            }
        }

        stage('Deploy to K8s') {
            steps {
                script {
                    // 1. Update the YAML to use the specific Build Number (Forces K8s to update)
                    sh "sed -i 's|:latest|:${BUILD_NUMBER}|g' k8s/app-deployment.yaml"   
                    // 2. Run Ansible to apply changes
                    sh "ansible-playbook -i ansible/inventory.ini ansible/deploy.yml"
                }
            }
        }
    }

    post {
        always {
            // Clean up local docker images to save space
            sh "docker rmi ${DOCKER_IMAGE}:${BUILD_NUMBER} || true"
            sh "docker rmi ${DOCKER_IMAGE}:latest || true"
        }
    }
}