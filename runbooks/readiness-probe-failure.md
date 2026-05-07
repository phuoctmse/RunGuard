# Readiness Probe Failure Runbook

## Scope
- Namespaces: default, staging
- Workloads: web-app, api-server

## Allowed Tools
- fetch_logs
- scale_replicas

## Forbidden Tools
- delete_pod
- patch_config

## Severity
medium

## Rollback Steps
1. kubectl rollout undo deployment/{name} -n {namespace}
2. kubectl scale deployment/{name} --replicas={original_replicas} -n {namespace}
