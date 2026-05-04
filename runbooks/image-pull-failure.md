# Image Pull Failure Runbook

## Scope
- Namespaces: default, staging, production
- Workloads: *

## Allowed Tools
- fetch logs
- rollout restart

## Forbidden Tools
- delete deployment
- delete namespace

## Severity
high

## Rollback Steps
1. kubectl set image deployment/{name} {container}={previous_image} -n {namespace}
