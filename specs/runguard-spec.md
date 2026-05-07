# RunGuard — Complete Product Specification

> AI-powered incident remediation platform for Kubernetes and AWS.
> Version: 1.0 — Updated 2026-05-07

---

## 1. What is RunGuard?

RunGuard là một **AI SRE assistant** — nhận alert từ monitoring systems, phân tích root cause, đề xuất remediation plan, và execute actions sau khi được approve.

**Tóm tắt 1 dòng:**
```
Alert → Incident → Evidence → AI Analysis → Policy Check → Approval → Execute → Audit → Notify
```

**Giá trị cốt lõi:**
- 3AM alert → RunGuard đã phân tích xong, SRE chỉ cần approve 1 click
- Mọi action đều qua policy check — không thể chạy lệnh nguy hiểm
- Full audit trail — ai làm gì, khi nào, tại sao

---

## 2. Who Uses It?

| Vai trò | Sử dụng | Giá trị |
|---------|---------|---------|
| **SRE/DevOps on-call** | Approve/reject remediation actions | Ngủ ngon hơn, chỉ approve khi cần |
| **Platform Engineer** | Viết runbooks, định nghĩa policies | Tiêu chuẩn hóa incident handling |
| **Engineering Manager** | Xem dashboard, audit trail | Visibility vào incident response |

---

## 3. How It Works — End-to-End Flow

### 3.1 The Big Picture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ Prometheus   │     │ Grafana     │     │ AWS         │
│ Alertmanager │     │ Alerting    │     │ CloudWatch  │
└──────┬───────┘     └──────┬──────┘     └──────┬──────┘
       │                    │                    │
       └────────────────────┼────────────────────┘
                            │ Webhook
                            ▼
                   ┌─────────────────┐
                   │   RunGuard API  │
                   │   (FastAPI)     │
                   └────────┬────────┘
                            │
              ┌─────────────┼─────────────┐
              ▼             ▼             ▼
       ┌───────────┐ ┌───────────┐ ┌───────────┐
       │ Runbook   │ │ Evidence  │ │ Claude AI │
       │ Compiler  │ │ Collector │ │ Reasoning │
       └─────┬─────┘ └─────┬─────┘ └─────┬─────┘
             │             │             │
             └─────────────┼─────────────┘
                           ▼
                   ┌─────────────────┐
                   │  Policy Engine  │
                   │  (validate)     │
                   └────────┬────────┘
                            │
                   ┌────────┴────────┐
                   ▼                 ▼
            ┌──────────┐     ┌──────────┐
            │ Auto     │     │ Human    │
            │ Execute  │     │ Approval │
            └────┬─────┘     └────┬─────┘
                 │                │
                 └────────┬───────┘
                          ▼
                   ┌─────────────────┐
                   │  K8s Cluster    │
                   │  (apply fix)    │
                   └────────┬────────┘
                            │
                          ▼
                   ┌─────────────────┐
                   │  Audit Store    │
                   │  + Slack Notify │
                   └─────────────────┘
```

### 3.2 Step-by-Step

**Step 1 — Intake: Alert đến**
- Prometheus/Alertmanager gửi webhook → `POST /webhooks/alertmanager`
- Hoặc người dùng tạo manual → `POST /incidents`
- Tạo incident, status = `pending`

**Step 1.5 — Runbook Matching (webhook only)**
- Webhook incidents: ngay sau khi tạo incident (Step 1), hệ thống auto-match runbook bằng `namespace` + `workload` từ alert labels.
- **Nếu match thành công:** set `runbook_id` vào incident record, tiếp tục Step 2.
- **Nếu match thất bại:** set `status=failed`, audit log ghi `"No matching runbook found"`. Incident không tiếp tục pipeline.
- **Timing:** `runbook_id` được set **trước** khi runbook compilation (Step 2). Step 2 chỉ parse Markdown và sinh Policy — không thực hiện matching.
- Manual incidents: client gửi `runbook_id` trong request body (bắt buộc). Nếu thiếu → API return 400 error, incident không được tạo.

**Step 2 — Runbook Compilation**
- **Runbook Selection:**
  - Manual incident (`POST /incidents`): `runbook_id` đã có sẵn từ request body.
  - Webhook incident (`POST /webhooks/*`): `runbook_id` đã được set ở Step 1.5.
  - Match criteria: runbook scope.namespaces chứa incident namespace **VÀ** scope.workloads chứa incident workload (hoặc workload = `*`).
  - **Tie-breaking (nhiều runbooks match):** Ưu tiên theo thứ tự:
    1. **Workload specificity:** runbook match workload cụ thể (e.g. `web-app`) thắng runbook match wildcard (`*`).
    2. **Most recently created:** Nếu cùng specificity → dùng runbook được tạo gần nhất (`created_at` mới nhất).
    3. Log warning: `"Multiple runbooks matched for incident {id}, selected {runbook_id} (matched {n} runbooks)"`.
- Đọc Markdown runbook → parse sections
- Trích xuất: scope, allowed tools, forbidden tools, severity, rollback steps
- Sinh Policy object (JSON)

**Step 3 — Evidence Collection**
- `KubernetesEvidenceCollector` thu thập:
  - Pod logs (`collect_pod_logs`)
  - K8s events (`collect_events`)
  - Deployment status (`collect_deployment_status`)
- Chạy song song qua `asyncio.gather`

**Step 4 — AI Reasoning** (Phase 5)
- Gọi Claude API với: raw_alert + evidence + runbook context
- Trả về: root causes (confidence score), remediation actions, summary
- Status → `requires_approval`

**Step 5 — Policy Validation**
- `PolicyEngine.validate_action()` kiểm tra mỗi action theo thứ tự first-match (xem Section 12.3 để biết chi tiết):
  1. Forbidden? → `blocked`
  2. Not in allowed list? → `blocked`
  3. Namespace ngoài scope? → `blocked`
  4. IAM permissions thiếu? → `blocked`
  5. Production env? → `requires_approval`
  6. Blast radius medium/high? → `requires_approval`
  7. Không có rollback path? → `requires_approval`
  8. Đã đạt 5 auto-approved actions? → `requires_approval`
  9. Low risk (blast_radius=low) + có rollback + chưa đạt limit? → `approved`

**Step 6 — Approval**
- `approved` → execute ngay
- `requires_approval` → chờ SRE approve qua UI hoặc API
- `blocked` → không execute

**Step 7 — Execution** (Phase 5)
- **Direct mode** (`RUNGUARD_GITOPS_ENABLED=false`, default): execute K8s actions trực tiếp qua K8s API — `rollout_restart`, `scale_replicas`, `update_image`.
- **GitOps mode** (`RUNGUARD_GITOPS_ENABLED=true`): commit YAML patch vào git repo. Flux/ArgoCD tự apply từ git. **Không direct execute K8s API** — tránh race condition giữa RunGuard và GitOps controller.
- Dry-run mode: chỉ log, không execute (áp dụng cho cả direct và GitOps mode).

**Step 8 — Audit**
- Mỗi bước đều ghi `AuditRecord` vào `AuditStore`
- Immutable — không thể sửa/xóa
- API: `GET /audit/{incident_id}`

**Step 9 — Notify** (Phase 5)
- Slack notification cho mỗi event quan trọng

---

## 4. Architecture

### 4.1 Module Map

```
runguard/
├── backend/
│   ├── main.py                    # FastAPI app entry
│   ├── config.py                  # Settings (env vars)
│   ├── api/
│   │   ├── incidents.py           # CRUD incidents
│   │   ├── runbooks.py            # CRUD runbooks
│   │   ├── workflow.py            # Approve/reject
│   │   ├── audit.py               # Audit trail query
│   │   └── webhooks.py            # [Phase 5] Alert webhooks
│   ├── compiler/
│   │   ├── parser.py              # Markdown → sections
│   │   └── extractor.py           # Sections → Policy
│   ├── evidence/
│   │   └── kubernetes.py          # K8s evidence collector
│   ├── policy/
│   │   └── engine.py              # Policy validation
│   ├── workflow/
│   │   ├── approval.py            # Human approval workflow
│   │   └── rollback.py            # Rollback execution
│   ├── executor/
│   │   └── k8s_actions.py         # [Phase 5] K8s action executor
│   ├── webhooks/
│   │   ├── alertmanager.py        # [Phase 5] Alertmanager parser
│   │   ├── prometheus.py          # [Phase 5] Prometheus parser
│   │   └── base.py                # [Phase 5] Base parser interface
│   ├── ai/
│   │   └── reasoner.py            # [Phase 5] Claude AI reasoning
│   ├── notifications/
│   │   └── slack.py               # [Phase 5] Slack notifications
│   ├── audit/
│   │   └── store.py               # JSON file-based audit store
│   └── models/
│       ├── runbook.py             # Runbook model
│       ├── policy.py              # Policy model
│       ├── incident.py            # Incident model
│       ├── plan.py                # RemediationPlan, RemediationAction models
│       └── audit.py               # AuditRecord model
├── mcp/                           # MCP server
│   ├── server.py                  # MCP server with policy enforcement
│   ├── tools.py                   # K8s + AWS tool implementations
│   └── models.py                  # ToolDefinition, ToolCall, ToolResult
├── gitops/                        # GitOps reconciler
│   ├── reconciler.py              # Git commit for K8s changes
│   └── models.py                  # ManifestPatch, GitOpsCommit
├── cost/                          # Cost tracking
│   ├── tracker.py                 # AWS Cost Explorer + OpenCost
│   └── models.py                  # CostEntry, NamespaceCost
├── ui/                            # Streamlit dashboard
│   ├── app.py                     # Main entry point
│   ├── pages.py                   # Page components
│   └── components.py              # Reusable UI components
└── aws/
    └── ssm_executor.py            # AWS SSM document trigger
```

### 4.2 Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11+, FastAPI, Pydantic |
| AI | Claude API (Anthropic) |
| K8s Client | `kubernetes` Python SDK |
| AWS | `boto3` (SSM, CloudWatch, Cost Explorer) |
| UI | Streamlit |
| Policy | Custom Pydantic-based engine |
| GitOps | subprocess git + JSON manifests |
| Audit | JSON file-based store |
| MCP | Custom MCP server implementation |
| Tests | pytest, pytest-asyncio, pytest-cov |
| Lint | ruff (format + check), mypy |

---

## 5. Current Status

### 5.1 Phases Completed

| Phase | Status | Features |
|-------|--------|----------|
| Phase 1 — Core | ✅ Done | Runbook compiler, K8s evidence collector, basic plan, audit log |
| Phase 2 — Safety | ✅ Done | Policy engine, approval workflow, rollback support |
| Phase 3 — AWS | ✅ Done | EventBridge, Lambda, DynamoDB, SSM, CloudWatch |
| Phase 4 — Polish | ✅ Done | MCP server, GitOps reconciler, cost tracking, Streamlit UI |
| Phase 5 — Features | ❌ Planned | Claude AI reasoning, K8s execution, alert webhooks, Slack |

### 5.2 Test Coverage

- **243 tests passing**
- **Coverage: 85%**
- ruff clean, mypy clean

### 5.3 Infrastructure

- Docker + docker-compose (FastAPI + Streamlit)
- kind cluster for local K8s deployment
- K8s manifests in `infra/k8s/`

---

## 6. Phase 5 — Planned Features

### 6.1 Claude AI Reasoning

**Purpose:** Tự động phân tích incident và sinh remediation plan.

```
Input:  raw_alert + evidence + runbook context
Output: root_causes[] + remediation_actions[] + summary
```

**Files:**
- `runguard/backend/ai/reasoner.py`
- `runguard/backend/ai/prompts.py`
- `POST /incidents/{id}/analyze`

### 6.2 Real K8s Actions

**Purpose:** Thực sự execute remediation trên K8s cluster.

| Action | K8s API |
|--------|---------|
| `rollout_restart` | `kubectl rollout restart` |
| `scale_replicas` | `patch deployment.spec.replicas` |
| `update_image` | `patch container.image` |
| `delete_pod` | `delete pod` |

**Files:**
- `runguard/backend/executor/k8s_actions.py`
- `POST /incidents/{id}/execute`

### 6.3 Alert Webhooks

**Purpose:** Nhận alert tự động từ Prometheus/Alertmanager.

```
POST /webhooks/alertmanager  — Alertmanager format
POST /webhooks/prometheus    — Prometheus format
POST /webhooks/generic       — Custom format
```

**Files:**
- `runguard/backend/api/webhooks.py` — Webhook route handlers
- `runguard/backend/webhooks/alertmanager.py` — Alertmanager payload parser
- `runguard/backend/webhooks/prometheus.py` — Prometheus payload parser
- `runguard/backend/webhooks/base.py` — Base webhook parser interface

### 6.4 Slack Notifications

**Purpose:** Gửi thông báo khi incident thay đổi trạng thái.

| Event | Message |
|-------|---------|
| Incident created | 🔴 New incident: {id} — {workload} ({severity}) |
| Approval required | ⚠️ Approval needed: {id} — {action} |
| Action executed | ✅ Action executed: {id} — {action} |
| Action failed | ❌ Action failed: {id} — {action}: {error} |
| Resolved | 🟢 Resolved: {id} — {summary} |

**Notification strategy (MVP):** Per-action notification — mỗi action execution gửi 1 Slack message. Lý do: mỗi action là 1 audit event riêng biệt, SRE cần biết action nào thành công/lại fail. Nếu incident có 5 actions → 5 messages. Future: batch mode (gom tất cả actions thành 1 summary message sau khi execute xong).

**Slack rate limiting:** Slack Incoming Webhook giới hạn 1 message/second per webhook. Executor thêm minimum 100ms delay giữa các Slack notifications để tránh rate limit. Nếu bị rate limit (HTTP 429), retry với exponential backoff (1s, 2s, 4s) — tối đa 3 lần. Nếu vẫn fail → log warning, tiếp tục execute actions (không block pipeline vì notification failure).

**Files:**
- `runguard/backend/notifications/slack.py`

---

## 7. API Reference

### 7.1 Current Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/incidents` | Create incident |
| `GET` | `/incidents` | List all incidents |
| `GET` | `/incidents/{id}` | Get incident details |
| `GET` | `/incidents/{id}/plan` | Get remediation plan |
| `POST` | `/incidents/{id}/approve` | Approve all pending actions (request body below) |
| `POST` | `/incidents/{id}/actions/{action_id}/approve` | Approve single action (request body below) |
| `POST` | `/incidents/{id}/reject` | Reject incident (request body below) |
| `POST` | `/runbooks` | Create/update runbook |
| `GET` | `/runbooks` | List all runbooks |
| `GET` | `/audit/{incident_id}` | Get audit trail |

**POST /incidents/{id}/approve**

Approve tất cả pending actions trong incident. Incident phải ở trạng thái `requires_approval`.

**Behavior khi approve:**
1. Lấy tất cả actions trong plan có `status=pending` và `policy_decision=requires_approval` → set `status=approved`.
2. Actions có `policy_decision=blocked` → **giữ nguyên** `status=blocked`, không approve, không execute. Blocked actions bị skip — không block cả incident.
3. Actions đã auto-approved (`policy_decision=approved`, `status=approved`) → giữ nguyên.
4. Nếu **tất cả** actions trong plan đều bị blocked (không có action nào được approve) → incident status = `failed`, audit log ghi `"All actions blocked by policy"`.
5. Incident status → `approved` (nếu có ít nhất 1 action được approve).

```json
// Request body (optional)
{
    "approver": "sre@example.com"   // optional — nếu không có, audit log ghi "anonymous"
}

// Response 200
{
    "status": "approved",
    "incident_id": "inc-abc123"
}

// Response 400 — incident không ở trạng thái requires_approval
{
    "detail": "Incident inc-abc123 is not in requires_approval state (current: pending)"
}
```

**POST /incidents/{id}/actions/{action_id}/approve**

Approve một action cụ thể trong plan. Dùng khi SRE muốn approve từng action thay vì bulk. Incident phải ở trạng thái `requires_approval`.

```json
// Request body (optional)
{
    "approver": "sre@example.com"
}

// Response 200 — action được approve
{
    "status": "approved",
    "action_id": "act-xxx",
    "incident_id": "inc-abc123"
}

// Response 200 — action đã auto-approved trước đó (no-op)
{
    "status": "already_approved",
    "action_id": "act-xxx",
    "incident_id": "inc-abc123"
}

// Response 400 — action bị blocked (không thể approve)
{
    "detail": "Action act-xxx is blocked by policy: Forbidden by runbook"
}

// Response 404 — action không tồn tại trong plan
{
    "detail": "Action act-xxx not found in incident plan"
}
```

**Auto-transition logic (synchronous):** Sau mỗi `POST /actions/{action_id}/approve`, server tự check trong request handler: đếm số actions có `policy_decision=requires_approval` và `status != approved`. Nếu bằng 0 → tự chuyển incident sang `approved`. Đây là synchronous check trong handler, không cần background job.

**Khi nào dùng per-action vs bulk:**
- `POST /incidents/{id}/approve` — bulk: approve tất cả `requires_approval` actions. Nhanh, tiện khi SRE tin tưởng policy engine.
- `POST /incidents/{id}/actions/{action_id}/approve` — per-action: SRE review từng action riêng. Dùng khi plan có mixed blast radius (low + high) và SRE chỉ muốn approve action an toàn.
- Khi **tất cả** `requires_approval` actions đã được approve (qua per-action), incident tự động chuyển sang `approved`. SRE không cần gọi bulk approve nữa.

**POST /incidents/{id}/reject**

Reject incident. Incident phải ở trạng thái `requires_approval`.

```json
// Request body (optional)
{
    "reason": "Not safe to restart in production hours"   // optional — ghi vào audit log
}

// Response 200
{
    "status": "rejected",
    "incident_id": "inc-abc123"
}

// Response 400 — incident không ở trạng thái requires_approval
{
    "detail": "Incident inc-abc123 is not in requires_approval state (current: pending)"
}
```

**GET /incidents/{id}/plan**

Lấy remediation plan của incident.

```json
// Response 200 — plan đã được generate
{
    "id": "plan-xxx",
    "incident_id": "inc-abc123",
    "summary": "Pod CrashLoopBackOff caused by OOMKilled",
    "root_causes": [...],
    "actions": [...]
}

// Response 200 — plan chưa được generate (status=pending hoặc analyzing)
// Trả về empty object, KHÔNG phải 404. Client check rỗng để biết plan chưa có.
// Lưu ý: client nên check `if (!response.id)` thay vì `if (!response)` vì object rỗng vẫn truthy trong JS.
{}

// Response 404 — incident không tồn tại
{
    "detail": "Incident not found"
}
```

### 7.2 Phase 5 Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/incidents/{id}/analyze` | AI analysis |
| `POST` | `/incidents/{id}/execute` | Execute approved actions |
| `POST` | `/webhooks/alertmanager` | Alertmanager webhook |
| `POST` | `/webhooks/prometheus` | Prometheus alert webhook |
| `POST` | `/webhooks/generic` | Generic webhook |

**POST /incidents/{id}/analyze**

Trigger AI analysis cho incident. Endpoint này **synchronous** — block tối đa 30s (Claude API timeout) rồi trả kết quả.

```json
// Request body — không có body. Incident context (alert, evidence, runbook) đã có sẵn trong incident.

// Response 200 — analysis thành công
{
    "incident_id": "inc-abc123",
    "status": "requires_approval",
    "plan": {
        "id": "plan-xxx",
        "summary": "Pod CrashLoopBackOff caused by OOMKilled. Restart with higher memory limit.",
        "root_causes": [
            {
                "cause": "Container OOMKilled due to memory limit too low",
                "confidence": 0.92,
                "evidence": ["pod logs show memory limit exceeded", "last state: OOMKilled"]
            }
        ],
        "actions": [
            {
                "id": "act-xxx",
                "name": "rollout_restart",
                "target": "my-app",
                "namespace": "default",
                "blast_radius": "low",
                "rollback_path": "kubectl rollout undo deployment/my-app -n default",
                "policy_decision": "requires_approval",
                "policy_reason": "Production environment requires human approval"
            }
        ]
    }
}

// Response 200 — tất cả actions auto-approved (Phase 5 only)
// /analyze tự trigger execution pipeline nội bộ khi tất cả actions là auto-approved.
// Không cần gọi /execute riêng. Incident → resolved trực tiếp.
{
    "incident_id": "inc-abc123",
    "status": "resolved",
    "plan": { ... },
    "execution_results": [
        {"action_id": "act-xxx", "status": "completed", "output": "deployment/my-app restarted"}
    ]
}

// Response 400 — incident không ở trạng thái đúng
{
    "detail": "Incident inc-abc123 is not in a valid state for analysis (current: requires_approval)"
}

// Response 500 — Claude API lỗi
{
    "detail": "AI analysis failed: Claude API timeout after 30s",
    "status": "analyzing"
}
```

**Valid states cho /analyze:** `pending`, `analyzing`. Nếu incident đã có plan (status = `requires_approval` hoặc sau) → return 400. Nếu Claude API fail → incident giữ nguyên status `analyzing`, SRE có thể retry.

**Flow khi gọi /analyze:**
- Nếu incident ở `pending` → endpoint tự động chạy Steps 2-3 (runbook compilation + evidence collection) trước khi gọi AI. Status chuyển: `pending` → `analyzing` → (AI) → `requires_approval` hoặc `resolved`.
- Nếu incident ở `analyzing` → Steps 2-3 đã hoàn thành (webhook flow đã chạy tự động khi alert đến). Chỉ chạy Step 4 (AI reasoning).
- Lý do `pending` là valid: manual incident được tạo qua `POST /incidents` nhưng evidence chưa được collect. SRE trigger `/analyze` để chạy toàn bộ pipeline.

**POST /incidents/{id}/execute**

Execute tất cả approved actions trong incident. Endpoint này **synchronous** — execute tuần tự, trả kết quả khi xong.

```json
// Request body — không có body. System execute tất cả actions có status "approved" trong plan.

// Response 200 — tất cả actions thành công
{
    "incident_id": "inc-abc123",
    "status": "resolved",
    "results": [
        {"action_id": "act-xxx", "name": "rollout_restart", "status": "completed", "output": "deployment/my-app restarted"},
        {"action_id": "act-yyy", "name": "scale_replicas", "status": "completed", "output": "deployment/my-app scaled to 3 replicas"}
    ]
}

// Response 207 (Multi-Status) — partial failure (some actions succeeded, some failed)
{
    "incident_id": "inc-abc123",
    "status": "failed",
    "results": [
        {"action_id": "act-xxx", "name": "rollout_restart", "status": "completed", "output": "deployment/my-app restarted"},
        {"action_id": "act-yyy", "name": "scale_replicas", "status": "failed", "error": "deployment not found"}
    ]
}

// Response 400 — incident không ở trạng thái approved
{
    "detail": "Incident inc-abc123 is not in approved state (current: requires_approval)"
}
```

**Execution behavior:**
- Execute **tuần tự** theo thứ tự actions trong plan (không song song — tránh blast radius chồng chéo).
- Nếu action #2 fail → **vẫn tiếp tục** execute action #3. Lý do: mỗi action có thể độc lập (e.g. restart deployment A không phụ thuộc vào scale deployment B). Ghi kết quả từng action vào results[].
- Nếu **bất kỳ** action nào fail → incident status = `failed` (không rollback tự động — SRE xem audit log để quyết định).
- Nếu **tất cả** thành công → incident status = `resolved`.
- Mỗi action execution ghi `action_executed` hoặc `action_failed` vào audit log.

**Valid states cho /execute:** `approved`. Nếu incident ở trạng thái khác → return 400.

**HTTP status codes cho /execute:**
- `200` — tất cả actions thành công (incident → `resolved`)
- `207 Multi-Status` — partial failure (ít nhất 1 action fail, ít nhất 1 action thành công). Client **phải** parse `results[]` để biết action nào fail.
- `400` — incident không ở trạng thái `approved`
- `500` — system error (K8s API unavailable, unexpected exception)

---

## 8. Data Models

### 8.1 Incident

```python
{
    "id": "inc-abc123",
    "source": "prometheus",           # prometheus | manual | cloudwatch
    "severity": "high",               # low | medium | high | critical
    "environment": "production",      # dev | staging | production
    "namespace": "default",
    "workload": "my-app",
    "raw_alert": "PodCrashLoopBackOff...",
    "runbook_id": "rb-xxx",           # required for manual incidents; auto-matched for webhooks (Step 1.5)
    "plan_id": "plan-xxx",            # set when plan is generated (Step 4 — AI Reasoning)
    "status": "pending",              # pending | analyzing | requires_approval | executing | resolved | rejected | failed
    "created_at": "2026-05-07T10:00:00Z",
    "updated_at": "2026-05-07T10:00:00Z"
}
```

### 8.2 Policy (from Runbook)

```python
{
    "id": "pol-xxx",
    "runbook_id": "rb-xxx",
    "scope": {
        "namespaces": ["default", "staging"],
        "workloads": ["web-app", "api-server"]
    },
    "allowed_actions": [
        {
            "name": "rollout_restart",
            "blast_radius": "low",
            "rollback_path": "kubectl rollout undo deployment/{name}"
        }
    ],
    "forbidden_actions": [
        {"name": "delete_deployment", "reason": "No auto-delete in MVP"}
    ],
    "severity": "high"
}
```

**Lưu ý:** `forbidden_actions.name` không bị giới hạn trong Valid Tool Names (Section 10.2).
Forbidden list có thể chứa bất kỳ action name nào — bao gồm cả tên chưa có trong allowed list — để phòng ngừa future runbooks thêm tool nguy hiểm.
Policy engine match theo exact string, không validate tool name existence.

### 8.3 RemediationPlan

```python
{
    "id": "plan-xxx",
    "incident_id": "inc-abc123",
    "actions": [RemediationAction],   # list of actions to execute
    "summary": "Pod CrashLoopBackOff caused by OOMKilled. Restart with higher memory limit.",
    "root_causes": [
        {
            "cause": "Container OOMKilled due to memory limit too low",
            "confidence": 0.92,
            "evidence": ["pod logs show memory limit exceeded", "last state: OOMKilled"]
        }
    ],
    "created_at": "2026-05-07T10:05:00Z"
}
```

Plan được tạo khi AI Reasoning hoàn thành (`POST /analyze`), sau khi evidence đã được collected. Plan chứa tất cả actions cần thực hiện. `GET /incidents/{id}/plan` trả về plan hiện tại của incident (trả `{}` nếu plan chưa được generate).

### 8.4 RemediationAction

```python
{
    "id": "act-xxx",
    "plan_id": "plan-xxx",
    "name": "rollout_restart",              # tool name from Allowed Tools
    "target": "my-app",                     # deployment/pod name
    "namespace": "default",
    "parameters": {},                       # action-specific params (e.g. {"replicas": 3} for scale_replicas)
    "blast_radius": "low",                  # low | medium | high
    "rollback_path": "kubectl rollout undo deployment/my-app -n default",
    "status": "pending",                    # pending | approved | blocked | executing | completed | failed
    "policy_decision": "approved",          # approved | requires_approval | blocked
    "policy_reason": "Low risk, rollback available",  # human-readable reason from policy engine
    "created_at": "2026-05-07T10:05:00Z",
    "executed_at": null                     # set when execution starts
}
```

Actions được lưu trong RemediationPlan.actions[].

**Approve flow (2 bước riêng biệt):**
1. `POST /incidents/{id}/approve` hoặc `POST /incidents/{id}/actions/{action_id}/approve` — chỉ set action `status=approved`, incident status → `approved`. **Không execute.**
2. `POST /incidents/{id}/execute` — trigger execution. Incident status → `executing` → `resolved` hoặc `failed`.

Actions có `policy_decision=blocked` bị skip — không approve, không execute, không block cả incident (xem Section 7.1 cho chi tiết approve behavior).

**Exception:** Khi `POST /analyze` phát hiện tất cả actions là auto-approved (`policy_decision=approved`), nó tự động trigger execution pipeline nội bộ — không cần gọi `/execute` riêng. Incident → `resolved` (xem Section 7.2 cho chi tiết). Đây là Phase 5 only.

### 8.5 AuditRecord

```python
{
    "id": "aud-xxx",
    "incident_id": "inc-abc123",
    "event_type": "action_executed",
    "actor": "sre-oncall@company.com",
    "details": {"action": "rollout_restart", "target": "my-app"},
    "timestamp": "2026-05-07T10:00:00Z"
}
```

Field notes:
- `event_type`: one of `incident_created`, `plan_generated`, `analysis_failed`, `action_validated`, `action_auto_approved`, `approved`, `rejected`, `action_executed`, `action_failed`, `gitops_commit`
- `actor`: user ID, email, token, or `"system"` for auto-approved/system actions

**Event Types:**

| Event Type | Description | Actor |
|------------|-------------|-------|
| `incident_created` | Incident được tạo | source system hoặc user |
| `plan_generated` | AI analysis thành công, remediation plan được tạo | `system` |
| `analysis_failed` | AI analysis thất bại (Claude API error/timeout) | `system` |
| `action_validated` | Policy engine check action | `system` |
| `action_auto_approved` | Action tự approve (low risk + có rollback) | `system` |
| `approved` | SRE approve action | user email/ID |
| `rejected` | SRE reject action | user email/ID |
| `execution_started` | Execution bắt đầu (`POST /execute` gọi, incident → `executing`) | `system` |
| `action_executed` | Action thực thi thành công | `system` |
| `action_failed` | Action thực thi thất bại | `system` |
| `gitops_commit` | GitOps commit created | `system` |

**Transition `approved → executing`:** Triggered by `POST /incidents/{id}/execute`. Không phải background job. SRE (hoặc system) phải gọi `/execute` explicit. Khi `/execute` được gọi, incident status chuyển `approved` → `executing`, ghi `execution_started` audit event, rồi execute actions tuần tự.

---

## 9. Deployment

### 9.0 Audit Store — MVP Limitation

> **MVP only:** JSON file-based audit store (`data/audit/*.json`) đơn giản nhưng có giới hạn:
> - **Không hỗ trợ multi-instance horizontal scaling** — mỗi instance ghi vào file riêng, không đồng bộ.
> - **Không có write-ahead log** — crash giữa write có thể corrupt record.
> - **Không có retention policy** — file grow vô hạn.
>
> **Production migration path:** PostgreSQL audit table (append-only, row-level security) hoặc S3 + Object Lock (WORM compliance). Trigger migration khi cần horizontal scaling hoặc compliance requirement.

### 9.1 Local Development

```bash
# Install
pip install -e ".[dev]"

# Run API (with K8s mock — no cluster needed)
RUNGUARD_K8S_MOCK=true uvicorn runguard.backend.main:app --reload

# Run UI
streamlit run runguard/ui/app.py

# Run tests
pytest tests/ -v
```

**K8s Mock Mode:** Khi `RUNGUARD_K8S_MOCK=true`, `KubernetesEvidenceCollector` trả về mock evidence data thay vì gọi K8s API. Hữu ích cho local development khi không có cluster. Mock data bao gồm: sample pod logs, events, deployment status. Được enable tự động khi chạy test (`conftest.py` set env var).

### 9.2 Docker Compose

```bash
docker compose up --build
# API: http://localhost:8000
# UI:  http://localhost:8501
```

### 9.3 kind Cluster

```bash
# Create cluster
kind create cluster --config infra/kind-config.yaml

# Build & load image
docker build -t runguard:latest .
kind load docker-image runguard:latest

# Deploy
kubectl apply -f infra/k8s/namespace.yaml
kubectl apply -f infra/k8s/

# Access
# API: http://localhost:8000 (NodePort 30080)
# UI:  http://localhost:8501 (NodePort 30081)
```

---

## 10. Runbook Format

### 10.1 Formal Schema

Runbook phải có đúng các heading sau (case-insensitive, nhưng recommend lowercase):

```markdown
# {Title}                    ← Bắt buộc, H1 đầu tiên

## Scope                     ← Bắt buộc
- Namespaces: {comma-separated}
- Workloads: {comma-separated}

## Allowed Tools             ← Bắt buộc
- {tool_name}               ← Mỗi tool một dòng
- {tool_name}

## Forbidden Tools           ← Bắt buộc
- {tool_name}

## Severity                  ← Bắt buộc
{low|medium|high|critical}   ← Plain text, không phải list

## Rollback Steps            ← Bắt buộc
1. {step}
2. {step}
```

### 10.2 Valid Tool Names

| Tool Name | Description |
|-----------|-------------|
| `rollout_restart` | Restart deployment pods |
| `scale_replicas` | Scale deployment replicas |
| `update_image` | Update container image |
| `delete_pod` | Delete specific pod |
| `fetch_logs` | Retrieve pod logs |
| `patch_config` | Update ConfigMap/Secret |

### 10.3 Parser Behavior

| Scenario | Behavior |
|----------|----------|
| Heading sai chính tả (e.g. `## Allowed Actions`) | Parser bỏ qua section đó → missing tools → compilation error |
| Thiếu section bắt buộc | Return error: `"Missing required section: {name}"` |
| Severity không hợp lệ | Default to `medium` + log warning |
| Scope section missing | Return error: `"Missing required section: Scope"` — không tự apply toàn cluster |
| Scope có `*` trong workloads | Apply cho tất cả workloads trong namespace đã khai báo, log warning |
| Duplicate headings | Section sau ghi đè section trước + log warning: `"Duplicate section: {name}, using last occurrence"` |
| Forbidden Tools section rỗng (không có tool nào list) | Hợp lệ — `forbidden_actions = []`. Nhiều runbooks không cần forbidden list. |

### 10.4 Sample Runbooks

#### 10.4.1 Pod CrashLoop

```markdown
# Pod CrashLoop Runbook

## Scope
- Namespaces: default, staging
- Workloads: web-app, api-server

## Allowed Tools
- rollout_restart
- scale_replicas
- fetch_logs

## Forbidden Tools
- delete_pod
- delete_deployment

## Severity
high

## Rollback Steps
1. kubectl rollout undo deployment/{name} -n {namespace}
2. kubectl scale deployment/{name} --replicas={original_replicas} -n {namespace}
```

#### 10.4.2 Other Runbooks

- `runbooks/image-pull-failure.md` — ImagePullBackOff handling
- `runbooks/readiness-probe-failure.md` — Readiness probe fixes

---

## 11. Configuration

### 11.1 Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `RUNGUARD_API_KEY` | — | API key for `X-API-Key` header auth |
| `RUNGUARD_WEBHOOK_SECRET` | — | Bearer token for webhook auth |
| `RUNGUARD_ANTHROPIC_API_KEY` | — | Claude API key |
| `RUNGUARD_CLAUDE_MODEL` | `claude-sonnet-4-20250514` | Claude model |
| `RUNGUARD_ENV` | `local` | Environment |
| `RUNGUARD_LOG_LEVEL` | `INFO` | Log level |
| `RUNGUARD_K8S_NAMESPACE` | `runguard` | Default K8s namespace |
| `RUNGUARD_K8S_MOCK` | `false` | Mock K8s API for local dev (returns sample evidence) |
| `RUNGUARD_AUDIT_STORE_PATH` | `./data/audit` | Audit store path |
| `RUNGUARD_GITOPS_ENABLED` | `false` | Enable GitOps mode |
| `RUNGUARD_GITOPS_REPO_PATH` | — | Git repo path for GitOps |
| `RUNGUARD_OPENCOST_ENDPOINT` | — | OpenCost API URL |
| `RUNGUARD_SLACK_WEBHOOK_URL` | — | Slack incoming webhook |
| `RUNGUARD_API_URL` | `http://localhost:8000` | API URL (for UI) |

### 11.2 Settings File

`runguard/backend/config.py` — Pydantic Settings, đọc từ env vars.

---

## 12. Safety Guardrails

### 12.1 Mandatory Rules

1. Không action nếu không match scope → `blocked`
2. Không action nếu blast radius vượt threshold → `requires_approval`
3. Không action nếu IAM permissions thiếu → `blocked`
4. Không action trên production nếu chưa approve → `requires_approval`
5. Không có rollback path → `requires_approval` (không blocked, SRE vẫn có thể approve nếu chấp nhận rủi ro)
6. Tối đa 5 auto-approved actions per incident → action thứ 6 trở đi là `requires_approval`
   - Counter chỉ đếm `action_auto_approved`, không đếm human-approved
   - Counter reset khi incident chuyển sang `resolved` hoặc `rejected` (cả hai là trạng thái cuối)
   - **Counter là computed value**, không lưu trong model. Policy engine đếm số `action_auto_approved` audit records cho incident_id khi validate. Không cần field `auto_approved_count` trong Incident hay Plan model.

### 12.2 Incident Status Transitions

```
                         ┌───────────┐
                         │  pending  │
                         └─────┬─────┘
                               │ evidence collected
                               ▼
                         ┌───────────┐         all auto-approved
                         │ analyzing │───────────────┐ & executed
                         └─────┬─────┘               │
                               │                     ▼
                    ┌──────────┴──────────┐     ┌──────────┐
                    │                     │     │ resolved │
                    │ plan generated      │     └──────────┘
                    │ (có action cần      │          ▲    ▲
                    │  approval)          │          │    │
                    ▼                     │          │    │
          ┌───────────────────┐  auto-    │          │    │
          │ requires_approval │  expire   │          │    │
          └─────────┬─────────┘  24h      │          │    │
                    │            (no      │          │    │
                    │            action)  ▼          │    │
         ┌──────────┴──────────┐  ┌──────────┐      │    │
         │                     │  │  failed  │      │    │
         ▼                     ▼  └──────────┘      │    │
   ┌──────────┐         ┌──────────┐                │    │
   │ approved │         │ rejected │                │    │
   └────┬─────┘         └──────────┘                │    │
        │                                           │    │
        ▼                      auto-expire          │    │
   ┌──────────┐    fail      4h (no SRE)            │    │
   │ executing │────────────────────────────────────┘    │
   └────┬─────┘                                         │
        │                                               │
        │ success                                       │
        └───────────────────────────────────────────────┘
```

**All terminal states:** `resolved`, `rejected`, `failed` — không có transition ra.

**Transition Rules:**

| From | To | Condition |
|------|-----|-----------|
| `pending` | `analyzing` | Evidence collection bắt đầu |
| `analyzing` | `requires_approval` | Plan generated, có action cần approval |
| `analyzing` | `resolved` | Plan generated, tất cả actions auto-approved và execute thành công |
| `analyzing` | `failed` | Auto-expire: không có action trong 24h (xem Section 14.3) |
| `requires_approval` | `approved` | SRE approve (POST /approve) |
| `requires_approval` | `rejected` | SRE reject (POST /reject) |
| `requires_approval` | `failed` | Auto-expire: SRE không respond trong 4h (xem Section 14.3) |
| `approved` | `executing` | Bắt đầu execute actions |
| `executing` | `resolved` | Tất cả actions thành công |
| `executing` | `failed` | Bất kỳ action nào fail |
| `rejected` | (end) | Incident đóng. Muốn reopen → tạo incident mới |

**Lưu ý:**
- `rejected` là trạng thái cuối — không reopen, không redo
- `failed` là trạng thái cuối — cần tạo incident mới nếu muốn retry
- Không có transition từ `resolved` sang bất kỳ trạng thái nào

### 12.3 Policy Decision Matrix

| # | Condition | Result | Lý do |
|---|-----------|--------|-------|
| 1 | Action trong forbidden list | `blocked` | Runbook explicit cấm |
| 2 | Action không trong allowed list | `blocked` | Không nằm trong scope |
| 3 | Namespace ngoài scope | `blocked` | Vi phạm scope |
| 4 | IAM permissions thiếu | `blocked` | Không có quyền thực thi |
| 5 | Production environment | `requires_approval` | Prod cần human oversight |
| 6 | Blast radius medium/high | `requires_approval` | Ảnh hưởng rộng cần xem xét |
| 7 | Không có rollback path | `requires_approval` | Rủi ro cao, SRE quyết định |
| 8 | Đã đạt 5 auto-approved actions | `requires_approval` | Giới hạn an toàn |
| 9 | blast_radius = "low" + có rollback + chưa đạt limit | `approved` | Tự động execute |
| 10 | Default (không match rule nào) | `requires_approval` | Fail-safe: default to human approval |

**"Low risk" definition:** Rule #9 match khi và chỉ khi cả 3 điều kiện đều đúng:
- `blast_radius == "low"` (đã define trong AllowedAction)
- `rollback_path` không rỗng (có ít nhất 1 step)
- `auto_approved_count < 5` (chưa đạt giới hạn)

Nếu bất kỳ điều kiện nào fail → rule #9 không match → fall through tới rule #10 (default `requires_approval`).

**Thứ tự evaluation:** Policy engine check theo thứ tự #1 → #9, match rule nào trả kết quả rule đó (first-match).

---

## 13. Authentication & Authorization

### 13.1 API Authentication

| Endpoint Type | Auth Mechanism | Description |
|---------------|---------------|-------------|
| Internal API (`/incidents`, `/runbooks`, `/audit`) | API Key header | `X-API-Key: {key}` — cho phép internal services và UI gọi |
| Webhooks (`/webhooks/*`) | Bearer token | `Authorization: Bearer {secret}` — Alertmanager native support |
| Public API (future) | JWT / OAuth 2.0 | Cho multi-user, SSO integration |

**MVP webhook auth: Bearer token**

Alertmanager natively supports `http_config.authorization` with `type: Bearer` — no custom plugin needed.

```yaml
# alertmanager.yml
receivers:
  - name: runguard
    webhook_configs:
      - url: http://runguard-api:8000/webhooks/alertmanager
        http_config:
          authorization:
            type: Bearer
            credentials_file: /etc/alertmanager/secrets/webhook-secret
        send_resolved: true
```

Lưu ý: Alertmanager không hỗ trợ `${VAR}` shell expansion trong config. Dùng `credentials_file` để đọc secret từ file (mounted từ K8s Secret). File chứa raw token string, không có newline.

RunGuard server verify: `Authorization: Bearer {secret}` matches `RUNGUARD_WEBHOOK_SECRET` env var.

### 13.2 Authorization Matrix

| Action | Anonymous | API Key | SRE Role | Admin Role |
|--------|-----------|---------|----------|------------|
| `GET /health` | ✅ | ✅ | ✅ | ✅ |
| `POST /incidents` | ❌ | ✅ | ✅ | ✅ |
| `GET /incidents` | ❌ | ✅ | ✅ | ✅ |
| `POST /incidents/{id}/analyze` | ❌ | ❌ | ✅ | ✅ |
| `POST /incidents/{id}/approve` | ❌ | ❌ | ✅ | ✅ |
| `POST /incidents/{id}/reject` | ❌ | ❌ | ✅ | ✅ |
| `POST /incidents/{id}/execute` | ❌ | ❌ | ✅ | ✅ |
| `POST /runbooks` | ❌ | ✅ | ✅ | ✅ |
| `GET /audit/*` | ❌ | ✅ | ✅ | ✅ |

**MVP note:** `POST /runbooks` cho phép API Key (không chỉ Admin) vì MVP chỉ có 1 service account. Post-MVP: phân quyền rõ ràng qua RBAC.

### 13.3 Webhook Verification

```python
import hmac


def verify_webhook_bearer(authorization_header: str, secret: str) -> bool:
    """Verify Bearer token from Authorization header."""
    if not authorization_header.startswith("Bearer "):
        return False
    token = authorization_header[7:]  # Remove "Bearer " prefix
    return hmac.compare_digest(token, secret)
```

### 13.4 MVP Scope

- **MVP:** API Key authentication cho internal API, Bearer token cho webhooks
- **Post-MVP:** JWT/OAuth cho multi-user, RBAC cho approval workflow
- Secrets lưu trong environment variables hoặc Kubernetes Secrets (không hardcode)

---

## 14. Error Handling & Timeouts

### 14.1 Timeout Configuration

| Operation | Timeout | Behavior on Timeout |
|-----------|---------|---------------------|
| Claude API call | 30s | Return raw evidence without plan, log warning |
| K8s pod logs collection | 10s | Return partial results + timeout warning |
| K8s events collection | 5s | Return empty list + timeout warning |
| K8s deployment status | 5s | Return error object + timeout warning |
| Evidence collection (total) | 30s | Return whatever collected so far |
| SSM document execution | 300s | Mark as `failed`, notify |
| Webhook processing | 10s | Return 504 to caller |
| Policy validation | 5s | Block action, log error |

### 14.2 Retry Policy

| Operation | Max Retries | Backoff | Behavior After Exhaust |
|-----------|-------------|---------|------------------------|
| Claude API call | 2 | exponential (1s, 2s) | Return raw evidence, no plan |
| K8s API call | 1 | immediate | Return error, continue with partial data |
| SSM trigger | 2 | exponential (2s, 4s) | Mark `failed`, notify |
| Slack notification | 3 | exponential (1s, 2s, 4s) | Log warning, continue |

### 14.3 Graceful Degradation

```
Claude API unavailable?
  → Collect evidence (works fine)
  → Skip AI reasoning
  → Return raw evidence to user
  → Status: "analyzing" (không chuyển "requires_approval")
  → Notify SRE: "AI analysis failed — manual review required"
  → SRE có thể:
    - Retry: POST /incidents/{id}/analyze (re-trigger AI)
    - Manual: Xem raw evidence, tự approve/reject qua UI
  → Incident auto-expire sau 24h nếu không có action → status: "failed"

**Auto-expire mechanism:** Lazy check — khi `GET /incidents/{id}` được gọi, server check `updated_at` timestamp. Nếu incident ở `requires_approval` quá 4h hoặc `analyzing` quá 24h → tự chuyển sang `failed`, ghi audit log. Không cần background scheduler. MVP approach — Phase 5+ có thể migrate sang background scheduler (APScheduler hoặc K8s CronJob) nếu cần real-time expiry.

K8s API unavailable?
  → Return last known state (nếu có cache)
  → Show "connection lost" warning trong UI
  → Không execute bất kỳ action nào

Policy Engine error?
  → Block tất cả actions (fail-safe)
  → Log error
  → Notify SRE

Incident ở trạng thái "requires_approval" quá 4h?
  → SRE không respond (không approve, không reject)
  → Auto-transition sang "failed"
  → Audit log ghi: "Incident auto-expired: no approval response within 4h"
  → Notify SRE: "Incident {id} expired — no approval within 4h"
  → Không rollback (chưa có action nào execute)

Incident ở trạng thái "analyzing" quá 24h?
  → Không có action nào được tạo (AI fail + SRE không retry)
  → Auto-transition sang "failed"
  → Audit log ghi: "Incident auto-expired: no action taken within 24h"
```

### 14.4 Error Response Format

```python
{
    "error": {
        "code": "EVIDENCE_TIMEOUT",
        "message": "Pod logs collection timed out after 10s",
        "details": {"namespace": "default", "workload": "my-app"},
        "retryable": true
    }
}
```

---

## 15. Differentiators

### vs Chatbot (ChatGPT, Claude)
- RunGuard **enforce execution constraints** — không chỉ suggest
- Có policy engine chặn actions nguy hiểm
- Audit trail cho mọi quyết định

### vs Automation Scripts (Ansible, Terraform)
- RunGuard **AI-powered** — tự phân tích root cause
- Không cần viết script cho từng scenario
- Context-aware — đọc evidence trước khi quyết định

### vs Generic AIOps (BigPanda, PagerDuty AIOps)
- RunGuard **narrower, more actionable** — focused vào remediation
- Runbook compiler — machine-enforceable policies
- Open source, self-hosted

---

## 16. Roadmap

### Near-term (Phase 5)
- Claude AI reasoning integration
- Real K8s action execution
- Alert webhooks (Prometheus/Alertmanager)
- Slack notifications

### Mid-term
- Multi-cluster support
- Custom policy rules (OPA/Rego)
- Web UI improvements (React)
- RBAC for multi-user

### Long-term
- Terraform integration for infra changes
- Multi-cloud support (GCP, Azure)
- Learning from past incidents
- Auto-generate runbooks from incidents

---

## 17. Quick Demo Script

```bash
# Prerequisites: jq must be installed (https://jqlang.github.io/jq/)
# macOS: brew install jq | Ubuntu: apt install jq | Windows: choco install jq

# 0. Required environment variables
export RUNGUARD_API_KEY="your-api-key"
export RUNGUARD_ANTHROPIC_API_KEY="sk-ant-..."    # required for /analyze endpoint
export RUNGUARD_WEBHOOK_SECRET="your-webhook-secret"

# 1. Start services
docker compose up --build

# 2. Create runbook (capture runbook ID from response)
RUNBOOK_ID=$(curl -s -X POST http://localhost:8000/runbooks \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${RUNGUARD_API_KEY}" \
  -d '{"title":"CrashLoop","content":"# CrashLoop\n\n## Scope\n- Namespaces: default\n\n## Allowed Tools\n- rollout_restart\n\n## Forbidden Tools\n- delete_pod\n\n## Severity\nhigh\n\n## Rollback Steps\n1. kubectl rollout undo deployment/{name}"}' | jq -r '.id')

# 3. Create incident (manual incidents require runbook_id)
curl -X POST http://localhost:8000/incidents \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${RUNGUARD_API_KEY}" \
  -d "{\"source\":\"manual\",\"severity\":\"high\",\"environment\":\"production\",\"namespace\":\"default\",\"workload\":\"my-app\",\"raw_alert\":\"PodCrashLoopBackOff\",\"runbook_id\":\"${RUNBOOK_ID}\"}"

# 4. Trigger AI analysis (generates remediation plan)
# [Phase 5 — requires RUNGUARD_ANTHROPIC_API_KEY]
curl -X POST http://localhost:8000/incidents/${INCIDENT_ID}/analyze \
  -H "X-API-Key: ${RUNGUARD_API_KEY}"

# 5. Open UI
# http://localhost:8501 → Incidents → View → Approve/Reject
```

**Lưu ý:** Incident mới tạo ở status `pending` — cần gọi `POST /analyze` để generate plan và chuyển status sang `requires_approval`. Nếu Phase 5 chưa implement, dùng seed endpoint hoặc mock plan để demo flow approval.
