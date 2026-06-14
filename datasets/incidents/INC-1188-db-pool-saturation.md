# INC-1188 Database Pool Saturation

Service: orders-api
Symptoms: request timeout, database pool wait above 2 seconds, thread starvation.
Root Cause: a slow query consumed database connections and blocked application workers.
Resolution: reduce worker concurrency, recycle connection pools, disable the expensive report endpoint, escalate to DBA.
Signals: connection pool exhausted, slow query, timeout, database.
