# Requirements Document — RunGuard

## Introduction

RunGuard is an AI-powered DevOps/SRE incident remediation platform. The system combines four core layers: a runbook compiler, an incident reasoning engine, a safety policy engine, and a remediation executor. The goal is to convert Markdown runbooks into machine-executable policies, investigate incidents from multiple signal sources, propose safe remediation plans, and execute only approved actions with a complete audit trail.

---

## Glossary

- **RunGuard**: The overall system described in this document.
- **Runbook_Compiler**: The component responsible for parsing and converting Markdown runbooks into structured JSON policies.
- **Incident_Reasoner**: The component that reasons about root causes and proposes remediation plans based on collected evidence.
- **Policy_Engine**: The component that validates every proposed action against safety rules, scope constraints, and permission boundaries.
- **Remediation_Executor**: The component that executes approved actions against Kubernetes and AWS infrastructure.
- **Audit_Store**: The component that persists the complete audit log for every incident and action.
- **Approval_Workflow**: The process that requires human approval before executing medium- or high-risk actions.
- **Runbook**: A Markdown document describing the procedure for handling a specific incident type, including scope, allowed tools, execution steps, and rollback steps.
- **Policy**: A structured JSON representation of a Runbook containing machine-enforceable action constraints.
- **Incident**: An anomalous event detected by a monitoring system that requires investigation and resolution.
- **Remediation_Plan**: A prioritized list of actions proposed to resolve an Incident.
- **Blast_Radius**: An estimate of the impact scope of a remediation action on the system.
- **Rollback_Path**: The set of undo steps that can be executed if an action produces unintended consequences.
- **Dry_Run**: A simulation mode that previews action outcomes without changing system state.
- **Scope**: The set of namespaces, workloads, or resources that a Runbook is permitted to affect.
- **MCP**: Model Context Protocol — a standardized protocol for AI tool integration, enabling LLMs to invoke external tools through a unified interface.
- **GitOps**: A operational pattern where Git repositories are the single source of truth for declarative infrastructure and application configuration.
- **Terraform_Backend**: The remote storage location (S3 + DynamoDB) where Terraform state is persisted, enabling team collaboration and state locking.

---

## Requirements

### Requirement 1: Runbook Parsing and Compilation

**User Story:** As a DevOps engineer, I want to upload a Markdown runbook so the system automatically converts it into a structured policy, enabling machines to enforce constraints without manual document reading.

#### Acceptance Criteria

1. WHEN a valid Markdown file is loaded, THE Runbook_Compiler SHALL extract metadata fields including: title, scope, allowed tools list, forbidden tools list, severity level, and rollback steps.
2. WHEN metadata extraction completes, THE Runbook_Compiler SHALL produce a JSON Policy file conforming to the defined schema.
3. WHEN a Markdown file does not contain a rollback section, THEN THE Runbook_Compiler SHALL reject compilation and return an error message describing the missing field.
4. WHEN a Runbook is updated, THE Runbook_Compiler SHALL create a new version of the Policy and retain the previous version for reference.
5. THE Runbook_Compiler SHALL support round-trip parsing: for every valid JSON Policy produced, converting it back to Markdown and recompiling SHALL yield a Policy equivalent to the original.
6. WHEN a Markdown file contains invalid syntax, THEN THE Runbook_Compiler SHALL return an error message describing the location and type of the syntax error.

---

### Requirement 2: Incident Intake from Multiple Sources

**User Story:** As an SRE, I want the system to automatically receive alerts from Kubernetes, CloudWatch, and Prometheus so I do not have to manually enter incidents every time an issue occurs.

#### Acceptance Criteria

1. WHEN a webhook from Prometheus Alertmanager is sent to the `/incidents` endpoint, THE RunGuard SHALL create a new Incident record with status `pending`.
2. WHEN a CloudWatch Alarm transitions to `ALARM` state and is routed via EventBridge, THE RunGuard SHALL create a new Incident record with status `pending`.
3. WHEN an engineer sends `POST /incidents` with a payload describing a manual incident, THE RunGuard SHALL create a new Incident record with status `pending`.
4. WHEN an Incident is created from any source, THE RunGuard SHALL assign a unique `incident_id` and record the intake timestamp.
5. IF a webhook payload is malformed or missing required fields, THEN THE RunGuard SHALL return HTTP 400 with a message describing the missing fields and SHALL NOT create an Incident record.
6. WHILE an Incident is in `pending` status, THE RunGuard SHALL NOT allow creation of a duplicate Incident record from the same alert source within 60 seconds.

---

### Requirement 3: Incident Reasoning and Remediation Plan Proposal

**User Story:** As a DevOps engineer, I want the system to automatically analyze evidence from infrastructure and propose a ranked remediation plan so I can make decisions faster instead of investigating from scratch.

#### Acceptance Criteria

1. WHEN an Incident is received, THE Incident_Reasoner SHALL collect evidence from at least one of the following sources: pod logs, Kubernetes events, deployment describe output, or CloudWatch metrics.
2. WHEN evidence collection completes, THE Incident_Reasoner SHALL produce a natural-language incident summary describing the observed symptoms.
3. WHEN the summary is produced, THE Incident_Reasoner SHALL propose at least one possible root cause with a confidence score between 0.0 and 1.0.
4. WHEN a root cause is identified, THE Incident_Reasoner SHALL produce a Remediation_Plan containing a prioritized list of actions.
5. THE Incident_Reasoner SHALL cite the specific evidence (log line, event, metric) that influenced each conclusion in the Remediation_Plan.
6. IF no Runbook matching the incident type is found, THEN THE Incident_Reasoner SHALL produce a read-only Remediation_Plan and mark the plan as `unmatched_runbook`.
7. WHEN collecting evidence from Kubernetes, THE Incident_Reasoner SHALL complete within 30 seconds or return partial results with a timeout warning.

---

### Requirement 4: Safety Policy Validation

**User Story:** As a Platform engineer, I want every remediation action to pass policy checks before execution, ensuring no action exceeds its permitted scope or produces irreversible consequences.

#### Acceptance Criteria

1. WHEN a Remediation_Plan is produced, THE Policy_Engine SHALL validate each action in the plan against the Scope defined in the corresponding Runbook.
2. IF an action in the plan affects a namespace or workload outside the Runbook's Scope, THEN THE Policy_Engine SHALL mark that action as `blocked` and record the violation reason.
3. IF an action has no defined Rollback_Path, THEN THE Policy_Engine SHALL mark that action as `blocked` with reason `missing_rollback`.
4. IF the estimated Blast_Radius of an action exceeds the threshold configured in the Policy, THEN THE Policy_Engine SHALL mark that action as `requires_approval`.
5. IF the IAM permissions required to execute an action do not exist or exceed permission boundaries, THEN THE Policy_Engine SHALL mark that action as `blocked` with reason `insufficient_iam`.
6. WHILE the environment is identified as `production`, THE Policy_Engine SHALL require manual approval for every action regardless of risk level.
7. THE Policy_Engine SHALL complete validation of the entire Remediation_Plan within 5 seconds.
8. WHEN validation completes, THE Policy_Engine SHALL return a classification result for each action: `approved`, `requires_approval`, or `blocked`.

---

### Requirement 5: Human Approval Workflow

**User Story:** As an SRE, I want to be notified and have the ability to approve or reject medium- and high-risk actions so I always maintain control over what the system does to infrastructure.

#### Acceptance Criteria

1. WHEN an action is classified as `requires_approval`, THE Approval_Workflow SHALL send a notification to the configured Slack channel or SNS topic, including an action summary and the reason approval is required.
2. WHEN an engineer sends `POST /incidents/{id}/approve`, THE Approval_Workflow SHALL transition the action status to `approved` and record the approver identity and approval timestamp.
3. WHEN an engineer sends `POST /incidents/{id}/reject`, THE Approval_Workflow SHALL transition the action status to `rejected` and SHALL NOT allow execution of that action.
4. IF a `requires_approval` action receives no response within 30 minutes, THEN THE Approval_Workflow SHALL automatically transition the status to `expired` and SHALL NOT execute the action.
5. THE Approval_Workflow SHALL NOT allow the same person to both propose and approve an action within the same Incident.
6. WHEN an action is classified as `approved` by the Policy_Engine (low risk), THE Approval_Workflow SHALL allow immediate execution without manual approval.

---

### Requirement 6: Remediation Action Execution

**User Story:** As a DevOps engineer, I want the system to execute approved remediation actions safely, with the ability to dry-run before applying changes to production.

#### Acceptance Criteria

1. WHEN an action is approved and `dry_run` mode is enabled, THE Remediation_Executor SHALL simulate the action and return the expected outcome without changing system state.
2. WHEN a `rollout restart` action is approved, THE Remediation_Executor SHALL execute the restart on the correct Deployment in the specified namespace.
3. WHEN a `scale deployment` action is approved, THE Remediation_Executor SHALL adjust the replica count within the bounds defined in the Policy (not exceeding the configured maximum or minimum).
4. WHEN a `fetch logs` action is executed, THE Remediation_Executor SHALL retrieve logs from the specified pod and store the result in the Audit_Store.
5. WHEN an AWS SSM document action is approved, THE Remediation_Executor SHALL trigger the SSM document on the specified target instance and record the execution ID.
6. IF an action execution fails, THEN THE Remediation_Executor SHALL record the detailed error, mark the action as `failed`, and trigger a notification to the configured channel.
7. THE Remediation_Executor SHALL NOT execute any action with a status other than `approved`.
8. THE Remediation_Executor SHALL NOT delete Kubernetes or AWS resources within the MVP scope.

---

### Requirement 7: Comprehensive Audit Trail

**User Story:** As a Platform engineer, I want a complete audit log for every incident and action so I can review any decision and satisfy audit requirements.

#### Acceptance Criteria

1. WHEN an Incident is created, THE Audit_Store SHALL record: `incident_id`, alert source, intake timestamp, environment, namespace, and related workload.
2. WHEN a Remediation_Plan is produced, THE Audit_Store SHALL record: the `runbook_id` used, the list of proposed root causes, confidence scores, and cited evidence.
3. WHEN an action is executed or rejected, THE Audit_Store SHALL record: action status, approver or rejector identity (if applicable), timestamp, and execution result.
4. THE Audit_Store SHALL store the Rollback_Path for every successfully executed action.
5. WHEN an engineer sends `GET /audit/{id}`, THE Audit_Store SHALL return the complete history of the corresponding Incident in chronological order.
6. THE Audit_Store SHALL NOT allow deletion or modification of any audit record once created.
7. WHILE the system is operating, THE Audit_Store SHALL ensure every record is successfully written before the corresponding action is executed.

---

### Requirement 8: User Interface and Dashboard

**User Story:** As an SRE, I want a web interface to view incident status, review remediation plans, and perform approvals without using the API directly.

#### Acceptance Criteria

1. THE RunGuard SHALL provide a web interface displaying a chronological list of Incidents with the current status of each.
2. WHEN an engineer selects an Incident, THE RunGuard SHALL display: incident summary, collected evidence, proposed Remediation_Plan, and the status of each action.
3. WHEN an action with status `requires_approval` is displayed, THE RunGuard SHALL provide "Approve" and "Reject" buttons directly in the interface.
4. THE RunGuard SHALL display a timeline for each Incident including all events from intake to closure.
5. WHERE `dry_run` mode is enabled, THE RunGuard SHALL display a clear label in the interface to distinguish it from live execution mode.

---

### Requirement 9: Kubernetes Integration

**User Story:** As a DevOps engineer, I want the system to connect directly to a Kubernetes cluster to collect evidence and execute actions without requiring complex agent installation.

#### Acceptance Criteria

1. THE RunGuard SHALL support connection to a local Kubernetes cluster (kind or k3d) via standard kubeconfig.
2. WHEN collecting evidence, THE Incident_Reasoner SHALL be able to query: pod logs, Kubernetes events, deployment status, and pod describe output.
3. WHEN executing Kubernetes actions, THE Remediation_Executor SHALL use a ServiceAccount with the minimum required permissions (least privilege) for each action type.
4. IF the connection to the Kubernetes API is interrupted, THEN THE RunGuard SHALL fall back to read-only mode using previously collected data and notify the user of the connection status.
5. THE RunGuard SHALL enforce namespace isolation: actions SHALL only be executed within namespaces defined in the Runbook's Scope.

---

### Requirement 10: AWS Integration

**User Story:** As a Platform engineer, I want the system to integrate with AWS services to receive automated alerts and execute remediation actions on AWS infrastructure when needed.

#### Acceptance Criteria

1. WHEN a CloudWatch Alarm transitions to `ALARM` state, THE RunGuard SHALL receive the event via an EventBridge rule and create the corresponding Incident within 60 seconds.
2. WHEN an AWS SSM action is approved, THE Remediation_Executor SHALL use an IAM role with minimum required permissions to trigger the SSM document and SHALL NOT use long-lived credentials.
3. THE Audit_Store SHALL store Incident data in DynamoDB with a configured TTL to control storage costs.
4. THE RunGuard SHALL use AWS Secrets Manager or Kubernetes Secrets to store credentials and SHALL NOT store credentials as plaintext in configuration.
5. IF the AI/LLM service is unavailable, THEN THE RunGuard SHALL still allow evidence collection and display raw data without automatically generating a Remediation_Plan.
6. WHERE an EKS environment is used, THE RunGuard SHALL support authentication via IRSA (IAM Roles for Service Accounts) instead of node-level IAM roles.

---

### Requirement 11: System Reliability and Fail-Safe Behavior

**User Story:** As a Platform engineer, I want the system to operate on a fail-safe principle, meaning that when an error occurs the system must stop safely rather than continuing to execute potentially harmful actions.

#### Acceptance Criteria

1. IF the Policy_Engine cannot complete validation due to an internal error, THEN THE RunGuard SHALL refuse to execute any action in the corresponding Remediation_Plan and record the error.
2. IF the Remediation_Executor encounters an error while executing one action in a multi-action sequence, THEN THE RunGuard SHALL stop executing subsequent actions and wait for manual approval to continue or rollback.
3. THE RunGuard SHALL NOT write credentials, tokens, or secrets as plaintext to any log.
4. WHEN a rollback action is triggered, THE Remediation_Executor SHALL execute rollback steps in the reverse order of the original execution sequence.
5. THE RunGuard SHALL limit the number of auto-approved actions executed within a single Incident to a maximum of 5; subsequent actions SHALL require manual approval.

---

### Requirement 12: Infrastructure Cost Control

**User Story:** As a DevOps engineer, I want the system designed to minimize AWS costs, especially during development and demo phases.

#### Acceptance Criteria

1. THE RunGuard SHALL prefer local Kubernetes (kind or k3d) for all development and testing activities and SHALL NOT require EKS to be running continuously.
2. THE RunGuard SHALL use a serverless AWS architecture (Lambda, Step Functions) for the control plane instead of always-on EC2 instances.
3. WHERE EKS resources are created for demo purposes, THE RunGuard SHALL provide a Terraform script to automatically destroy all resources after the demo concludes.
4. THE Audit_Store SHALL configure TTL for DynamoDB data and log retention for CloudWatch Logs to prevent uncontrolled storage cost accumulation.
5. THE RunGuard SHALL integrate with AWS Cost Explorer API to track cost per incident and display cost estimates in the Audit_Store.
6. WHERE OpenCost or Kubecost is available in the cluster, THE RunGuard SHALL query namespace-level cost data and include it in the remediation plan impact analysis.

---

### Requirement 13: LLM/AI Integration Layer

**User Story:** As a Platform engineer, I want the AI reasoning component to use a production-grade LLM with cost controls, caching, and graceful degradation, ensuring the system remains usable even when AI is unavailable.

#### Acceptance Criteria

1. THE RunGuard SHALL use Claude API (Anthropic) or Amazon Bedrock as the primary LLM provider for incident reasoning and plan generation.
2. THE RunGuard SHALL implement prompt caching to reduce token costs on repeated incident types with similar evidence patterns.
3. THE RunGuard SHALL enforce a per-incident token budget limit (configurable, default 10,000 input tokens, 2,000 output tokens) and SHALL NOT exceed it.
4. IF the primary LLM provider is unavailable, THEN the RunGuard SHALL fall back to Amazon Bedrock (if configured) or return raw evidence without a generated plan.
5. THE RunGuard SHALL log token usage per incident in the Audit_Store for cost tracking.
6. THE RunGuard SHALL NOT send secrets, credentials, or raw sensitive data in LLM prompts; all sensitive values SHALL be redacted before sending to the LLM.
7. WHEN generating remediation plans, THE RunGuard SHALL use structured output (JSON schema) from the LLM to ensure deterministic parsing.

---

### Requirement 14: Model Context Protocol (MCP) Support

**User Story:** As a DevOps engineer, I want the system to use MCP for standardized AI tool integration, enabling the LLM to invoke K8s and AWS tools through a unified protocol.

#### Acceptance Criteria

1. THE RunGuard SHALL implement MCP server endpoints for K8s operations (pod logs, events, deployment status, describe) and AWS operations (CloudWatch metrics, SSM trigger).
2. WHEN the LLM needs to collect evidence, THE RunGuard SHALL use MCP tool calls rather than hardcoded API invocations.
3. THE RunGuard SHALL support MCP client connections for external tools or UIs to query incident state and remediation plans.
4. MCP tool definitions SHALL include descriptions, parameter schemas, and required permissions metadata.
5. THE RunGuard SHALL enforce policy checks on MCP tool calls before execution, applying the same guardrails as direct API calls.

---

### Requirement 15: GitOps Integration

**User Story:** As a Platform engineer, I want the system to support GitOps-based remediation for Kubernetes, enabling declarative infrastructure changes tracked through Git.

#### Acceptance Criteria

1. WHERE Flux or ArgoCD is installed in the cluster, THE RunGuard SHALL support remediation by updating Git manifests and triggering reconciliation instead of direct API calls.
2. WHEN a GitOps remediation is proposed, THE RunGuard SHALL generate a Git commit or pull request with the proposed change and record the commit hash in the Audit_Store.
3. THE RunGuard SHALL NOT directly modify cluster state when GitOps mode is enabled; all changes SHALL flow through the Git repository.
4. IF GitOps reconciliation fails, THEN the RunGuard SHALL record the failure and notify the configured channel.

---

### Requirement 16: Terraform State Management

**User Story:** As a DevOps engineer, I want the system to manage Terraform state for AWS resources, enabling auditable infrastructure changes and proper state isolation.

#### Acceptance Criteria

1. THE RunGuard SHALL use a remote Terraform backend (S3 + DynamoDB locking) for all AWS infrastructure state.
2. WHEN proposing infrastructure changes, THE RunGuard SHALL run `terraform plan` in dry-run mode and include the plan output in the Remediation_Plan.
3. IF `terraform apply` is approved, THEN the RunGuard SHALL execute the change and record the apply output and state version in the Audit_Store.
4. THE RunGuard SHALL enforce state locking to prevent concurrent modifications to the same infrastructure.
5. THE RunGuard SHALL provide a `terraform destroy` script for demo environments with a confirmation prompt before execution.

---

### Requirement 17: MVP Phasing and Incremental Delivery

**User Story:** As a developer, I want the MVP to be delivered in incremental phases so each phase is testable and demonstrable independently.

#### Acceptance Criteria

1. **Phase 1 — Core (Local):** Runbook parser + K8s evidence collector + basic plan generator + simple audit log. All running locally with kind/k3d.
2. **Phase 2 — Safety:** Policy engine + approval workflow + rollback support. Extends Phase 1.
3. **Phase 3 — AWS:** EventBridge intake + Lambda/Step Functions orchestration + DynamoDB audit. Extends Phase 2.
4. **Phase 4 — Polish:** Dashboard UI + MCP integration + GitOps support + cost tracking. Extends Phase 3.
5. Each phase SHALL produce a working demo that can be shown independently.
6. Phase 1 SHALL be completable within 2 weeks of focused development.
7. The RunGuard SHALL maintain a CHANGELOG documenting which features belong to which phase.
 