pipeline {
    agent any

    environment {
        //Docker Hub Image Name
        DOCKER_IMAGE = "anurag9507/spe-mlops"
        REGISTRY_CREDS = credentials('dockerhub-creds')
        // Vault Password for Automation
        VAULT_PASS = credentials('vault-pass-secret') 
    }

    stages {

        stage('Build Docker Image') {
            steps {
                script {
                    echo "Building image..."
                    sh "docker build -t ${DOCKER_IMAGE}:${BUILD_NUMBER} ."
                    sh "docker tag ${DOCKER_IMAGE}:${BUILD_NUMBER} ${DOCKER_IMAGE}:latest"
                }
            }
        }

        // stage('Automated Test') {
        //     steps {
        //         script {
        //             echo "Running Syntax Checks..."
        //             sh "docker run --rm ${DOCKER_IMAGE}:${BUILD_NUMBER} python -m py_compile cloud/train.py app/edge_infer.py devices/publisher.py"
        //         }
        //     }
        // }
        stage('Robust Testing') {
                    steps {
                        script {
                            echo "--- Phase 1: Unit & Integration Testing ---"
                            // Runs the pytest file inside the container
                            // This verifies logic in edge_infer.py and train.py
                            sh "docker run --rm ${DOCKER_IMAGE}:${BUILD_NUMBER} pytest tests/"
                            
                            echo "--- Phase 2: Security Vulnerability Scan ---"
                            // 1. Bandit: Checks Python code for security issues (e.g. hardcoded passwords, unsafe subprocess)
                            // The '|| true' ensures the pipeline reports issues but doesn't crash on warnings
                            sh "docker run --rm ${DOCKER_IMAGE}:${BUILD_NUMBER} bandit -r app/ cloud/ -f custom || true"
                            
                            // 2. Safety: Checks installed dependencies (requirements.txt) for known CVEs
                            sh "docker run --rm ${DOCKER_IMAGE}:${BUILD_NUMBER} safety check || true"
                        }
                    }
                }

        stage('Push to Docker Hub') {
            steps {
                script {
                    echo "Pushing to Docker Hub..."
                    sh "echo $REGISTRY_CREDS_PSW | docker login -u $REGISTRY_CREDS_USR --password-stdin"
                    sh "docker push ${DOCKER_IMAGE}:${BUILD_NUMBER}"
                    sh "docker push ${DOCKER_IMAGE}:latest"
                }
            }
        }

        stage('Deploy to K8s') {
            steps {
                script {
                    echo "Deploying to Kubernetes..."
                    
                    // 1. Update K8s manifest to use the new Build Number
                    sh "sed -i 's|:latest|:${BUILD_NUMBER}|g' k8s/app-deployment.yaml"
                    
                    // 2. Create temporary Vault Password file for automation
                    sh "echo '${VAULT_PASS}' > ansible/.vault_pass"
                    
                    // 3. Run Ansible using the password file (Non-interactive mode)
                    sh "ansible-playbook -i ansible/inventory.ini ansible/deploy.yml --vault-password-file ansible/.vault_pass"
                    
                    // 4. Cleanup password file
                    sh "rm ansible/.vault_pass"
                }
            }
        }
    }

    post {
        always {
            // Clean up to save disk space
            sh "docker rmi ${DOCKER_IMAGE}:${BUILD_NUMBER} || true"
            sh "docker rmi ${DOCKER_IMAGE}:latest || true"
        }
        success {
            mail to: 'anurag.ramaswamy.201344@gmail.com',
            subject: "Build #${env.BUILD_NUMBER} SUCCESS",
            body: """\
            BUILD SUCCESS!
            Pipeline: ${env.JOB_NAME}
            Build Number: ${env.BUILD_NUMBER}
            URL: ${env.BUILD_URL}
            """
        }
        failure {
            mail to: 'anurag.ramaswamy.201344@gmail.com',
            subject: "Build #${env.BUILD_NUMBER} FAILURE",
            body: """\
            BUILD FAILURE!
            Pipeline: ${env.JOB_NAME}
            Build Number: ${env.BUILD_NUMBER}
            URL: ${env.BUILD_URL}
            """
        }
    }
}