# Enterprise Risk Intelligence Agent

A portfolio-ready, evidence-grounded enterprise risk analyst built with **LangGraph**, **LangChain**, **FastAPI**, and local TF-IDF document retrieval. Includes an offline deterministic demo, optional Azure OpenAI/OpenAI synthesis, citations, basic hallucination checks, and automated tests.

> **Status:** prototype, not a production service or financial advice. Example documents are synthetic, not live market intelligence.

## Architecture
```
POST /analyze -> retrieve (TF-IDF) -> assess_evidence -> draft (LLM or demo)
                                              |              |
                                              +-- no evidence -> abstain
                                                             |
                                                   verify citations -> response
```

## Run locally
Requires Python 3.11+.
```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
uvicorn risk_agent.api:app --reload
```
Open http://127.0.0.1:8000/docs and send:
```json
{"company":"Prairie Manufacturing","question":"How do higher policy rates and a stronger dollar affect this company?","top_k":4}
```
By default `DEMO_MODE=true` produces a deterministic, evidence-based demonstration without an API key. Unknown questions **abstain** if the retrieved documents fail the relevance threshold.

## Enable an actual LLM
Set `DEMO_MODE=false`. For OpenAI: set `OPENAI_API_KEY` and optionally `OPENAI_MODEL`. For Azure OpenAI set `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_API_VERSION`, `AZURE_OPENAI_DEPLOYMENT`. Azure takes precedence if configured. Never commit secrets or real sensitive documents.

## Ingest source documents
Store UTF-8 `.txt` files in `data/documents/`. Each filename becomes a source ID. Retrieval uses word + bigram TF-IDF; the included documents are **synthetic illustrative scenarios**. Future work: pgvector ingestion, live source connectors, document versioning and access controls.

## API
- `GET /health` health check
- `POST /analyze` evidence-backed question and risk memo
- `GET /sources` indexed source listing

`/analyze` returns `status`, `memo`, `sources`, `citations_valid` and `retrieval_scores`. A citation whitelist validates source IDs, **not** the semantic accuracy of claims. Human review remains necessary.

## Quality gates
```bash
pytest -q
ruff check .
```
GitHub Actions runs unit tests on pushes and pull requests. The offline demo is intentionally reproducible; it should not be confused with real model evaluation.

## Roadmap
1. Persist embeddings in pgvector, maintain metadata and document provenance.
2. Integrate authoritative time-stamped macro series and corporate filings.
3. Add evaluation dataset for citation precision, abstention, groundedness and latency.
4. Add OpenTelemetry traces, MLflow experiment tracking, authentication and rate limits.
5. Deploy container to Azure Container Apps, monitor spend and failure rates.
