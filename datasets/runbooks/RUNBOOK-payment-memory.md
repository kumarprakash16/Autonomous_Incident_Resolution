# RUNBOOK Payment Memory Recovery

1. Confirm heap pressure with service metrics and OutOfMemoryError logs.
2. Shift a small percentage of checkout traffic away from unhealthy pods.
3. Drain one affected pod and wait for in-flight requests to complete.
4. Restart the drained pod and verify readiness, p95 latency, and 5xx rate.
5. Repeat only for replicas that continue to show heap pressure.
6. Roll back traffic shift after 10 minutes of stable metrics.
