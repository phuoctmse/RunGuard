# RunGuard

**Project Type:** AI-powered DevOps/SRE incident remediation platform

**Product Subtitle:** Runbook compiler + safe auto-remediation planner

**Primary Goal:** Build a low-cost, Kubernetes-first, AWS-integrated tool that converts human runbooks into machine-readable policies, investigates incidents, proposes remediation plans, and executes only safe actions with guardrails.

**Audience:** DevOps Engineers, SREs, Platform Engineers

**Secondary Goal:** Support portfolio/CV value for AWS SAA, CKA, CKAD, and DevOps Engineer Professional preparation.

---

## 1. Executive Summary

RunGuard is an internal operations platform for incident investigation and safe remediation. It is not just a chatbot and not just an automation framework. It combines four layers:

1. **Runbook compiler**: converts Markdown runbooks into structured policies and action constraints.
2. **Incident reasoning engine**: uses alerts, logs, metrics, traces, and Kubernetes events to infer likely causes.
3. **Safety policy engine**: validates the proposed plan against guardrails such as scope, blast radius, rollback availability, and IAM permissions.
4. **Remediation executor**: performs only approved actions, ideally in a dry-run or human-approved mode first.

The product should be demonstrated on Kubernetes workloads running locally and optionally on AWS EKS in short-lived environments to keep cost low.

---

## 2. Problem Statement

Modern DevOps and SRE teams usually operate with fragmented knowledge and fragmented tools:

- Runbooks live in Markdown, wiki pages, Notion, or tribal knowledge.
- Alerts come from Kubernetes, AWS CloudWatch, Prometheus, or application logs.
- Operators must manually correlate signals across logs, metrics, traces, and events.
- Remediation is risky because the wrong action can increase downtime or cause a larger blast radius.
- Even when automation exists, it is usually rule-based and not context-aware.

### Core Pain Points

- Incident triage is slow.
- Runbooks are human-readable but not machine-enforceable.
- Automation is often too broad, too unsafe, or too rigid.
- Engineers need a system that can reason about context while still obeying hard guardrails.

### Why this matters

This is a realistic DevOps problem that maps to production operations, Kubernetes troubleshooting, incident response, observability, and cloud automation. It is also a strong portfolio project because it shows both engineering depth and operational thinking.

---

## 3. Product Vision

The product should behave like a smart incident assistant for platform teams:

- It reads an incident alert.
- It retrieves the most relevant runbook.
- It converts the runbook into an execution policy.
- It gathers evidence from Kubernetes and AWS.
- It proposes a safe remediation plan.
- It executes only approved actions.
- It always records what happened, why, and what can be rolled back.

### Positioning

This is best positioned as:

- an internal platform tool,
- an incident remediation assistant,
- a Kubernetes and AWS operations copilot with policy guardrails.

It is **not** intended to be a public SaaS in the first version.

---

## 4. Product Scope

### In Scope

- Parse runbooks written in Markdown.
- Support incident triage for Kubernetes workloads.
- Integrate with AWS services for alerts, automation, and logging.
- Produce structured remediation plans.
- Validate plans against policy.
- Support human approval before risky actions.
- Maintain audit logs.
- Keep infrastructure cost low.

### Out of Scope for MVP

- Full multi-tenant SaaS billing.
- Complex user management and organization admin panels.
- Large-scale enterprise SSO integration.
- Fully autonomous remediation without approval.
- GPU-heavy AI workloads.
- Always-on EKS clusters in production for demo purposes.

---

## 5. Target Users

### Primary Persona: DevOps Engineer

- Needs to troubleshoot production issues.
- Wants faster triage and safer remediation.
- Cares about AWS, Kubernetes, CI/CD, and reliability.

### Secondary Persona: SRE / Platform Engineer

- Needs repeatable incident handling.
- Wants governance, auditability, and rollback.
- Cares about automation that does not break production.

### Tertiary Persona: Hiring Manager / Interviewer

- Wants to see production thinking.
- Wants evidence of Kubernetes, AWS, observability, and automation skills.
- Wants a project that is more than a generic AI demo.

---

## 6. Core User Stories

1. As an engineer, I want to paste or receive an alert so the system can identify the likely runbook.
2. As an engineer, I want the system to summarize the incident in plain language.
3. As an engineer, I want the system to retrieve relevant logs, metrics, traces, and Kubernetes events.
4. As an engineer, I want the system to propose a remediation plan with ranked steps.
5. As an engineer, I want risky actions to be blocked unless policy and approval requirements are satisfied.
6. As an engineer, I want rollback steps to be required for every executed action.
7. As an engineer, I want a complete audit trail for every diagnosis and action.
8. As an engineer, I want the system to run cheaply, with most development done locally and only short-lived AWS resources.

---

## 7. Key Differentiators

### Compared to a normal chatbot

- This project enforces execution constraints.
- It knows about runbooks and operational policy.
- It integrates with real signals and actions.

### Compared to a normal automation tool

- This project uses AI reasoning to choose what to inspect and what to do.
- It does not rely only on static workflows.

### Compared to generic AIOps

- It is narrower and more actionable.
- It is designed around a runbook compiler and safety checks.
- It is Kubernetes-first and AWS-aware.

---

## 8. Functional Requirements

### 8.1 Runbook Compiler

The system must:

- Read runbooks written in Markdown.
- Extract metadata such as scope, prerequisites, allowed tools, forbidden tools, severity, and rollback steps.
- Convert the runbook into structured JSON policy data.
- Support versioning of runbooks.

### 8.2 Incident Intake

The system must accept incident input from:

- Kubernetes alerts,
- CloudWatch alarms,
- Prometheus Alertmanager webhooks,
- manual input through UI or API.

### 8.3 Incident Reasoning

The system must:

- summarize the incident,
- identify likely root cause candidates,
- fetch supporting evidence,
- cite which evidence influenced the conclusion,
- produce a ranked remediation plan.

### 8.4 Safety Policy Engine

The system must validate any proposed action against:

- namespace/workload scope,
- blast radius estimate,
- rollback existence,
- allowed action list,
- IAM permissions,
- environment safety (dev/staging/prod rules),
- approval requirements.

### 8.5 Remediation Executor

The system must be able to execute low-risk actions such as:

- Kubernetes rollout restart,
- scaling a deployment,
- checking pod status,
- fetching logs,
- running a Kubernetes Job or CronJob,
- triggering an AWS SSM document,
- sending notifications to Slack or SNS.

### 8.6 Human Approval Workflow

The system must support:

- auto-execution for low-risk actions,
- manual approval for medium/high-risk actions,
- rejection and rollback for unsafe actions.

### 8.7 Audit and Observability

The system must store:

- incident ID,
- alert source,
- evidence gathered,
- runbook used,
- plan proposed,
- actions executed,
- approval status,
- rollback status,
- timestamps,
- operator identity if applicable.

---

## 9. Non-Functional Requirements

### 9.1 Reliability

- The platform should fail safe.
- If the AI component is unavailable, the system should still allow read-only investigation.
- If policy validation fails, no remediation action should run.

### 9.2 Security

- Use least privilege IAM roles.
- Keep secrets in AWS Secrets Manager or Kubernetes Secrets with proper access control.
- Avoid exposing raw credentials in logs.
- Use signed identity through OIDC for CI/CD role assumption.

### 9.3 Cost Control

- Prefer local Kubernetes for most development.
- Prefer AWS serverless services for control plane orchestration.
- Avoid always-on EKS during early development.
- Destroy short-lived demo resources automatically.

### 9.4 Maintainability

- Keep the system modular.
- Separate runbook parsing, reasoning, policy validation, and execution.
- Make each module testable independently.

### 9.5 Explainability

- Every plan must explain why it was chosen.
- The output should show evidence and confidence level.
- The system must make policy failures explicit.

---

## 10. Proposed Architecture

### 10.1 High-Level Flow

1. Alert arrives from AWS or Kubernetes.
2. EventBridge or API Gateway forwards the incident.
3. Step Functions orchestrates the workflow.
4. Lambda or a small service invokes the planner.
5. Planner retrieves the matching runbook.
6. Policy engine validates the plan.
7. If approved, executor performs the action.
8. Observability and audit records are stored.

### 10.2 Logical Components

#### A. Intake Layer

- EventBridge
- CloudWatch Alarm
- Alertmanager webhook
- API endpoint for manual cases

#### B. Runbook Compiler

- Markdown parser
- metadata extractor
- policy schema generator

#### C. Incident Planner

- LLM or reasoning service
- tool selection logic
- evidence retriever
- action proposal generator

#### D. Policy Engine

- scope validation
- blast radius validation
- rollback validation
- IAM validation
- action approval rules

#### E. Execution Layer

- Kubernetes API client
- SSM Automation / Run Command
- notification integration

#### F. Storage and Audit

- DynamoDB for incident state
- CloudWatch Logs for operational logs
- optional S3 for archived artifacts

#### G. UI / Console

- minimal web dashboard
- incident timeline view
- remediation plan view
- approval button
- rollback history

---

## 11. Suggested Technology Stack

### Core

- **Backend orchestration:** Go or Python
- **Policy / rules:** Go preferred for deterministic checks
- **UI:** minimal Next.js, React, or Streamlit if speed matters
- **Kubernetes:** kind or k3d locally, optional EKS short-lived
- **AWS:** Lambda, Step Functions, EventBridge, DynamoDB, SQS, CloudWatch, SSM, IAM, KMS, Secrets Manager
- **Observability:** OpenTelemetry, CloudWatch, Prometheus, Loki, Grafana
- **IaC:** Terraform
- **CI/CD:** GitHub Actions with OIDC

### Optional Enhancements

- AWS Cost Explorer for cost-aware remediation
- OpenCost for EKS cost visibility
- ALB Ingress Controller for EKS exposure
- S3 for archived runbooks and incident artifacts

---

## 12. Kubernetes Requirements

Because this project must support CKA and CKAD preparation, Kubernetes is not optional. It should be visible in the product and the demo.

### Kubernetes Features to Include

- Deployment
- Service
- ConfigMap
- Secret
- Ingress
- HPA
- Job
- CronJob
- Namespace isolation
- ResourceQuota
- LimitRange
- NetworkPolicy
- RBAC
- ServiceAccount
- Readiness and liveness probes
- pod troubleshooting with events and logs

### Kubernetes Skills Demonstrated

#### CKA-like Skills

- cluster operations
- networking troubleshooting
- scheduling and resource management
- storage and volume usage
- debugging broken pods and services

#### CKAD-like Skills

- application deployment
- configuration management
- probes and scaling
- service exposure
- jobs and cronjobs
- secure pod configuration

---

## 13. AWS Requirements

The project should still show AWS fluency, but in a cost-conscious way.

### AWS Services to Use

- EventBridge
- Lambda
- Step Functions
- DynamoDB
- CloudWatch Logs and Metrics
- SSM Automation or Run Command
- IAM
- KMS
- Secrets Manager
- SQS
- Optional EKS for demonstration

### AWS Skills Demonstrated

- event-driven architecture
- serverless orchestration
- IAM least privilege
- audit logging
- alert routing
- deployment automation
- short-lived environments

---

## 14. Safety and Guardrails

### Mandatory Guardrails

1. No action without scope match.
2. No action without rollback path.
3. No action if blast radius exceeds threshold.
4. No action if IAM role is missing permission or exceeds permission boundaries.
5. No action on production unless explicitly approved.
6. No auto-remediation for unknown incidents in MVP.

### Example Safety Rules

- Restart deployment only if the runbook says rollout restart is allowed.
- Scale replicas only within a bounded range.
- Never delete resources automatically in MVP.
- Never touch Secrets unless a dedicated runbook allows it.
- Require approval for actions that affect more than one workload.

---

## 15. Data Model

### Incident Record

- incident_id
- source
- severity
- environment
- namespace
- workload
- timestamps
- raw_alert
- extracted_signals
- runbook_id
- plan
- approval_status
- execution_status
- rollback_status
- audit_log_refs

### Runbook Record

- runbook_id
- title
- owner
- environment scope
- allowed tools
- forbidden tools
- steps
- rollback steps
- version
- last updated

### Policy Record

- policy_id
- runbook_id
- allowed actions
- forbidden actions
- approval rules
- risk thresholds
- IAM requirements
- blast-radius rules

---

## 16. API Surface

### Public Endpoints

- `POST /incidents` create or ingest incident
- `GET /incidents/{id}` get incident details
- `GET /incidents/{id}/plan` get remediation plan
- `POST /incidents/{id}/approve` approve a plan
- `POST /incidents/{id}/reject` reject a plan
- `POST /incidents/{id}/execute` execute approved actions
- `GET /runbooks` list runbooks
- `POST /runbooks` create or update runbook
- `GET /audit/{id}` get audit trail

### Internal Services

- compiler service
- planner service
- policy service
- executor service

---

## 17. Example Incident Workflow

### Scenario: Kubernetes pod restart loop on EKS

1. Alert fires because pod restarts repeatedly.
2. System detects the namespace and workload.
3. Runbook compiler finds the matching runbook.
4. Planner inspects events, deployment, logs, and probe settings.
5. Planner proposes two possible causes:
   - bad readiness probe,
   - insufficient CPU/memory request.
6. Policy engine checks whether rollout restart or patching probe is allowed.
7. If allowed and low-risk, the executor performs a safe action.
8. The system records all evidence, action, and rollback instructions.

### Expected Output

- root cause candidates
- confidence score
- evidence summary
- approved remediation plan
- rollback strategy
- audit log

---

## 18. MVP Definition

### MVP Goal

Build a narrow but complete version that proves the concept without expensive infrastructure.

### MVP Features

- local Kubernetes support
- 3 sample runbooks
- incident intake from a webhook or manual form
- evidence gathering from pod logs, events, and deployment describe output
- plan generation
- policy validation
- human approval
- one or two safe remediation actions
- audit trail
- dashboard showing incident timeline

### MVP Non-Features

- no production auto-delete
- no complex multi-user access model
- no enterprise SSO
- no multi-region support
- no expensive always-on EKS

---

## 19. Recommended Demo Scenarios

1. Pod crash loop because of bad environment variable.
2. Image pull failure due to wrong image tag.
3. Readiness probe misconfiguration causing traffic errors.
4. Deployment rollout causing increased error rate.
5. Optional AWS case: CloudWatch alarm triggering a safe SSM remediation on a sandbox instance.

---

## 20. Development Phases

### Phase 1: Local Prototype

- Build Markdown runbook parser.
- Build local Kubernetes incident reader.
- Generate simple remediation plans.

### Phase 2: Policy Enforcement

- Add policy engine.
- Add rollback requirements.
- Add approval workflow.

### Phase 3: AWS Integration

- Add EventBridge intake.
- Add Lambda and Step Functions orchestration.
- Add DynamoDB audit and CloudWatch logs.

### Phase 4: Kubernetes Demo / EKS Short Run

- Deploy a small EKS demo only for showcase.
- Capture screenshots and logs.
- Destroy environment after use.

---

## 21. Success Criteria

The project is successful if RunGuard can demonstrate all of the following:

- It can convert a runbook into a structured policy.
- It can explain why it thinks a problem happened.
- It can propose a safe remediation plan.
- It can reject unsafe actions.
- It can execute at least one approved low-risk action.
- It can audit everything it did.
- It can run cheaply.
- It clearly demonstrates Kubernetes and AWS competence.

---

## 22. Risks

### Technical Risks

- LLM outputs may be inconsistent.
- Tool selection may be inaccurate.
- Policy parsing may be too loose.
- AWS cost may grow if environments are left running.

### Mitigations

- Keep policy validation deterministic.
- Limit the model to plan generation, not final authority.
- Use short-lived infrastructure.
- Set AWS budgets and log retention.
- Start with only a few runbooks and a few incident types.

---

## 23. What Makes This a Strong Portfolio Project

- It aligns with real DevOps/SRE operations.
- It demonstrates Kubernetes skills directly.
- It shows AWS service knowledge.
- It includes safety, auditing, and rollback.
- It is not a generic AI demo.
- It can be explained clearly in interviews.

---

## 24. Deliverables for the Repository

- architecture diagram
- sequence diagram
- sample runbooks
- policy schema
- incident workflow demo
- Kubernetes manifests
- Terraform for AWS resources
- README with screenshots
- cost budget section
- CKA/CKAD mapping section
- AWS SAA / DevOps Pro mapping section

---

## 25. Suggested Final Product Name Ideas

- Runbook Guard
- Incident Policy Copilot
- SafeRemediate
- OpsRunbook AI
- Kubernetes Incident Planner

Recommended product name:

**RunGuard**

---

## 26. One-Sentence Pitch

RunGuard is an AI-powered Kubernetes and AWS incident remediation platform that compiles runbooks into enforceable policies, reasons over alerts and telemetry, and executes only safe, approved actions with full auditability.
