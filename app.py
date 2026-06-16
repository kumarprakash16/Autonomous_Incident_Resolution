from __future__ import annotations

import streamlit as st

from agents import orchestrate_incident
from config import DEFAULT_INCIDENT, Settings
from models import IncidentInput
from rag import RagRetriever
from ui.components import render_metrics, render_result


st.set_page_config(page_title="Autonomous Incident Resolution", page_icon="A", layout="wide")

st.title("Autonomous Incident Resolution System")
st.caption("Detection, retrieval, RCA, recommendation, human approval, and simulated execution.")

settings = Settings.from_env()

with st.sidebar:
    st.header("Runtime")
    st.write(f"LLM provider: `{settings.llm_provider}`")
    model = settings.gemini_model if settings.llm_provider == "gemini" else settings.ollama_model
    st.write(f"Model: `{model}`")
    st.write(f"Embedding: `{settings.embedding_model}`")
    st.write(f"Reranker: `{settings.reranker_model}`")
    st.write(f"RAG top-k: `{settings.top_k}`")
    if st.button("Re-index Knowledge Base", use_container_width=True):
        with st.spinner("Rebuilding retrieval index..."):
            RagRetriever(settings=settings).reindex()
        st.success("Knowledge base indexed.")
    st.divider()
    st.header("Human Approval")
    reviewer = st.text_input("Reviewer", "incident-commander")
    approval_notes = st.text_area("Approval notes", "Demo approval after reviewing RCA evidence.")

left, right = st.columns([0.38, 0.62], gap="large")

with left:
    st.subheader("Synthetic Incident")
    service = st.text_input("Service", DEFAULT_INCIDENT["service"])
    severity = st.selectbox("Severity", ["P0", "P1", "P2", "P3"], index=1)
    environment = st.selectbox("Environment", ["production", "staging", "development"], index=0)
    alert = st.text_area("Alert", DEFAULT_INCIDENT["alert"], height=90)
    logs = st.text_area("Logs", DEFAULT_INCIDENT["logs"], height=220)

    analyze = st.button("Analyze Incident", type="primary", use_container_width=True)

incident = IncidentInput(
    service=service,
    alert=alert,
    logs=logs,
    severity=severity,
    environment=environment,
)

if analyze:
    with st.spinner("Agents are resolving the incident..."):
        st.session_state["incident_result"] = orchestrate_incident(incident)

with right:
    if "incident_result" not in st.session_state:
        st.info("Run the synthetic incident to start the diagnosis workflow.")
    else:
        result = st.session_state["incident_result"]
        render_metrics(result)

        st.subheader("Approval Gate")
        st.write(
            "Automation is paused until a human reviewer approves or rejects the remediation."
        )
        approve_col, reject_col = st.columns(2)
        if approve_col.button("Approve Simulation", use_container_width=True):
            with st.spinner("Running approved simulation..."):
                st.session_state["incident_result"] = orchestrate_incident(
                    incident,
                    approval_status="approved",
                    approved_by=reviewer,
                    approval_notes=approval_notes,
                )
            st.rerun()
        if reject_col.button("Reject Simulation", use_container_width=True):
            with st.spinner("Recording rejection..."):
                st.session_state["incident_result"] = orchestrate_incident(
                    incident,
                    approval_status="rejected",
                    approved_by=reviewer,
                    approval_notes=approval_notes,
                )
            st.rerun()

        render_result(st.session_state["incident_result"])
