# RCA 2025-11 Checkout Heap Exhaustion

Impact: 17 minutes of elevated checkout errors.
Root Cause: a cache eviction regression retained pricing objects until the payment-service heap was exhausted.
Detection: OutOfMemoryError logs appeared three minutes before gateway retries amplified traffic.
Corrective Actions: add heap alerting, limit pricing cache size, document drain-and-restart recovery steps.
