# RunGuard

AI-powered DevOps/SRE incident remediation platform for Kubernetes. RunGuard compiles Markdown runbooks into machine-enforceable policies, investigates incidents from alerts, proposes safe remediation plans, and executes only approved actions with full audit trails.

## Architecture

```
Markdown Runbook
       │
       ▼
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│ Runbook Compiler │────▶│ Incident Reasoner │────▶│  Policy Engine  │
│  (parse → JSON)  │     │ (evidence → plan) │     │ (validate only) │
└─────────────────┘     └──────────────────┘     └────────┬────────┘
                                                          │
                                                          ▼
                                                 ┌─────────────────┐
                                                 │Remediation Exec  │
                                                 │(dry-run → apply) │
                                                 └─────────────────┘
```

### Four Layers

| Layer | Responsibility |
|-------|---------------|
| **Runbook Compiler** | Parses Markdown runbooks, extracts metadata, produces JSON policies |
| **Incident Reasoner** | Receives alerts, collects evidence (pod logs, events, deployment status), identifies root causes, generates remediation plans |
| **Policy Engine** | Validates actions against scope, blast radius, rollback path, IAM rules |
| **Remediation Executor** | Executes approved actions with dry-run and rollback support |

## Tech Stack

- **Backend:** Python 3.11+, FastAPI, Pydantic
- **AI:** Claude API (Anthropic)
- **Infrastructure:** Kubernetes (via `kubernetes` Python client)
- **Testing:** pytest, pytest-asyncio, pytest-cov

## Quick Start

### Prerequisites

- Python 3.11+
- pip

### Install

```bash
# Clone the repository
git clone https://github.com/your-org/runguard.git
cd runguard

# Install in editable mode with dev dependencies
pip install -e ".[dev]"
```

### Run the Server

```bash
uvicorn runguard.backend.main:app --reload
```

Server starts at `http://localhost:8000`. API docs at `http://localhost:8000/docs`.

### Run Tests

```bash
# All tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=runguard --cov-report=term-missing

# Specific module
pytest tests/compiler/ -v
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/runbooks` | Create/update runbook from Markdown |
| `GET` | `/runbooks` | List all runbooks |
| `POST` | `/incidents` | Create incident from alert |
| `GET` | `/incidents/{id}` | Get incident details |

### Example: Create a Runbook

```bash
curl -X POST http://localhost:8000/runbooks \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Pod CrashLoop Runbook",
    "content": "# Pod CrashLoop Runbook\n\n## Scope\n- Namespaces: default, staging\n- Workloads: web-app\n\n## Allowed Tools\n- rollout restart\n- scale deployment\n\n## Forbidden Tools\n- delete deployment\n\n## Severity\nhigh\n\n## Rollback Steps\n1. kubectl rollout undo deployment/{name} -n {namespace}"
  }'
```

### Example: Create an Incident

```bash
curl -X POST http://localhost:8000/incidents \
  -H "Content-Type: application/json" \
  -d '{
    "source": "prometheus",
    "severity": "high",
    "environment": "staging",
    "namespace": "default",
    "workload": "web-app",
    "raw_alert": "Pod CrashLoopBackOff for web-app"
  }'
```

## Project Structure

```
runguard/
├── backend/
│   ├── main.py              # FastAPI app entry point
│   ├── config.py            # App configuration
│   ├── api/
│   │   ├── incidents.py     # Incident routes
│   │   └── runbooks.py      # Runbook routes
│   ├── models/
│   │   ├── runbook.py       # Runbook data model
│   │   ├── policy.py        # Policy data model
│   │   ├── incident.py      # Incident data model
│   │   └── audit.py         # Audit record model
│   ├── compiler/
│   │   ├── parser.py        # Markdown parser
│   │   ├── extractor.py     # Metadata extractor
│   │   └── compiler.py      # Runbook → Policy compiler
│   ├── evidence/
│   │   ├── collector.py     # Evidence collection interface
│   │   └── kubernetes.py    # K8s evidence collector
│   ├── reasoning/
│   │   └── planner.py       # LLM-powered incident planner
│   └── audit/
│       └── store.py         # Audit trail storage
tests/                       # Full test suite (100% coverage)
runbooks/                    # Sample Markdown runbooks
specs/                       # Product specifications
```

## Sample Runbooks

The `runbooks/` directory contains ready-to-use runbooks:

- `pod-crashloop.md` — Restart/scale deployments on CrashLoopBackOff
- `image-pull-failure.md` — Handle ImagePullBackOff errors
- `readiness-probe-failure.md` — Fix readiness probe failures

## License

MIT
