# RUNBOOK Database Pool Recovery

1. Check database health, slow queries, and connection pool utilization.
2. Reduce service worker concurrency if pool wait time is above threshold.
3. Recycle saturated pools one replica at a time.
4. Disable non-critical report endpoints if they are consuming connections.
5. Escalate to DBA if saturation remains above threshold.
