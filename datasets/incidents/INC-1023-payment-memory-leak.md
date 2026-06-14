# INC-1023 Payment Service Memory Leak

Service: payment-service
Symptoms: checkout latency above 4 seconds, HTTP 5xx increase, retry storm from gateway.
Root Cause: memory leak in cart pricing cache exhausted JVM heap after a promotion traffic spike.
Resolution: drain unhealthy pods, restart affected payment-service replicas, cap cache size, monitor p95 latency and heap usage.
Signals: OutOfMemoryError, heap exhausted, connection pool exhausted, retry storm.
