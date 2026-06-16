from __future__ import annotations

import streamlit as st

from models import IncidentResult


def render_metrics(result: IncidentResult) -> None:
    metrics = result.metrics
    cols = st.columns(4)
    cols[0].metric("Detection", f"{metrics.detection_latency_ms:.1f} ms")
    cols[1].metric("Retrieval", f"{metrics.retrieval_latency_ms:.1f} ms")
    cols[2].metric("RCA", f"{metrics.rca_latency_ms:.1f} ms")
    cols[3].metric("Total", f"{metrics.total_workflow_latency_ms:.1f} ms")

    cols = st.columns(3)
    cols[0].metric("Similarity", f"{metrics.similarity_score:.2f}")
    cols[1].metric("Retrieval Accuracy", f"{metrics.retrieval_accuracy:.2f}")
    cols[2].metric("RCA Confidence", f"{metrics.rca_confidence_score:.2f}")


def render_result(result: IncidentResult) -> None:
    st.subheader("Agent Trace")
    with st.expander("Detection Agent", expanded=True):
        st.json(
            {
                "service": result.detected.service,
                "severity": result.detected.severity,
                "symptoms": result.detected.symptoms,
                "keywords": result.detected.raw_keywords,
                "normalized_summary": result.detected.normalized_summary,
            }
        )

    with st.expander("Retrieval Agent", expanded=True):
        for doc in result.evidence:
            st.markdown(
                f"**{doc.title}**  \n"
                f"`{doc.source_type}` | vector score `{doc.score:.2f}` | rerank `{doc.rerank_score:.2f}`"
            )
            st.caption(doc.path)

    with st.expander("RCA Agent", expanded=True):
        st.markdown(f"**Likely root cause:** {result.rca.root_cause}")
        st.progress(min(1.0, max(0.0, result.rca.confidence)))
        st.caption(
            f"Model: {result.rca.model_used} | Offline fallback: {result.rca.offline_fallback}"
        )
        st.write(result.rca.reasoning)
        st.json({"contributing_factors": result.rca.contributing_factors})

    st.subheader("Recommended Remediation")
    st.markdown(f"**Action:** {result.recommendation.action_summary}")
    st.markdown(f"**Risk:** {result.recommendation.risk_level}")
    st.markdown("**Immediate mitigation**")
    for step in result.recommendation.immediate_mitigation:
        st.checkbox(step, value=True, disabled=True)
    st.markdown("**Long-term fix**")
    for step in result.recommendation.long_term_fix:
        st.write(f"- {step}")
    st.markdown("**Monitoring improvements**")
    for step in result.recommendation.monitoring_improvements:
        st.write(f"- {step}")
    st.info(f"Rollback plan: {result.recommendation.rollback_plan}")

    st.subheader("Execution Simulation")
    st.markdown(f"**Status:** {result.execution.status}")
    st.write(result.execution.details)
    if result.execution.actions_executed:
        st.code("\n".join(result.execution.actions_executed), language="text")

    st.subheader("Retrieved Evidence")
    for doc in result.evidence:
        with st.expander(f"{doc.title} | {doc.source_type} | score {doc.score:.2f}"):
            st.caption(doc.path)
            st.write(doc.content)

    st.subheader("Explainability")
    st.caption(f"Report ID: {result.report_id}")
    for item in result.explanation:
        st.write(f"- {item}")
