pipeline {
    agent any

    environment {
        DOCKER_HUB_REPO  = 'raviprabhakar/aceest-fitness'
        DOCKER_CREDS     = credentials('docker-hub-credentials')
        SONAR_TOKEN      = credentials('sonarqube-token')
        SONAR_HOST       = 'http://sonarqube:9000'
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
                    pip install --upgrade pip
                    pip install -r requirements.txt
                '''
            }
        }

        stage('Static Code Analysis - Lint') {
            steps {
                echo "Running flake8 lint checks..."
                sh '''
                    . venv/bin/activate
                    pip install flake8
                    flake8 ACEest_Fitness.py ACEest_Fitness_v1.py ACEest_Fitness_v2.py \
                        --max-line-length=120 \
                        --exclude=venv,__pycache__ \
                        --format=default || true
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
                    junit 'test-results.xml'
                    publishCoverage adapters: [coberturaAdapter('coverage.xml')]
                }
            }
        }

        stage('SonarQube Analysis') {
            steps {
                echo "Running SonarQube static analysis..."
                withSonarQubeEnv('SonarQube') {
                    sh '''
                        sonar-scanner \
                            -Dsonar.projectKey=aceest-fitness-gym \
                            -Dsonar.sources=. \
                            -Dsonar.exclusions=tests/**,venv/**,k8s/** \
                            -Dsonar.python.coverage.reportPaths=coverage.xml \
                            -Dsonar.python.xunit.reportPath=test-results.xml \
                            -Dsonar.host.url=${SONAR_HOST} \
                            -Dsonar.login=${SONAR_TOKEN}
                    '''
                }
            }
        }

        stage('SonarQube Quality Gate') {
            steps {
                echo "Checking SonarQube Quality Gate..."
                timeout(time: 5, unit: 'MINUTES') {
                    waitForQualityGate abortPipeline: true
                }
            }
        }

        stage('Build Docker Image') {
            steps {
                echo "Building Docker image: ${IMAGE_TAG}..."
                sh """
                    docker build \
                        --build-arg BUILD_DATE=\$(date -u +"%Y-%m-%dT%H:%M:%SZ") \
                        --build-arg VCS_REF=\$(git rev-parse --short HEAD) \
                        -t ${IMAGE_TAG} \
                        -t ${IMAGE_LATEST} \
                        .
                """
            }
        }

        stage('Test Docker Container') {
            steps {
                echo "Running smoke tests against Docker container..."
                sh """
                    docker run -d --name aceest-test-${BUILD_NUMBER} \
                        -p 5001:5000 ${IMAGE_TAG}
                    sleep 5
                    curl -f http://localhost:5001/health || (docker rm -f aceest-test-${BUILD_NUMBER} && exit 1)
                    curl -f http://localhost:5001/ || (docker rm -f aceest-test-${BUILD_NUMBER} && exit 1)
                    docker rm -f aceest-test-${BUILD_NUMBER}
                """
            }
        }

        stage('Push to Docker Hub') {
            steps {
                echo "Pushing images to Docker Hub..."
                sh """
                    echo \${DOCKER_CREDS_PSW} | docker login -u \${DOCKER_CREDS_USR} --password-stdin
                    docker push ${IMAGE_TAG}
                    docker push ${IMAGE_LATEST}
                    docker logout
                """
            }
        }

        stage('Deploy to Kubernetes') {
            steps {
                echo "Deploying Rolling Update to Kubernetes..."
                sh """
                    kubectl create namespace ${KUBE_NAMESPACE} --dry-run=client -o yaml | kubectl apply -f -
                    kubectl set image deployment/aceest-fitness \
                        aceest-fitness=${IMAGE_TAG} \
                        -n ${KUBE_NAMESPACE} || \
                    kubectl apply -f k8s/rolling-update/ -n ${KUBE_NAMESPACE}

                    kubectl rollout status deployment/aceest-fitness \
                        -n ${KUBE_NAMESPACE} --timeout=120s
                """
            }
        }

        stage('Smoke Test on Cluster') {
            steps {
                echo "Running smoke test on Kubernetes cluster..."
                sh """
                    CLUSTER_IP=\$(kubectl get svc aceest-fitness-svc \
                        -n ${KUBE_NAMESPACE} \
                        -o jsonpath='{.spec.clusterIP}')
                    curl -f http://\${CLUSTER_IP}:5000/health
                """
            }
        }
    }

    post {
        success {
            echo "Pipeline completed successfully! Image: ${IMAGE_TAG}"
        }
        failure {
            echo "Pipeline failed! Initiating rollback..."
            sh """
                kubectl rollout undo deployment/aceest-fitness \
                    -n ${KUBE_NAMESPACE} || true
            """
        }
        always {
            sh 'docker rmi ${IMAGE_TAG} ${IMAGE_LATEST} || true'
            cleanWs()
        }
    }
}
