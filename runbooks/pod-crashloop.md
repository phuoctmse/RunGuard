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
