"""FastAPI service for the enterprise risk agent."""
from fastapi import FastAPI
from pydantic import BaseModel, Field

from risk_agent.core import analyze, load_documents

app = FastAPI(title="Enterprise Risk Intelligence Agent", version="0.1.0")


class AnalyzeRequest(BaseModel):
    company: str = Field(min_length=1, max_length=200)
    question: str = Field(min_length=5, max_length=2000)
    top_k: int = Field(default=4, ge=1, le=10)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/sources")
def sources():
    return [{"id": d["id"], "characters": len(d["text"])} for d in load_documents()]


@app.post("/analyze")
def analyze_risk(request: AnalyzeRequest):
    return analyze(request.company, request.question, request.top_k)
