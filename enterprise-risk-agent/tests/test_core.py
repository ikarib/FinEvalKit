from risk_agent.core import analyze, retrieve


DOCS = [
    {"id": "rates", "text": "Higher interest rates increase borrowing and refinancing costs."},
    {"id": "fx", "text": "Currency appreciation reduces exporter revenue in local currency."},
]


def test_retrieval_returns_relevant_source():
    result = retrieve("interest rates borrowing costs", DOCS)
    assert result and result[0]["id"] == "rates"


def test_demo_produces_valid_source_citations(monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "true")
    result = analyze("ExampleCo", "How do interest rates affect borrowing costs?", documents=DOCS)
    assert result["status"] == "complete"
    assert result["citations_valid"]
    assert "rates" in result["sources"]


def test_abstain_when_no_evidence():
    result = analyze("ExampleCo", "Discuss Antarctic penguin migration", documents=DOCS)
    assert result["status"] == "insufficient_evidence"
    assert result["sources"] == []
