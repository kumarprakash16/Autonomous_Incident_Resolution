
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="AutoHeal AI")

class Incident(BaseModel):
    service: str
    alert: str
    logs: str

@app.post("/incident")
def process_incident(incident: Incident):
    return {
        "service": incident.service,
        "root_cause": "Possible memory leak",
        "resolution": "Restart service and monitor metrics",
        "status": "Resolved (Demo)"
    }
