# Phase 5 — Core Features

> 4 tính năng cốt lõi để RunGuard trở thành sản phẩm thực sự.
> Updated: 2026-05-08 — aligned with runguard-spec.md v1.0

---

## Feature 1: Claude AI Reasoning

**Mục đích:** Dùng Claude API phân tích incident → sinh root cause + remediation plan tự động.

### Files cần tạo/sửa

- `runguard/backend/ai/reasoner.py` — Claude API integration, prompt engineering
- `runguard/backend/ai/prompts.py` — System prompts cho incident analysis
- `runguard/backend/api/incidents.py` — Thêm endpoint `POST /incidents/{id}/analyze`
- `tests/ai/test_reasoner.py` — Unit tests với mocked Claude API

### Endpoint Spec: `POST /incidents/{id}/analyze`

**Valid states:** `pending`, `analyzing`. Nếu incident đã có plan (status = `requires_approval` hoặc sau) → return 400.

**Flow:**
- Nếu incident ở `pending` → tự động chạy Steps 2-3 (runbook compilation + evidence collection) trước khi gọi AI. Status: `pending` → `analyzing` → (AI) → `requires_approval` hoặc `resolved`.
- Nếu incident ở `analyzing` → Steps 2-3 đã hoàn thành (webhook flow). Chỉ chạy Step 4 (AI reasoning).
- Lý do `pending` là valid: manual incident được tạo qua `POST /incidents` nhưng evidence chưa được collect.

**Response 200 — analysis thành công (cần approval):**
```json
{
    "incident_id": "inc-abc123",
    "status": "requires_approval",
    "plan": {
        "id": "plan-xxx",
        "summary": "Pod CrashLoopBackOff caused by OOMKilled",
        "root_causes": [
            {"cause": "Container OOMKilled due to memory limit too low", "confidence": 0.92, "evidence": [...]}
        ],
        "actions": [
            {"id": "act-xxx", "name": "rollout_restart", "target": "my-app", "policy_decision": "requires_approval", ...}
        ]
    }
}
```

**Response 200 — tất cả actions auto-approved (tự trigger execution):**
```json
{
    "incident_id": "inc-abc123",
    "status": "resolved",
    "plan": { ... },
    "execution_results": [
        {"action_id": "act-xxx", "status": "completed", "output": "deployment/my-app restarted"}
    ]
}
```
Khi tất cả actions là auto-approved (`policy_decision=approved`), `/analyze` tự trigger execution pipeline nội bộ — không cần gọi `/execute` riêng. Incident → `resolved`.

**Error responses:**
- 400: incident không ở trạng thái đúng
- 500: Claude API lỗi → incident giữ nguyên `analyzing`, SRE có thể retry

### Audit Events

| Event | Khi nào |
|-------|----------|
| `plan_generated` | AI analysis thành công |
| `analysis_failed` | Claude API error/timeout |
| `action_validated` | Policy engine check mỗi action |
| `action_auto_approved` | Action auto-approved (low risk + rollback) |

### Key reuse

- `runguard/backend/compiler/parser.py` — Parse runbook sections
- `runguard/backend/models/plan.py` — `RemediationPlan`, `RemediationAction`, `RootCause`
- `runguard/backend/models/audit.py` — `AuditEventType`
- `anthropic` SDK (đã có trong dependencies)

### Config

| Variable | Default | Description |
|----------|---------|-------------|
| `RUNGUARD_ANTHROPIC_API_KEY` | — | Claude API key |
| `RUNGUARD_CLAUDE_MODEL` | `claude-sonnet-4-20250514` | Claude model |

Token budget: 10K input, 2K output. Timeout: 30s. Retry: 2 lần, exponential backoff (1s, 2s).

---

## Feature 2: Real K8s Actions

**Mục đích:** Thực sự chạy remediation actions trên K8s cluster (hiện tại chỉ có policy engine, chưa execute).

### Files cần tạo/sửa

- `runguard/backend/executor/k8s_actions.py` — K8s action executor
- `runguard/backend/executor/actions.py` — Action registry (restart, scale, update_image)
- `runguard/backend/api/incidents.py` — Thêm endpoint `POST /incidents/{id}/execute`
- `tests/executor/test_k8s_actions.py` — Unit tests với mocked K8s API

### Endpoint Spec: `POST /incidents/{id}/execute`

**Valid states:** `approved`. Nếu incident ở trạng thái khác → return 400.

**Behavior:**
- Execute **tuần tự** theo thứ tự actions trong plan (không song song — tránh blast radius chồng chéo).
- Nếu action #2 fail → **vẫn tiếp tục** execute action #3. Mỗi action có thể độc lập.
- Nếu **bất kỳ** action nào fail → incident status = `failed` (không rollback tự động).
- Nếu **tất cả** thành công → incident status = `resolved`.
- Execute chỉ các actions có `status=approved`. Blocked/pending actions bị skip.

**Response 200 — tất cả thành công:**
```json
{
    "incident_id": "inc-abc123",
    "status": "resolved",
    "results": [
        {"action_id": "act-xxx", "name": "rollout_restart", "status": "completed", "output": "deployment/my-app restarted"},
        {"action_id": "act-yyy", "name": "scale_replicas", "status": "completed", "output": "deployment/my-app scaled to 3 replicas"}
    ]
}
```

**Response 207 (Multi-Status) — partial failure:**
```json
{
    "incident_id": "inc-abc123",
    "status": "failed",
    "results": [
        {"action_id": "act-xxx", "name": "rollout_restart", "status": "completed", "output": "..."},
        {"action_id": "act-yyy", "name": "scale_replicas", "status": "failed", "error": "deployment not found"}
    ]
}
```
Client **phải** parse `results[]` để biết action nào fail.

**HTTP status codes:**
- `200` — tất cả thành công (incident → `resolved`)
- `207 Multi-Status` — partial failure
- `400` — incident không ở trạng thái `approved`
- `500` — system error

### Execution Modes

| Mode | Env var | Behavior |
|------|---------|----------|
| **Direct** (default) | `RUNGUARD_GITOPS_ENABLED=false` | Execute K8s actions trực tiếp qua K8s API |
| **GitOps** | `RUNGUARD_GITOPS_ENABLED=true` | Commit YAML patch vào git repo. Flux/ArgoCD tự apply. **Không direct execute K8s API** — tránh race condition. |

Cả hai mode đều support dry-run mode (chỉ log, không execute).

### Supported Actions

| Action | K8s API | Description |
|--------|---------|-------------|
| `rollout_restart` | `kubectl rollout restart` | Restart pods |
| `scale_replicas` | `patch deployment.spec.replicas` | Scale up/down |
| `update_image` | `patch container.image` | Update container image |
| `delete_pod` | `delete pod` | Delete specific pod |

### Safety

- Luôn chạy qua `PolicyEngine.validate_action()` trước
- Dry-run mode: chỉ log, không execute
- Audit mọi action qua `AuditStore`
- Namespace isolation — chỉ action trong namespace cho phép

### Audit Events

| Event | Khi nào |
|-------|----------|
| `execution_started` | `POST /execute` gọi, incident → `executing` |
| `action_executed` | Action thực thi thành công |
| `action_failed` | Action thực thi thất bại |
| `gitops_commit` | GitOps commit created (GitOps mode only) |

### Key reuse

- `runguard/backend/policy/engine.py` — Policy validation
- `runguard/backend/audit/store.py` — Audit logging
- `runguard/backend/gitops/reconciler.py` — GitOps commit (Phase 4 đã có)
- `kubernetes` SDK (đã có trong dependencies)

---

## Feature 3: Alert Webhook

**Mục đích:** Nhận alert từ Prometheus/Alertmanager webhook → tự động tạo incident.

### Files cần tạo/sửa

- `runguard/backend/api/webhooks.py` — Webhook endpoints
- `runguard/backend/webhooks/alertmanager.py` — Parse Alertmanager payload
- `runguard/backend/webhooks/prometheus.py` — Parse Prometheus alert format
- `runguard/backend/webhooks/base.py` — Base webhook parser interface
- `tests/webhooks/test_alertmanager.py` — Unit tests

### Endpoints

```
POST /webhooks/alertmanager  — Alertmanager webhook receiver
POST /webhooks/prometheus    — Prometheus alert receiver
POST /webhooks/generic       — Generic webhook (custom format)
```

**Auth:** Bearer token (`Authorization: Bearer {secret}`), verified against `RUNGUARD_WEBHOOK_SECRET` env var.

### Flow

```
Alertmanager → POST /webhooks/alertmanager
  → Parse payload (status, labels, annotations)
  → Map severity, namespace, workload
  → Tạo incident (status=pending, runbook_id=null)
  → Step 1.5: Auto-match runbook bằng namespace + workload
    → Nếu match: set runbook_id, tiếp tục
    → Nếu không match: set status=failed, audit log "No matching runbook found"
  → Nếu severity=critical → gọi auto-analyze
  → Return 200 OK
```

**Step 1.5 — Runbook Matching (webhook only):**
- Auto-match runbook bằng `namespace` + `workload` từ alert labels.
- Match criteria: runbook scope.namespaces chứa incident namespace **VÀ** scope.workloads chứa incident workload (hoặc workload = `*`).
- Tie-breaking: workload specificity → most recently created → log warning.
- Nếu match thất bại → `status=failed`, incident không tiếp tục pipeline.
- `runbook_id` được set **trước** khi runbook compilation.

### Alertmanager Payload Format

```json
{
  "alerts": [
    {
      "status": "firing",
      "labels": {
        "alertname": "PodCrashLooping",
        "namespace": "default",
        "pod": "my-app-xxx",
        "severity": "critical"
      },
      "annotations": {
        "summary": "Pod is crash looping",
        "description": "Pod my-app has restarted 5 times in 10 minutes"
      }
    }
  ]
}
```

### Key reuse

- `runguard/backend/api/incidents.py` — Incident creation
- `runguard/backend/compiler/` — Runbook matching logic

### Config

| Variable | Default | Description |
|----------|---------|-------------|
| `RUNGUARD_WEBHOOK_SECRET` | — | Bearer token for webhook auth |

---

## Feature 4: Slack Notifications

**Mục đích:** Gửi thông báo Slack khi incident tạo/xử lý xong.

### Files cần tạo/sửa

- `runguard/backend/notifications/slack.py` — Slack API integration
- `runguard/backend/notifications/base.py` — Notification interface
- `tests/notifications/test_slack.py` — Unit tests với mocked Slack API

### Events → Notifications

| Event | Slack Message |
|-------|--------------|
| Incident created | 🔴 New incident: {id} — {workload} ({severity}) |
| Approval required | ⚠️ Approval needed: {id} — {action} |
| Action executed | ✅ Action executed: {id} — {action} |
| Action failed | ❌ Action failed: {id} — {action}: {error} |
| Resolved | 🟢 Resolved: {id} — {summary} |

### Notification Strategy

**Per-action notification** (MVP): mỗi action execution gửi 1 Slack message. Nếu incident có 5 actions → 5 messages. Future: batch mode (gom tất cả actions thành 1 summary message sau khi execute xong).

### Rate Limiting

Slack Incoming Webhook giới hạn 1 message/second per webhook. Executor xử lý:
- Minimum **100ms delay** giữa các Slack notifications
- Nếu bị rate limit (HTTP 429): retry với exponential backoff (1s, 2s, 4s) — tối đa 3 lần
- Nếu vẫn fail → log warning, **tiếp tục execute actions** (không block pipeline vì notification failure)

### Config

| Variable | Default | Description |
|----------|---------|-------------|
| `RUNGUARD_SLACK_WEBHOOK_URL` | — | Slack incoming webhook URL |

### Key reuse

- `httpx` (đã có trong dependencies) — HTTP client
- Slack Incoming Webhook (không cần Slack SDK)

---

## Implementation Order

```
1. Alert Webhook      (standalone, không depend feature khác)
2. Claude AI Reasoning (depend trên incident model)
3. Real K8s Actions   (depend trên policy engine)
4. Slack Notifications (depend trên event system, nên làm cuối)
```

**Lý do:** Alert Webhook là entry point cho automated flow. Claude AI cần webhook tạo incident trước. K8s Actions cần AI sinh plan trước. Slack cần tất cả events từ các feature trên.

---

## New Models (đã implement trong Phase 4)

Phase 5 cần các models đã được tạo:

| Model | File | Purpose |
|-------|------|---------|
| `RemediationPlan` | `runguard/backend/models/plan.py` | Plan + root causes + actions |
| `RemediationAction` | `runguard/backend/models/plan.py` | Single action trong plan |
| `RootCause` | `runguard/backend/models/plan.py` | Root cause với confidence + evidence |
| `ActionStatus` | `runguard/backend/models/plan.py` | Enum: pending, approved, blocked, executing, completed, failed |
| `PolicyDecision` | `runguard/backend/models/plan.py` | Enum: approved, requires_approval, blocked |
| `AuditEventType` | `runguard/backend/models/audit.py` | Bao gồm: execution_started, gitops_commit |

---

## Dependencies mới

```toml
# pyproject.toml — thêm vào nếu cần
# anthropic đã có
# kubernetes đã có
# httpx đã có
# Không cần thêm dependency mới
```

---

## Environment Variables mới

| Variable | Default | Description |
|----------|---------|-------------|
| `RUNGUARD_ANTHROPIC_API_KEY` | — | Claude API key (Feature 1) |
| `RUNGUARD_CLAUDE_MODEL` | `claude-sonnet-4-20250514` | Claude model (Feature 1) |
| `RUNGUARD_K8S_MOCK` | `false` | Mock K8s API for local dev (Feature 2/3) |
| `RUNGUARD_GITOPS_ENABLED` | `false` | Enable GitOps mode (Feature 2) |
| `RUNGUARD_GITOPS_REPO_PATH` | — | Git repo path for GitOps (Feature 2) |
| `RUNGUARD_WEBHOOK_SECRET` | — | Bearer token for webhook auth (Feature 3) |
| `RUNGUARD_SLACK_WEBHOOK_URL` | — | Slack incoming webhook (Feature 4) |

---

## Verification

```bash
# Tests
pytest tests/ai/ tests/executor/ tests/webhooks/ tests/notifications/ -v

# Smoke test webhook
curl -X POST http://localhost:8000/webhooks/alertmanager \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${RUNGUARD_WEBHOOK_SECRET}" \
  -d '{"alerts":[{"status":"firing","labels":{"alertname":"Test","namespace":"default","severity":"high"},"annotations":{"summary":"Test alert"}}]}'

# Smoke test AI
curl -X POST http://localhost:8000/incidents/{id}/analyze \
  -H "X-API-Key: ${RUNGUARD_API_KEY}"

# Smoke test execute
curl -X POST http://localhost:8000/incidents/{id}/execute \
  -H "X-API-Key: ${RUNGUARD_API_KEY}"

# Smoke test with K8s mock (local dev)
RUNGUARD_K8S_MOCK=true uvicorn runguard.backend.main:app --reload
```

---

## Approve → Execute Flow (2 bước)

Phase 5 implement đầy đủ flow 2 bước:

1. **Approve** (`POST /approve` hoặc `POST /actions/{id}/approve`) — chỉ set action `status=approved`, incident → `approved`. **Không execute.**
2. **Execute** (`POST /execute`) — trigger execution. Incident → `executing` → `resolved` hoặc `failed`.

**Exception:** Khi `/analyze` phát hiện tất cả actions là auto-approved, nó tự trigger execution — không cần gọi `/execute` riêng.

**Per-action approve:** Dùng khi SRE muốn approve từng action thay vì bulk. Khi tất cả `requires_approval` actions đã approve → incident tự chuyển `approved` (synchronous check trong handler).
