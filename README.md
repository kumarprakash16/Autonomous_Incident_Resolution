# AGENTS_026 - Autonomous Incident Diagnosis & Resolution Agent

Hackathon-ready Streamlit demo using multi-agent orchestration, local RAG retrieval, Qwen/vLLM-compatible LLM calls, safe offline fallback, human approval, execution simulation, explainability, and metrics.

## Quick Start

```bash

python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

In a managed AMD/Jupyter environment, you can also run:

```bash
python run_demo.py
```

## Demo Flow

Synthetic Incident -> Detection Agent -> RAG Retrieval Agent -> RCA Agent -> Recommendation Agent -> Approval Agent -> Execution Simulation Agent -> Explainability + Metrics

## Qwen/vLLM Integration

The project works out of the box in offline demo mode. To connect to a local vLLM OpenAI-compatible endpoint:

```bash
$env:USE_VLLM="true"
$env:VLLM_BASE_URL="http://localhost:8000/v1/chat/completions"
$env:VLLM_MODEL="Qwen/Qwen2.5-7B-Instruct"
streamlit run app.py
```

If the endpoint is unavailable, the app automatically falls back to a deterministic local RCA generator.

## Project Structure

```text
AGENTS_026_project/
├── app.py
├── run_demo.py
├── config.py
├── models.py
├── requirements.txt
├── notebook.ipynb
├── agents/
├── rag/
├── llm/
├── datasets/
├── evaluation/
├── assets/
├── tests/
└── ui/
```

## Metrics Shown

- Detection latency
- Retrieval latency
- RCA generation latency
- Total workflow latency
- Similarity score
- RCA confidence score
- Simulated resolution status

## Testing

```bash
pytest
python run_demo.py
```

