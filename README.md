<div align="center">

<h1>🏥 Self-Healing GitOps Deployment Platform</h1>

<p>
  <strong>Production-grade progressive delivery with automated rollback — zero human intervention</strong>
</p>

<p>
  <img src="https://img.shields.io/badge/Kubernetes-326CE5?style=for-the-badge&logo=kubernetes&logoColor=white" alt="Kubernetes"/>
  <img src="https://img.shields.io/badge/ArgoCD-EF7B4D?style=for-the-badge&logo=argo&logoColor=white" alt="ArgoCD"/>
  <img src="https://img.shields.io/badge/Prometheus-E6522C?style=for-the-badge&logo=prometheus&logoColor=white" alt="Prometheus"/>
  <img src="https://img.shields.io/badge/Grafana-F46800?style=for-the-badge&logo=grafana&logoColor=white" alt="Grafana"/>
  <img src="https://img.shields.io/badge/GitHub_Actions-2088FF?style=for-the-badge&logo=github-actions&logoColor=white" alt="GitHub Actions"/>
  <img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker"/>
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI"/>
  <img src="https://img.shields.io/badge/Terraform-7B42BC?style=for-the-badge&logo=terraform&logoColor=white" alt="Terraform"/>
</p>

<p>
  <img src="https://img.shields.io/badge/status-production--ready-brightgreen?style=flat-square" alt="Status"/>
  <img src="https://img.shields.io/badge/rollback-automated-blue?style=flat-square" alt="Rollback"/>
  <img src="https://img.shields.io/badge/canary-5--step-purple?style=flat-square" alt="Canary"/>
  <img src="https://img.shields.io/badge/MTTR-%3C%203%20min-orange?style=flat-square" alt="MTTR"/>
</p>

</div>

---

## 📋 Table of Contents

- [Problem Statement](#-problem-statement)
- [Solution Overview](#-solution-overview)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Key Features](#-key-features)
- [Self-Healing Demo](#-self-healing-demo-proven-results)
- [Getting Started](#-getting-started)
- [How It Works](#-how-it-works-deep-dive)
- [CI/CD Pipeline](#-cicd-pipeline)
- [GitOps Workflow](#-gitops-workflow)
- [Observability Stack](#-observability-stack)
- [Infrastructure as Code](#-infrastructure-as-code)
- [Configuration Reference](#-configuration-reference)
- [Lessons Learned](#-lessons-learned)
- [What's Next](#-whats-next)

---

## 🔥 Problem Statement

Most CI/CD pipelines **deploy blindly** — push code, hope it works. When production breaks:

1. An engineer has to **manually notice** the issue (often from an alert at 3 AM)
2. Manually investigate: is it the new deploy or something else?
3. Manually trigger a rollback and wait for it to complete
4. Repeat

**Mean time to recovery (MTTR)** can be 30+ minutes. Users suffer. This project solves that.

---

## ✅ Solution Overview

A platform that:

1. **Deploys progressively** (canary-style: 10% → 25% → 50% → 100%) instead of all-at-once
2. **Monitors in real-time** — queries Prometheus every 15 seconds for error rate and P99 latency
3. **Auto-aborts** the canary if metrics degrade past thresholds
4. **Auto-rolls back** to the last known good version — **zero human intervention**
5. **Alerts** the team via Alertmanager when a rollback fires

> **MTTR: ~3 minutes. Zero manual steps. Zero downtime to end users.**

---

## 🏗 Architecture

```
                     ┌─────────────────────────────────────────────────┐
                     │            GitHub (Source of Truth)              │
                     │                                                   │
                     │  ┌─────────────────┐  ┌────────────────────────┐│
                     │  │  order-service   │  │ gitops-selfhealing-    ││
                     │  │  (app code)      │  │ config (k8s manifests) ││
                     │  └────────┬─────────┘  └──────────┬─────────────┘│
                     └───────────┼───────────────────────┼──────────────┘
                                 │ git push               │ ArgoCD watches
                                 ▼                        ▼
                     ┌───────────────────┐    ┌───────────────────────┐
                     │  GitHub Actions   │    │       ArgoCD          │
                     │  ─────────────── │    │  ──────────────────── │
                     │  1. pytest        │    │  Auto-syncs cluster   │
                     │  2. trivy scan    │───▶│  to Git state         │
                     │  3. docker push   │    │  (reconciles drift)   │
                     │  4. patch GitOps  │    └──────────┬────────────┘
                     └───────────────────┘               │ applies
                                                         ▼
                     ┌───────────────────────────────────────────────────────┐
                     │                  kind Cluster (local)                 │
                     │                                                       │
                     │  ┌─────────────────────────────────────────────────┐ │
                     │  │              Argo Rollouts                       │ │
                     │  │  ┌──────────┐  10%  ┌──────────┐  25%  ┌──────┐│ │
                     │  │  │  stable  │──────▶│  canary  │──────▶│ ...  ││ │
                     │  │  │  (v1.0)  │       │  (v1.1)  │  ▲    └──────┘│ │
                     │  │  └──────────┘       └──────────┘  │            │ │
                     │  │                          │    ABORT if fail     │ │
                     │  │                          ▼         │            │ │
                     │  │                   ┌────────────┐   │            │ │
                     │  │                   │AnalysisRun │───┘            │ │
                     │  │                   │ (every 15s)│                │ │
                     │  │                   └─────┬──────┘                │ │
                     │  └─────────────────────────┼───────────────────────┘ │
                     │                            │ queries                  │
                     │                    ┌───────▼────────┐                │
                     │                    │   Prometheus   │                │
                     │                    │  ─────────── │                │
                     │                    │  error_rate   │                │
                     │                    │  p99_latency  │                │
                     │                    └───────┬────────┘                │
                     │                            │ feeds                   │
                     │                    ┌───────▼────────┐                │
                     │                    │    Grafana     │ + Alertmanager │
                     │                    └────────────────┘                │
                     └───────────────────────────────────────────────────────┘
```

---

## 🛠 Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **App** | FastAPI (Python 3.12) | REST API with `/health`, `/metrics`, `/orders` endpoints |
| **Container** | Docker (multi-stage) | Hardened image, non-root user, Debian Bookworm base |
| **CI** | GitHub Actions | Test → Scan → Build → Push → Patch GitOps |
| **Image Registry** | GHCR (ghcr.io) | Private container registry |
| **Security** | Trivy | CVE scanning of container image on every build |
| **GitOps** | ArgoCD | Cluster continuously reconciled to Git state |
| **Deployment** | Argo Rollouts | Canary strategy with automated analysis |
| **Orchestration** | Kubernetes (kind) | Local 3-node cluster (1 control-plane, 2 workers) |
| **Metrics** | Prometheus + ServiceMonitor | Auto-scrapes app metrics via CRD |
| **Dashboards** | Grafana | Live canary health dashboard (auto-provisioned) |
| **Alerting** | Alertmanager | Fires on rollback events |
| **IaC** | Terraform | Kind cluster + Helm releases as code |

---

## 📁 Project Structure

```
selfhealing-platform/
├── app/                            # FastAPI microservice
│   ├── src/
│   │   └── main.py                 # App with metrics, health, failure injection
│   ├── tests/
│   │   └── test_main.py            # Pytest unit tests
│   ├── .github/
│   │   └── workflows/
│   │       └── ci.yml              # GitHub Actions: test→scan→push→gitops
│   ├── Dockerfile                  # Multi-stage, hardened, non-root
│   └── requirements.txt            # Pinned dependencies (CVE-clean)
│
├── gitops-config/                  # Separate GitOps repo (watched by ArgoCD)
│   ├── apps/
│   │   └── order-service/
│   │       ├── rollout.yaml        # Argo Rollouts canary strategy
│   │       ├── service.yaml        # Stable + canary services
│   │       ├── analysis-template.yaml  # PromQL-based auto-rollback brain
│   │       ├── servicemonitor.yaml # Prometheus scrape config
│   │       └── grafana-dashboard.yaml  # Auto-provisioned dashboard
│   └── argocd/
│       └── app.yaml                # ArgoCD Application CRD
│
├── infra-manifests/                # Infrastructure-level K8s resources
│   ├── alertmanager-config.yaml    # Rollback alert routing
│   ├── rollout-alert-rules.yaml    # PrometheusRule for AnalysisRun failures
│   └── argo-rollouts-servicemonitor.yaml
│
├── terraform/                      # IaC for full environment
│   ├── providers.tf                # kind + helm providers
│   ├── cluster.tf                  # Kind cluster definition
│   └── helm-releases.tf            # ArgoCD, Prometheus, Grafana, Rollouts
│
├── kind-cluster.yaml               # Kind cluster config (3 nodes, port mappings)
└── restart-portforwards.sh         # One-command port-forward restore
```

---

## ⭐ Key Features

### 1. Progressive Canary Delivery
The Argo Rollout uses a 5-step canary strategy:

```yaml
steps:
  - setWeight: 10    # 10% → analyze for 2 min
  - analysis: ...
  - setWeight: 25    # 25% → analyze for 2 min
  - analysis: ...
  - setWeight: 50    # 50% → analyze for 2 min
  - analysis: ...
  - setWeight: 100   # Promote to 100% only if all checks pass
```

At every step, an `AnalysisRun` runs Prometheus queries every 15 seconds. The canary **never progresses** unless metrics pass.

### 2. Prometheus-Driven Auto-Rollback (The Brain)

```yaml
# analysis-template.yaml — the self-healing core
failureCondition: "result[0] > 0.05"  # > 5% error rate → FAIL
query: |
  (1 - sum(rate(http_requests_total{status_code=~"2..",namespace="order-service"}[2m]))
       / sum(rate(http_requests_total{namespace="order-service"}[2m])))
  or vector(0)   # safe default: "no data" = 0% error rate, not a failure
```

**Why `failureCondition` over `successCondition`?** If `successCondition` uses `or vector(1)` as fallback (100% success), it masks real failures. Using `failureCondition` with `or vector(0)` means: "no data is safe; only explicit high error rates trigger rollback."

### 3. Multi-Layer Observability

- **Prometheus** auto-scrapes `/metrics` via `ServiceMonitor` CRD
- **Grafana** dashboard shows live canary vs stable success rate, request rate, and P99 latency
- **Alertmanager** fires a `RolloutAborted` alert with the failed revision and reason

### 4. Fully GitOps-Driven

Every deployment is a **git commit** to the config repo. No `kubectl apply` in production. ArgoCD auto-syncs within 3 minutes, or you can trigger manual sync. The cluster state is always an exact reflection of Git.

### 5. Hardened CI Pipeline

```
push to main
    │
    ├─── pytest ──────────────────── unit tests (conftest + fixtures)
    │
    ├─── trivy scan ──────────────── CVE scan (CRITICAL/HIGH fail build)
    │                                uploads SARIF to GitHub Security tab
    │
    ├─── docker build + push ─────── to ghcr.io (only if tests + scan pass)
    │
    └─── patch gitops repo ────────── updates image tag in rollout.yaml
                                      ArgoCD picks up → canary starts
```

---

## 🎬 Self-Healing Demo — Proven Results

### Setup

```bash
# Terminal 1 — watch the rollout live
kubectl argo rollouts get rollout order-service -n order-service --watch

# Terminal 2 — generate traffic
for i in $(seq 1 300); do curl -s http://localhost:8085/orders > /dev/null; sleep 0.3; done
```

### Inject the Broken Version

```bash
# Patch the rollout env to simulate a bad deploy (80% of requests return 500)
kubectl patch rollout order-service -n order-service --type=json -p='[
  {"op":"replace","path":"/spec/template/spec/containers/0/env/0/value","value":"1.1.0-bad"},
  {"op":"replace","path":"/spec/template/spec/containers/0/env/1/value","value":"0.8"}
]'
```

### Watch It Heal

```
14:34:15 — ✔ Healthy     Step 7/7 — v1.0.0 stable at 100%
14:34:27 — ◌ Progressing Step 1/7 — v1.1.0-bad canary at 10%
14:35:00 — ◌ Progressing           AnalysisRun running (✔ 2, ⚠ 1)
14:35:30 — ◌ Progressing           AnalysisRun running (✔ 3, ⚠ 2)
14:36:00 — ◌ Progressing           AnalysisRun running (✔ 3, ⚠ 3) ← failureLimit hit
14:36:10 — ✖ Degraded              RolloutAborted: "success-rate" failure limit exceeded
           Images: ghcr.io/pulkitt990/order-service:25d9c3c (stable)
           
✅ Zero manual action. Stable serving 100% traffic in < 3 minutes.
```

### Direct Canary Pod Verification

```
=== Canary pod (FAILURE_RATE=0.8) ===
Request 1: HTTP 500    Request 6: HTTP 500
Request 2: HTTP 500    Request 7: HTTP 500
Request 3: HTTP 500    Request 8: HTTP 500
Request 4: HTTP 500    Request 9: HTTP 500
Request 5: HTTP 500    Request 10: HTTP 500
→ Result: 10/10 FAILED
```

---

## 🚀 Getting Started

### Prerequisites

```bash
# Install required tools (macOS)
brew install kubectl kind helm argocd
brew install argoproj/tap/kubectl-argo-rollouts

# Install Docker Desktop (ARM64 for Apple Silicon)
# https://www.docker.com/products/docker-desktop/
```

### 1. Create the Kind Cluster

```bash
git clone https://github.com/pulkitt990/selfhealing-platform
cd selfhealing-platform

kind create cluster --config kind-cluster.yaml --name selfhealing
```

### 2. Install the Stack

```bash
# ArgoCD
kubectl create namespace argocd
helm repo add argo https://argoproj.github.io/argo-helm
helm install argocd argo/argo-cd -n argocd --wait

# Argo Rollouts
kubectl create namespace argo-rollouts
helm install argo-rollouts argo/argo-rollouts -n argo-rollouts \
  --set dashboard.enabled=true --wait

# Prometheus + Grafana (kube-prometheus-stack)
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus-stack prometheus-community/kube-prometheus-stack \
  -n monitoring --create-namespace \
  --set grafana.adminPassword=admin123 --wait
```

### 3. Bootstrap ArgoCD

```bash
# Apply ArgoCD Application pointing at gitops-config repo
kubectl apply -f gitops-config/argocd/app.yaml

# Get ArgoCD admin password
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath="{.data.password}" | base64 -d
```

### 4. Restore Port-Forwards

```bash
chmod +x restart-portforwards.sh
./restart-portforwards.sh
```

| UI | URL | Credentials |
|---|---|---|
| **ArgoCD** | http://127.0.0.1:9999 | `admin` / `<above password>` |
| **Grafana** | http://127.0.0.1:3000 | `admin` / `admin123` |
| **Prometheus** | http://127.0.0.1:9090 | none |
| **Alertmanager** | http://127.0.0.1:9093 | none |
| **Argo Rollouts** | http://127.0.0.1:3100 | none |
| **Order Service** | http://127.0.0.1:8085 | none |

### 5. Trigger the Self-Healing Demo

```bash
# Option A: Edit gitops-config (proper GitOps way)
# Edit gitops-config/apps/order-service/rollout.yaml:
#   FAILURE_RATE: "0.8"
# git commit + push → ArgoCD syncs → canary starts → rollback fires

# Option B: Direct patch (for quick demo)
kubectl patch rollout order-service -n order-service --type=json -p='[
  {"op":"replace","path":"/spec/template/spec/containers/0/env/1/value","value":"0.8"}
]'

# Watch the magic
kubectl argo rollouts get rollout order-service -n order-service --watch
```

---

## 🔬 How It Works — Deep Dive

### The AnalysisRun Loop

```
Every 15 seconds:
  1. Prometheus query fires → computes error_rate = 1 - (2xx / total)
  2. If error_rate > 0.05 (5%):
       failure counter += 1
  3. If failure counter > failureLimit (2):
       AnalysisRun → Phase: Failed
       Rollout controller detects failure
       Rollout → Phase: Aborted
       ReplicaSet: canary scaled to 0
       ReplicaSet: stable resumes 100% weight
       Alertmanager: fires RolloutAborted alert
```

### Why This PromQL is Correct

```promql
(
  1 - (
    sum(rate(http_requests_total{status_code=~"2..",namespace="order-service"}[2m]))
    /
    sum(rate(http_requests_total{namespace="order-service"}[2m]))
  )
) or vector(0)
```

- Computes the **error rate** (1 - success rate) as a fraction in [0, 1]
- `or vector(0)` means: if there's no traffic data yet, return 0 (don't fail)
- Paired with `failureCondition: result[0] > 0.05` — explicit failure, no ambiguity

### Failure Mode: `or vector(0)` vs `or vector(1)`

| Fallback | Behavior on no data | Risk |
|---|---|---|
| `or vector(1)` | "100% success" → passes | **Masks failures** if scrape hasn't started yet |
| `or vector(0)` | "0% error rate" → passes safely | Correct — new deploys start with clean slate |
| No fallback | Query returns empty → AnalysisRun errors | Causes `consecutiveErrors` abort, not a failure |

---

## ⚙️ CI/CD Pipeline

```yaml
# .github/workflows/ci.yml (simplified)
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - pytest --cov=src tests/

  scan:
    needs: test
    steps:
      - docker build -t $IMAGE .
      - trivy image --exit-code 1 --severity CRITICAL,HIGH $IMAGE
      - trivy image --format sarif → upload to GitHub Security

  publish:
    needs: scan
    if: github.ref == 'refs/heads/main'
    steps:
      - docker push ghcr.io/pulkitt990/order-service:$SHORT_SHA

  update-gitops:
    needs: publish
    steps:
      - git clone gitops-selfhealing-config
      - sed -i "s|image:.*|image: ghcr.io/pulkitt990/order-service:$SHORT_SHA|" rollout.yaml
      - git commit -m "ci: update image to $SHORT_SHA"
      - git push  # ← ArgoCD picks this up → canary starts
```

---

## 🔄 GitOps Workflow

```
Developer pushes code
        │
        ▼
GitHub Actions builds + scans + pushes image
        │
        ▼ (auto-patches image tag)
gitops-selfhealing-config repo gets a new commit
        │
        ▼ (ArgoCD polls every 3 min, or webhook)
ArgoCD detects drift: cluster ≠ git
        │
        ▼
ArgoCD applies new Rollout spec
        │
        ▼
Argo Rollouts starts canary at 10%
        │
     ┌──┴───────────────────────────┐
     │ Metrics OK?                   │
     │ YES → promote → 25% → ...   │ NO → abort → stable resumes
     └──────────────────────────────┘
```

**Key principle**: The GitOps config repo is the **single source of truth**. The cluster always converges to what's in Git. No manual `kubectl apply` in production.

---

## 📊 Observability Stack

### Grafana Dashboard: "Order Service — Canary Deployment Monitor"

Panels included:
- **Request Rate** (req/s) — stable vs canary
- **Error Rate (%)** — real-time, split by canary/stable
- **P99 Latency** (seconds)
- **Active Sessions**
- **Rollout Phase** — current step and weight

### PrometheusRule Alerts

| Alert | Condition | Severity |
|---|---|---|
| `RolloutAborted` | Rollout phase == Aborted | critical |
| `HighErrorRate` | error_rate > 10% for 2m | warning |
| `HighLatency` | p99 > 1s for 5m | warning |

### App Metrics (from `/metrics`)

```
http_requests_total{status_code, method, endpoint}  # counter
http_request_duration_seconds{endpoint}              # histogram (P50/P99/P999)
active_sessions_total                                # gauge
```

---

## 🏗 Infrastructure as Code

Full environment is reproducible via Terraform:

```bash
cd terraform/
terraform init
terraform plan
terraform apply  # Creates kind cluster + installs all helm charts
```

```hcl
# terraform/cluster.tf
resource "kind_cluster" "selfhealing" {
  name           = "selfhealing"
  wait_for_ready = true
  kind_config { ... }  # 3 nodes, port mappings
}

# terraform/helm-releases.tf
resource "helm_release" "argocd" { ... }
resource "helm_release" "argo_rollouts" { ... }
resource "helm_release" "prometheus_stack" { ... }
```

---

## 📝 Configuration Reference

### Failure Injection Parameters

| Env Var | Default | Description |
|---|---|---|
| `FAILURE_RATE` | `0.0` | Fraction of requests that return HTTP 500 (0.0–1.0) |
| `LATENCY_MS` | `0` | Extra artificial latency in milliseconds |
| `APP_VERSION` | `1.0.0` | Version string returned by `/health` |

### Analysis Thresholds

| Metric | Threshold | Logic |
|---|---|---|
| Error Rate | > 5% | `failureCondition: result[0] > 0.05` |
| P99 Latency | ≥ 2.0s | `failureCondition: result[0] >= 2.0` |
| Interval | 15s | Query frequency |
| Count | 8 | Total measurements per step |
| failureLimit | 2 | Consecutive failures before abort |

---

## 💡 Lessons Learned

### 1. `failureCondition` > `successCondition` for rollback
Using `successCondition` with a `vector(1)` fallback means "no data = success," which masks the exact failures you want to catch. Always use `failureCondition` with `vector(0)` for rollback metrics.

### 2. `imagePullPolicy: IfNotPresent` is mandatory for kind
Kind doesn't have access to private registries unless you `kind load docker-image`. Setting `imagePullPolicy: Always` causes `ImagePullBackOff`. Use `IfNotPresent` + `kind load` for local development.

### 3. Port-forward stability on macOS
`kubectl port-forward` on macOS with `--address 127.0.0.1` (loopback) is significantly more stable than `0.0.0.0` (all interfaces). Build a restart script and keep it handy.

### 4. ArgoCD and Argo Rollouts need matching port awareness
ArgoCD will sync the Rollout spec, but Argo Rollouts controller manages the actual pod lifecycle. If they're out of sync, use `argocd app sync order-service --force`.

### 5. PromQL division by zero on cold starts
New deployments start with zero traffic. A bare success-rate query returns NaN, which causes AnalysisRun `consecutiveErrors` (not failures). Always add `or vector(safe_value)` fallback.

---

## 🔮 What's Next

- [ ] **Slack/PagerDuty integration** — Alertmanager webhook for rollback notifications
- [ ] **Multi-cluster promotion** — dev → staging → prod with progressive delivery at each stage
- [ ] **Flagger** comparison — implement the same platform with Flagger and compare DX
- [ ] **KEDA** — event-driven autoscaling based on queue depth during canary
- [ ] **Chaos Engineering** — integrate Chaos Mesh to simulate node failures during canary
- [ ] **OPA/Gatekeeper** — policy enforcement: block deploys that skip the canary strategy
- [ ] **Cosign** — image signing and verification in the supply chain

---

## 👤 Author

**Pulkit** — B.Tech (DevOps specialization)

- GitHub: [@pulkitt990](https://github.com/pulkitt990)
- GitOps Config Repo: [gitops-selfhealing-config](https://github.com/pulkitt990/gitops-selfhealing-config)

---

<div align="center">

**⭐ If this project helped you understand GitOps + progressive delivery, give it a star!**

*Built to go beyond basic CI/CD into production-grade self-healing infrastructure.*

</div>
