
import streamlit as st
import requests

st.title("AutoHeal AI")

service = st.text_input("Service", "payment-service")
alert = st.text_area("Alert", "CPU > 95%")
logs = st.text_area("Logs", "OutOfMemoryError")

if st.button("Analyze Incident"):
    r = requests.post(
        "http://localhost:8000/incident",
        json={"service": service, "alert": alert, "logs": logs}
    )
    st.json(r.json())
