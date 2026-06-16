# Autonomous Incident Resolution System

Production-oriented Streamlit application for autonomous incident diagnosis and safe remediation simulation. The workflow is multi-agent, RAG-backed, human-gated, and provider-configurable.

## Architecture

Incident Submission -> Detection Agent -> Retrieval Agent -> RCA Agent -> Recommendation Agent -> Approval Agent -> Execution Agent -> Final Report

The execution step is simulation only. No real infrastructure changes are performed.

## LLM Providers

Gemini is the default provider.

```bash
export GEMINI_API_KEY="..."
export LLM_PROVIDER="gemini"
export GEMINI_MODEL="gemini-2.5-flash-lite"
```

Switch to Ollama without code changes:

```bash
export LLM_PROVIDER="ollama"
export OLLAMA_MODEL="qwen2.5:7b"
export OLLAMA_BASE_URL="http://localhost:11434"
```

If the configured provider is unavailable and `ALLOW_OFFLINE_FALLBACK=true`, the app falls back to deterministic local RCA logic so the demo remains end-to-end runnable.

## RAG

- Embeddings: `BAAI/bge-small-en-v1.5`
- Vector store: FAISS when `faiss-cpu` and `sentence-transformers` are installed
- Reranker: `BAAI/bge-reranker-base` cross-encoder when available
- Fallback: lexical search and lexical reranking for constrained environments
- Documents: markdown knowledge base under `datasets/` and JSON incidents under `data/incidents/`

Use the Streamlit sidebar button to re-index the knowledge base.

## Quick Start

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

CLI smoke test:

```bash
python3 run_demo.py
```

Tests:

```bash
python3 -m pytest -q
```

## Metrics

Each workflow records latency, similarity, rerank score, retrieval accuracy, RCA confidence, and execution status. Runtime metrics are appended to `data/metrics/workflow_metrics.jsonl`.

## Project Structure

```text
agents/
rag/
llm/
data/
datasets/
evaluation/
tests/
ui/
```

P0 → Entire system down
P1 → Major customer impact
P2 → Partial degradation
P3 → Minor issue
