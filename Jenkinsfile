pipeline {
    agent any

    environment {
        DOCKER_HUB_REPO  = 'raviprabhakar/aceest-fitness'
        DOCKER_CREDS     = credentials('docker-hub-credentials')
        SONAR_TOKEN      = credentials('sonarqube-token')
        SONAR_HOST       = 'http://aceest-sonarqube:9000'
        APP_VERSION      = '3.0.0'
        IMAGE_TAG        = "${DOCKER_HUB_REPO}:${APP_VERSION}"
        IMAGE_LATEST     = "${DOCKER_HUB_REPO}:latest"
        KUBE_NAMESPACE   = 'aceest-fitness'
    }

    options {
        buildDiscarder(logRotator(numToKeepStr: '10'))
        timeout(time: 30, unit: 'MINUTES')
    }

    triggers {
        pollSCM('H/5 * * * *')
    }

    stages {

        stage('Checkout') {
            steps {
                echo "Checking out source code..."
                checkout scm
                sh 'git log --oneline -5'
            }
        }

        stage('Setup Python Environment') {
            steps {
                echo "Setting up Python virtual environment..."
                sh '''
                    python3 -m venv venv
                    . venv/bin/activate
                    pip install --upgrade pip -q
                    pip install -r requirements.txt -q
                '''
            }
        }

        stage('Static Code Analysis - Lint') {
            steps {
                echo "Running flake8 lint checks..."
                sh '''
                    . venv/bin/activate
                    pip install flake8 -q
                    flake8 ACEest_Fitness.py ACEest_Fitness_v1.py ACEest_Fitness_v2.py \
                        --max-line-length=120 \
                        --exclude=venv,__pycache__ \
                        --format=default || true
                    echo "Lint stage complete"
                '''
            }
        }

        stage('Unit Tests') {
            steps {
                echo "Running Pytest unit tests with coverage..."
                sh '''
                    . venv/bin/activate
                    pytest tests/ \
                        --cov=. \
                        --cov-report=xml:coverage.xml \
                        --cov-report=term-missing \
                        --junitxml=test-results.xml \
                        -v
                '''
            }
            post {
                always {
                    junit testResults: 'test-results.xml', allowEmptyResults: true
                }
            }
        }

        stage('SonarQube Analysis') {
            steps {
                echo "Running SonarQube static analysis..."
                sh """
                    sonar-scanner \\
                        -Dsonar.projectKey=aceest-fitness-gym \\
                        -Dsonar.projectName='ACEest Fitness & Gym' \\
                        -Dsonar.projectVersion=${APP_VERSION} \\
                        -Dsonar.sources=. \\
                        -Dsonar.exclusions='tests/**,venv/**,k8s/**,**/__pycache__/**' \\
                        -Dsonar.python.coverage.reportPaths=coverage.xml \\
                        -Dsonar.python.xunit.reportPath=test-results.xml \\
                        -Dsonar.host.url=${SONAR_HOST} \\
                        -Dsonar.token=${SONAR_TOKEN}
                """
            }
        }

        stage('SonarQube Quality Gate') {
            steps {
                echo "Checking SonarQube Quality Gate via API..."
                sh """
                    ANALYSIS_ID=\$(curl -s -u '${SONAR_TOKEN}:' \\
                        '${SONAR_HOST}/api/qualitygates/project_status?projectKey=aceest-fitness-gym' \\
                        | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['projectStatus']['status'])")
                    echo "Quality Gate Status: \$ANALYSIS_ID"
                    if [ "\$ANALYSIS_ID" = "ERROR" ]; then
                        echo "QUALITY GATE FAILED"
                        exit 1
                    fi
                    echo "QUALITY GATE PASSED"
                """
            }
        }

        stage('Build Docker Image') {
            steps {
                echo "Building Docker image: ${IMAGE_TAG}..."
                sh """
                    docker build \\
                        -t ${IMAGE_TAG} \\
                        -t ${IMAGE_LATEST} \\
                        .
                """
            }
        }

        stage('Test Docker Container') {
            steps {
                echo "Running smoke tests against Docker container..."
                sh """
                    docker run -d --name aceest-test-${BUILD_NUMBER} \\
                        -p 5002:5000 ${IMAGE_TAG}
                    sleep 5
                    curl -f http://localhost:5002/health || (docker rm -f aceest-test-${BUILD_NUMBER} && exit 1)
                    docker rm -f aceest-test-${BUILD_NUMBER}
                    echo "Container smoke test passed!"
                """
            }
        }

        stage('Push to Docker Hub') {
            steps {
                echo "Pushing images to Docker Hub..."
                sh """
                    echo '${DOCKER_CREDS_PSW}' | docker login -u '${DOCKER_CREDS_USR}' --password-stdin
                    docker push ${IMAGE_TAG}
                    docker push ${IMAGE_LATEST}
                    docker logout
                    echo "Images pushed to Docker Hub!"
                """
            }
        }

        stage('Deploy to Kubernetes') {
            steps {
                echo "Deploying Rolling Update to Kubernetes..."
                sh """
                    kubectl create namespace aceest-fitness --dry-run=client -o yaml | kubectl apply -f - || true
                    kubectl set image deployment/aceest-fitness \\
                        aceest-fitness=${IMAGE_TAG} \\
                        -n aceest-fitness 2>/dev/null || \\
                    kubectl apply -f k8s/rolling-update/ -n aceest-fitness
                    kubectl rollout status deployment/aceest-fitness \\
                        -n aceest-fitness --timeout=120s
                    echo "Kubernetes deployment complete!"
                """
            }
        }

        stage('Smoke Test on Cluster') {
            steps {
                echo "Running smoke test on Kubernetes cluster..."
                sh """
                    kubectl get pods -n aceest-fitness
                    kubectl get svc -n aceest-fitness
                    echo "Cluster smoke test complete!"
                """
            }
        }
    }

    post {
        success {
            echo "Pipeline completed successfully!"
        }
        failure {
            echo "Pipeline failed! Initiating rollback..."
            sh "kubectl rollout undo deployment/aceest-fitness -n aceest-fitness || true"
        }
        always {
            sh "docker rmi raviprabhakar/aceest-fitness:3.0.0 raviprabhakar/aceest-fitness:latest || true"
            deleteDir()
        }
    }
}
