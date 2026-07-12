# RunGuard

AI-powered DevOps/SRE incident remediation platform for Kubernetes. RunGuard compiles Markdown runbooks into machine-enforceable policies, investigates incidents using LLM reasoning, proposes safe remediation plans, and executes only approved actions with full audit trails.

## Architecture

```
Alertmanager Webhook
        │
        ▼
┌───────────────┐    ┌─────────────┐    ┌──────────────┐    ┌───────────────┐
│  API Gateway  │───▶│   Backend   │◀───│    Worker    │◀───│     NATS      │
│  (Go, :8080)  │    │  (Go, :8081)│    │  (Go, NATS) │    │   JetStream   │
└───────────────┘    └──────┬──────┘    └──────────────┘    └───────────────┘
                            │
              ┌─────────────┼─────────────┐
              ▼             ▼             ▼
       ┌─────────┐  ┌──────────────┐  ┌──────────────┐
       │Operator │  │   Reasoner   │  │   Web UI     │
       │(Go,:9090)│  │(Python,:8082)│  │(React, :3000)│
       └────┬────┘  └──────────────┘  └──────────────┘
            │
    ┌───────┼───────┐
    ▼       ▼       ▼
Compiler  Policy  Executor
```

### Four Layers

| Layer | Service | Responsibility |
|-------|---------|----------------|
| **Runbook Compiler** | `operator` | Parses Markdown runbooks, extracts scope/tools/rollback steps, produces typed policies |
| **Incident Reasoner** | `reasoner` | Calls Claude API with alert + evidence, returns root cause, confidence score, and recommended actions |
| **Policy Engine** | `operator` | Validates actions against scope, blast radius, rollback path, environment, and auto-approval limits |
| **Remediation Executor** | `operator` | Executes approved actions (restart, scale, rollback) in dry-run or live mode with automatic rollback on failure |

## Services

| Service | Language | Port | Description |
|---------|----------|------|-------------|
| `api-gateway` | Go | 8080 | Reverse proxy (`/v1/*` → `/api/*`) with service-token auth and rate limiting |
| `backend` | Go | 8081 | Core REST API — incidents, runbooks, approvals, audit trail. Backed by Postgres + Redis |
| `operator` | Go | 9090 | Alertmanager webhook receiver, reconciler loop, runbook compiler, policy engine, executor |
| `worker` | Go | — | NATS JetStream subscriber — receives `incidents.new` events, forwards to backend |
| `reasoner` | Python | 8082 | FastAPI service wrapping Anthropic Claude for incident analysis |
| `web-ui` | TypeScript | 3000 | React SPA — incident list, detail, approve/reject workflow, runbook management |

## Tech Stack

- **Backend services:** Go 1.25, standard `net/http`, Chi router (api-gateway)
- **Reasoner:** Python 3.14, FastAPI, Anthropic SDK (`claude-sonnet-4-20250514`)
- **Frontend:** React 18, TypeScript, Vite, React Router
- **Messaging:** NATS 2 with JetStream
- **Storage:** PostgreSQL 18, Redis 8
- **Observability:** OpenTelemetry tracing, Prometheus metrics, structured `slog` logging
- **Infrastructure:** Kubernetes, Helm, ArgoCD, kind (local), NATS, cert-manager
- **Security:** Cosign keyless signing, Trivy, CodeQL, Semgrep, TruffleHog, SBOM generation
- **CI/CD:** GitHub Actions (lint → test → security → build → release → ArgoCD deploy)

## Quick Start

### Prerequisites

- Docker and Docker Compose
- `ANTHROPIC_API_KEY` for the reasoner service

### Run with Docker Compose

```bash
git clone https://github.com/phuoctmse/runguard.git
cd runguard

# Copy and configure environment
cp .env.example .env
# Edit .env and set ANTHROPIC_API_KEY

# Start all services
docker compose up -d

# Verify all services are healthy
docker compose ps
```

| Service | URL |
|---------|-----|
| Web UI | http://localhost:3000 |
| API Gateway | http://localhost:8080 |
| Backend API | http://localhost:8081 |
| Reasoner | http://localhost:8082 |
| Operator | http://localhost:9090 |

### Local Go Development

```bash
# Requires Go 1.25+

# Build all Go services
make build

# Run tests across all modules
go test ./services/... ./shared/... -v

# Run a specific service
cd services/backend && go run ./cmd/main.go
```

### Local Python Development

```bash
cd services/reasoner

# Install with dev dependencies
pip install -e ".[dev]"

# Run tests with coverage
pytest tests/ -v --cov=reasoner --cov-report=term-missing

# Start the reasoner service
uvicorn reasoner.main:app --reload --port 8082
```

## API Reference

All public endpoints are available through the API Gateway at `:8080/v1/`.

### Incidents

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/v1/incidents` | List all incidents |
| `POST` | `/v1/incidents` | Create an incident from an alert |
| `GET` | `/v1/incidents/{id}` | Get incident details |
| `POST` | `/v1/incidents/{id}/approve` | Approve a pending remediation plan |
| `POST` | `/v1/incidents/{id}/reject` | Reject a pending remediation plan |

### Runbooks

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/v1/runbooks` | List compiled runbooks |
| `POST` | `/v1/runbooks` | Create/update a runbook from Markdown |

### Audit

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/v1/audit/{incident_id}` | Get immutable audit trail for an incident |

### Health & Metrics (per service, direct)

| Path | Description |
|------|-------------|
| `/healthz` | Liveness probe |
| `/readyz` | Readiness probe |
| `/metrics` | Prometheus metrics |

### Incident Lifecycle

```
pending → analyzing → requires_approval → executing → resolved
                                        ↘             ↘
                                         rejected      failed
```

Approval requests auto-expire to `rejected` after 30 minutes if no human action.

### Example: Create an Incident

```bash
curl -X POST http://localhost:8080/v1/incidents \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "alertName": "PodCrashLooping",
    "severity": "critical",
    "namespace": "default",
    "workload": "web-app"
  }'
```

### Example: Alertmanager Webhook (Operator)

Send alerts directly to the operator webhook (bypassing the gateway):

```bash
curl -X POST http://localhost:9090/webhook/alertmanager \
  -H "Content-Type: application/json" \
  -d '{
    "alerts": [{
      "labels": {
        "alertname": "PodCrashLooping",
        "severity": "critical",
        "namespace": "default",
        "workload": "web-app"
      }
    }]
  }'
```

## Runbook Format

Runbooks are Markdown files that the compiler parses into structured policies. The compiler validates that a `## Rollback` section exists before accepting a runbook.

```markdown
# Pod CrashLoop Runbook

## Scope
- Namespaces: default, staging
- Resources: web-app, api

## Severity
high, critical

## Allowed Tools
- rollout_restart
- scale_replicas
- fetch_logs

## Forbidden Tools
- delete_pod
- delete_deployment

## Diagnosis

### check_logs
```bash
kubectl logs {{.PodName}} -n {{.Namespace}} --tail=100
```

## Remediation

### restart_deployment
- Action: restart
- Target: {{.PodName}}
- Risk: low
- AutoApprove: true

## Rollback

### undo_restart
- Action: rollback
- Target: {{.PodName}}
- Risk: low
```

See `runbooks/` for ready-to-use examples:

- `pod-crashloop.md` — CrashLoopBackOff restarts and scaling
- `image-pull-failure.md` — ImagePullBackOff diagnosis and remediation
- `readiness-probe-failure.md` — Readiness probe failures and scaling

## Project Structure

```
runguard/
├── services/
│   ├── api-gateway/         # Go reverse proxy + rate limiting
│   ├── backend/             # Go REST API (incidents, runbooks, audit, approvals)
│   ├── operator/            # Go operator: compiler + policy engine + executor
│   │   └── internal/
│   │       ├── compiler/    # Markdown → policy parser
│   │       ├── controller/  # Reconciler loop
│   │       ├── evidence/    # K8s evidence collection
│   │       ├── executor/    # Action executor with rollback
│   │       ├── policy/      # Policy engine (scope, blast radius, env checks)
│   │       └── webhook/     # Alertmanager webhook parser
│   ├── worker/              # Go NATS subscriber
│   ├── reasoner/            # Python FastAPI + Claude API client
│   └── web-ui/              # React/TypeScript SPA
├── shared/                  # Shared Go libraries
│   ├── errors/              # HTTP error helpers
│   ├── health/              # Liveness/readiness handlers
│   ├── logger/              # Structured slog wrapper
│   ├── metrics/             # Prometheus middleware
│   ├── middleware/          # Service auth middleware
│   ├── resilience/          # Retry / circuit breaker patterns
│   ├── server/              # Graceful HTTP server
│   ├── tracing/             # OpenTelemetry tracer setup
│   └── types/               # Shared domain types (Incident, Policy, Runbook, etc.)
├── infra/
│   ├── k8s/                 # Raw Kubernetes manifests
│   └── runguard/            # Helm chart
├── runbooks/                # Sample Markdown runbooks
├── specs/                   # Product specifications
├── docs/                    # Architecture and planning docs
├── docker-compose.yml       # Local full-stack environment
└── go.work                  # Go workspace (13 modules)
```

## Safety Guardrails

All remediation actions pass through the policy engine before execution:

1. **Forbidden list** — actions on the runbook's forbidden list are blocked unconditionally
2. **Blast radius** — delete actions are blocked when `forbidDelete` is set in the policy
3. **Scope check** — actions outside the allowed namespaces/resources are blocked
4. **Rollback required** — actions without a matching rollback step are blocked
5. **Environment gate** — any action targeting a `production` environment requires human approval
6. **Auto-approval limit** — exceeding `maxAutoApproved` per incident escalates remaining actions to `RequiresApproval`
7. **Fail-safe** — a panic in the policy engine blocks all actions rather than allowing them through

## Kubernetes Deployment

### Local cluster (kind)

```bash
# Create a kind cluster
kind create cluster --config infra/kind-config.yaml

# Install via Helm
helm install runguard infra/runguard \
  --namespace runguard \
  --create-namespace \
  --set reasoner.anthropicApiKey=<your-key>
```

### GitOps (ArgoCD)

ArgoCD application definitions are in `infra/k8s/argocd/`. The release pipeline automatically syncs `runguard-staging` on tag push and requires a GitHub Environment approval gate for `runguard-prod`.

## CI/CD

| Workflow | Trigger | Jobs |
|----------|---------|------|
| `ci.yml` | PR + push to `v2`/`main` | Go lint → Go test → Python lint → Python test → security scan (govulncheck + pip-audit + TruffleHog) → build |
| `release.yml` | `v*` tag | Cross-platform builds (linux/darwin/windows × amd64/arm64) → Docker push to GHCR → Trivy scan → Cosign signing + SBOM → GitHub Release → ArgoCD deploy (staging auto, prod manual) |
| `security.yml` | Weekly + PRs | CodeQL (Go + Python) → Semgrep → Go supply chain → Python supply chain → Trivy container scans with SARIF upload |

## License

MIT
