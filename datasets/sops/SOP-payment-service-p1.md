# SOP Payment Service P1 Response

For P0 or P1 payment-service incidents, keep automation read-only until an incident commander approves remediation.
Collect alert, logs, recent deploy version, heap usage, p95 latency, 5xx rate, and gateway retries.
Safe first actions are traffic shifting, pod drain, one-at-a-time restart, and rollback to the last known good version.
Never restart every replica at once during checkout traffic.
