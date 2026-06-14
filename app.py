from __future__ import annotations

import streamlit as st

from agents import orchestrate_incident
from config import DEFAULT_INCIDENT, Settings
from models import IncidentInput
from ui.components import render_metrics, render_result


st.set_page_config(page_title="AGENTS_026 Incident Agent", page_icon="A", layout="wide")

st.title("AGENTS_026 Autonomous Incident Diagnosis & Resolution")
st.caption("Multi-agent RAG workflow with Qwen/vLLM compatibility and safe offline fallback.")

settings = Settings.from_env()

with st.sidebar:
    st.header("Runtime")
    st.write(f"vLLM enabled: `{settings.use_vllm}`")
    st.write(f"Model: `{settings.vllm_model}`")
    st.write(f"RAG top-k: `{settings.top_k}`")
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
            st.session_state["incident_result"] = orchestrate_incident(
                incident,
                approval_status="approved",
                approved_by=reviewer,
                approval_notes=approval_notes,
            )
            st.rerun()
        if reject_col.button("Reject Simulation", use_container_width=True):
            st.session_state["incident_result"] = orchestrate_incident(
                incident,
                approval_status="rejected",
                approved_by=reviewer,
                approval_notes=approval_notes,
            )
            st.rerun()

        render_result(st.session_state["incident_result"])
