# ACEest Fitness & Gym — DevOps CI/CD Report

**Student:** Ravi Ranjan  
**Email:** ravi.ranjan@thesouledstore.com  
**Course:** Introduction to DEVOPS (CSIZG514/SEZG514) — S1-25  
**Assignment:** 2 — DevOps CI/CD Implementation

---

## 1. CI/CD Architecture Overview

### Pipeline Flow

```
Developer Push → GitHub → Jenkins (Poll SCM)
    │
    ├─► Checkout Code
    ├─► Setup Python venv
    ├─► Lint (flake8)
    ├─► Unit Tests (Pytest + Coverage)
    ├─► SonarQube Analysis + Quality Gate
    ├─► Build Docker Image
    ├─► Container Smoke Test
    ├─► Push to Docker Hub
    └─► Deploy to Kubernetes (Rolling Update)
              │
              ├─ Rollback on failure (kubectl rollout undo)
              └─ Smoke test on cluster
```

### Application Versions

| Version | Key Features |
|---------|-------------|
| v1.0.0 | Member registration, membership plans (Basic/Premium/VIP), health endpoint |
| v2.0.0 | + Class scheduling (Yoga, HIIT, CrossFit…), class bookings |
| v3.0.0 | + Workout logging, trainer management, equipment tracking, dashboard |

### Tool Stack

| Category | Tool | Purpose |
|----------|------|---------|
| Version Control | Git + GitHub | Source code management, branching, tagging |
| Build & CI | Jenkins | Pipeline automation, SCM polling |
| Testing | Pytest + pytest-cov | Unit tests, coverage reporting |
| Code Quality | SonarQube | Static analysis, quality gate enforcement |
| Containerization | Docker | Application packaging |
| Registry | Docker Hub | Image storage and versioning |
| Orchestration | Minikube / Kubernetes | Deployment, scaling, rollback |

---

## 2. Deployment Strategies

### 2.1 Rolling Update
Default strategy. Replaces pods one-by-one: `maxSurge: 1`, `maxUnavailable: 0`.  
Zero downtime. Automatic rollback via `kubectl rollout undo`.

**Rollback command:**
```bash
kubectl rollout undo deployment/aceest-fitness -n aceest-fitness
```

### 2.2 Blue-Green Deployment
Two identical environments (Blue = v2, Green = v3) run in parallel.  
Traffic is switched by patching the Service selector from `slot: blue` to `slot: green`.

**Switch to Green (new version):**
```bash
kubectl patch svc aceest-fitness-bg-svc \
  -p '{"spec":{"selector":{"slot":"green"}}}' \
  -n aceest-fitness
```

**Rollback to Blue (instant):**
```bash
kubectl patch svc aceest-fitness-bg-svc \
  -p '{"spec":{"selector":{"slot":"blue"}}}' \
  -n aceest-fitness
```

### 2.3 Canary Release
New version (v3) receives ~10% of traffic (1 pod) alongside stable (v2, 9 pods).  
Both deployments share the `app: aceest-fitness` label so the single Service routes to both.  
To promote: scale canary to 10, stable to 0, then update stable image.

### 2.4 Shadow Deployment
Production (v2) serves real users; Shadow (v3) receives mirrored copies of all requests.  
Shadow responses are discarded — no impact on users.  
Used to validate v3 behaviour with live traffic before promotion.  
Traffic mirroring configured at the ingress/proxy layer (Nginx or Istio `mirror` directive).

### 2.5 A/B Testing
Version A (v2) and Version B (v3) run simultaneously on separate NodePorts (30084, 30085).  
Users are routed to A or B based on session ID, HTTP header, or geographic region.  
Metrics are collected per variant to determine which version performs better before full rollout.

---

## 3. Pytest Test Summary

| Test File | Covers | Tests |
|-----------|--------|-------|
| `tests/test_v1.py` | v1: Members, Plans, Health | 30 |
| `tests/test_v2.py` | v2: Classes, Bookings | 27 |
| `tests/test_app.py` | v3: Trainers, Workouts, Equipment, Dashboard | 40 |

All tests use Flask's `test_client()`. Each test class resets in-memory state via an `autouse` fixture. Coverage is reported to `coverage.xml` and consumed by SonarQube.

---

## 4. SonarQube Quality Gate

SonarQube is configured via `sonar-project.properties` and integrated into the Jenkins pipeline stage `SonarQube Analysis`. The `waitForQualityGate` step aborts the pipeline if code quality thresholds are not met.

Key metrics enforced:
- Code coverage > 80%
- No critical/blocker issues
- Technical debt ratio < 5%

---

## 5. Challenges Faced & Mitigation

| Challenge | Mitigation |
|-----------|-----------|
| In-memory state leaks between tests | `autouse` pytest fixture clears all dicts before/after each test |
| Docker socket access from Jenkins container | Mount `/var/run/docker.sock` into the Jenkins container (see `docker-compose.yml`) |
| SonarQube memory requirements | Set `SONAR_ES_BOOTSTRAP_CHECKS_DISABLE=true`; allocate ≥2 GB RAM to Docker |
| Zero-downtime rolling updates | `maxUnavailable: 0` + readiness probes ensure pods are healthy before old ones are removed |
| Blue-Green instant rollback | Service selector patch is atomic — switchover takes <1 second |
| Canary traffic split without Istio | Controlled by pod replica ratio (9:1); no mesh required |

---

## 6. Key Automation Outcomes

- **Fully automated pipeline:** every `git push` triggers lint → test → scan → build → push → deploy.
- **Quality gate enforcement:** broken code never reaches the registry; SonarQube blocks the build.
- **Versioned Docker images:** `raviranjan/aceest-fitness:1.0.0`, `2.0.0`, `3.0.0`, and `latest` on Docker Hub.
- **Five deployment strategies** implemented and ready to apply against any Kubernetes cluster.
- **Instant rollback:** Blue-Green switch or `kubectl rollout undo` recovers in under 60 seconds.
- **97 unit tests** covering all API endpoints across all three application versions.
