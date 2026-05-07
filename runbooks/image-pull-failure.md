# Image Pull Failure Runbook

## Scope
- Namespaces: default, staging, production
- Workloads: *

## Allowed Tools
- fetch_logs
- rollout_restart

## Forbidden Tools
- delete_pod
- delete_deployment

## Severity
high

## Rollback Steps
1. kubectl set image deployment/{name} {container}={previous_image} -n {namespace}
