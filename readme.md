# ACEest Fitness & Gym — DevOps Assignment 2

**Student:** Ravi Ranjan Prabhakar  
**Email:** 2022us70038@wilp.bits-pilani.ac.in  
**Course:** Introduction to DEVOPS (CSIZG514/SEZG514) — S1-25

---

## Quick Start

```bash
# Clone and run locally
git clone https://github.com/rrprabhakar2003/ACEest.git
cd ACEest
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python ACEest_Fitness.py        # runs on http://localhost:5001
```

## Run Tests

```bash
pytest tests/ --cov=. -v       # 101 tests across 3 files
```

## Docker

```bash
docker pull raviprabhakar/aceest-fitness:3.0.0
docker run -p 5001:5000 raviprabhakar/aceest-fitness:3.0.0
```

## CI/CD Stack

| Tool | Purpose | URL |
|------|---------|-----|
| Jenkins | Pipeline automation | http://localhost:8080 |
| SonarQube | Code quality gate | http://localhost:9000 |
| Docker Hub | Image registry | hub.docker.com/r/raviprabhakar/aceest-fitness |
| Minikube | Local K8s cluster | `minikube dashboard` |

```bash
# Start all services
docker-compose up -d jenkins sonarqube
```

## Application Versions

| Tag | Features |
|-----|----------|
| v1.0.0 | Members CRUD, membership plans (Basic/Premium/VIP) |
| v2.0.0 | + Class scheduling, bookings with capacity enforcement |
| v3.0.0 | + Workout logging, trainer management, equipment, dashboard UI |

## Kubernetes Deployment Strategies

| Strategy | Namespace | Command |
|----------|-----------|---------|
| Rolling Update | aceest-fitness | `kubectl apply -f k8s/rolling-update/` |
| Blue-Green | aceest-fitness | `kubectl apply -f k8s/blue-green/` |
| Canary | aceest-fitness | `kubectl apply -f k8s/canary/` |
| Shadow | aceest-fitness | `kubectl apply -f k8s/shadow/` |
| A/B Testing | aceest-fitness | `kubectl apply -f k8s/ab-testing/` |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Home UI |
| GET | `/health` | Health check |
| GET/POST | `/members` | Member management |
| GET/POST | `/classes` | Class scheduling |
| GET/POST | `/bookings` | Class bookings |
| GET/POST | `/trainers` | Trainer management |
| GET/POST | `/workouts` | Workout logging |
| GET/POST | `/equipment` | Equipment tracking |
| GET | `/dashboard` | Stats dashboard |
| GET | `/plans` | Membership plans |
