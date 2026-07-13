# Inventory Replenishment RAG Agent

Automated e-commerce inventory replenishment system with predictive demand modeling, supplier selection, and human-in-the-loop escalation.

## Architecture

```
Stock Level Monitor (Cron / API Trigger)
    |
    v
Predictive Demand Model (LLM + Vector KB)
    |
    v
Purchase Order Evaluator (Conditional Router)
    |                           |
    v                           v
  END (no deficit)      Procurement Sub-Graph
                              |
                              v
                        Supplier Selection (Vector Search)
                              |
                              v
                        Order Generation
                              |
                              v
                        Escalation Check
                          |         |
                          v         v
                    END (auto)   Manager Approval (HITL)
                                    |
                                    v
                                  END
```

## Quick Start

```bash
make install
make seed         # seed mock supplier data into vector KB
make dev          # uvicorn with hot reload
```

## Usage

```bash
# Trigger a stock audit
curl -X POST http://localhost:8000/audit \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-local-key" \
  -d '{}'

# Approve an escalation
curl -X POST http://localhost:8000/audit/{audit_id}/approve \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-local-key" \
  -d '{"approved": true}'
```

## Environment defaults

- `APP_ENV=development` uses **Chroma** by default.
- `APP_ENV=production` uses **Qdrant** by default and requires `QDRANT_URL` (plus `QDRANT_API_KEY` when secured).
- `VECTOR_BACKEND` can explicitly override auto-selection (`chroma` or `qdrant`).
- Default LLM model is `gemini-1.5-flash` (`GOOGLE_API_KEY`).

## Test

```bash
make test         # all tests
make lint         # ruff + mypy
```

## Stack

- **Orchestration:** LangGraph state machine
- **LLM:** Google Gemini (default: gemini-1.5-flash)
- **Ingestion/Retrieval:** LlamaIndex + Chroma/Qdrant
- **API:** FastAPI with rate limiting and API key auth
- **Observability:** structlog, LangSmith opt-in
- **Security:** Input guardrails, Fernet memory encryption, security headers
