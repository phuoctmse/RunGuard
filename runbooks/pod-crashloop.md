# Pod CrashLoop Runbook

## Scope
- Namespaces: default, staging
- Workloads: web-app, api-server

## Allowed Tools
- rollout restart
- scale deployment
- fetch logs

## Forbidden Tools
- delete deployment
- delete namespace

## Severity
high

## Rollback Steps
1. kubectl rollout undo deployment/{name} -n {namespace}
2. kubectl scale deployment/{name} --replicas={original_replicas} -n {namespace}
