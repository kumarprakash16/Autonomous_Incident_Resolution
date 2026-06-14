# RCA 2026-02 Release Regression

Impact: intermittent 5xx errors after version 2.8.4 deployment.
Root Cause: a feature flag enabled a new downstream validation call without timeout limits.
Resolution: rollback deployment, add downstream timeout, replay failed jobs.
Signals: deploy, release, rollback, timeout, validation service.
