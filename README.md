# PE Org-AI-R Platform

**AI-Readiness Assessment Platform for Private Equity Portfolio Companies**

[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green.svg)](https://fastapi.tiangolo.com)
[![Tests](https://img.shields.io/badge/Tests-255%20passed-brightgreen.svg)]()
[![Coverage](https://img.shields.io/badge/Coverage-97%25-brightgreen.svg)]()

---

## Links

| Resource | URL |
|----------|-----|
| **Codelabs Document** | https://codelabs-preview.appspot.com/?file_id=1XPoDQtI28SVqOQTJ0J3cJQRhWVE97O0d0MUoTDU1V5E |
| **Video Presentation** | https://youtu.be/G0shIap0rwY |
| **Live Application** | _[Add Streamlit URL if deployed]_ |

---

## Project Overview

The PE Org-AI-R platform enables private equity firms to systematically assess the AI-readiness of portfolio companies using a data-driven scoring framework. It collects evidence from 9 real data sources, maps them to 7 AI-readiness dimensions, produces calibrated Org-AI-R scores with confidence intervals, and generates **cited score justifications** for Investment Committee review via a hybrid RAG pipeline.

### Case Studies Implemented

| Case Study | Focus | Key Components |
|------------|-------|---------------|
| **CS1** | API & Database Design | FastAPI REST API, Snowflake schema, Redis caching, Pydantic models |
| **CS2** | Evidence Collection | SEC EDGAR filings, job postings, patents, tech stack signals |
| **CS3** | AI Scoring Engine | Evidence mapper, rubric scorer, VR/HR/Synergy calculations, 5-company portfolio |
| **CS4** | RAG & Search | Hybrid retrieval (Dense+BM25+RRF), score justifications, IC meeting prep, analyst notes |

**Course**: DAMG 7245 — Big Data and Intelligent Analytics (Spring 2026)

### Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend API** | Python 3.12, FastAPI, Pydantic v2 |
| **CS4 RAG API** | FastAPI (port 8003), LiteLLM, ChromaDB, sentence-transformers, BM25 |
| **Database** | Snowflake (cloud data warehouse) |
| **Vector Store** | ChromaDB (persistent, cosine similarity, metadata filtering) |
| **Embeddings** | sentence-transformers (all-MiniLM-L6-v2, 384-dim) |
| **LLM Routing** | LiteLLM (100+ providers, automatic fallbacks, cost tracking) |
| **Cache** | Redis 7 (Alpine) |
| **Frontend** | Streamlit 1.54, Plotly |
| **Orchestration** | Apache Airflow 2.8 |
| **Containerization** | Docker Compose (8 services) |
| **Testing** | Pytest, Hypothesis (property-based) |
| **External APIs** | SEC EDGAR, Wextractor (Glassdoor), sec-api.io (Board), USPTO PatentsView, GNews, python-jobspy |

---

## Architecture Diagram

```
┌────────────────────────────────────────────────────────────────────────┐
│                        Docker Compose Stack                            │
│                                                                        │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────────────┐      │
│  │  Streamlit    │──▶│  FastAPI      │──▶│  Snowflake           │      │
│  │  (Port 8501)  │   │  (Port 8000)  │   │  (Cloud DW)          │      │
│  └──────┬───────┘   └──────┬───────┘   └──────────────────────┘      │
│         │                  │                                           │
│         │           ┌──────┴───────┐                                  │
│         │           │  Redis Cache  │                                  │
│         │           │  (Port 6379)  │                                  │
│         │           └──────────────┘                                  │
│         │                                                              │
│         │  ┌──────────────────────────────────────────────────────┐   │
│         └─▶│  CS4 RAG API (Port 8003)                             │   │
│            │  ┌────────────┐  ┌──────────┐  ┌─────────────────┐  │   │
│            │  │  ChromaDB   │  │  BM25    │  │  LiteLLM Router │  │   │
│            │  │  (Dense)    │  │  (Sparse) │  │  (Multi-Model)  │  │   │
│            │  └────────────┘  └──────────┘  └─────────────────┘  │   │
│            │  ┌────────────────────────────────────────────────┐  │   │
│            │  │  RRF Fusion + HyDE Enhancement                 │  │   │
│            │  └────────────────────────────────────────────────┘  │   │
│            └──────────────────────────────────────────────────────┘   │
│                                                                        │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │                    Apache Airflow                                 │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌────────────────────┐      │ │
│  │  │  Webserver   │  │  Scheduler  │  │  PostgreSQL (meta) │      │ │
│  │  │ (Port 8080)  │  │             │  │  (Port 5432)       │      │ │
│  │  └─────────────┘  └─────────────┘  └────────────────────┘      │ │
│  └──────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────────┘

                    ┌─── External Data Sources ───┐
                    │  SEC EDGAR  │  Wextractor    │
                    │  sec-api.io │  USPTO Patents │
                    │  GNews API  │  python-jobspy │
                    └─────────────────────────────┘
```

### CS4 RAG Pipeline Flow

```
                    "Why did NVDA score 94 on Data Infrastructure?"
                                    │
                    ┌───────────────┴───────────────┐
                    ▼                               ▼
             ┌─────────────┐                 ┌─────────────┐
             │  CS3 Client  │                 │  CS3 Client  │
             │  Get Score   │                 │  Get Rubric  │
             │  (93.7/100)  │                 │  (Level 5)   │
             └──────┬──────┘                 └──────┬──────┘
                    │                               │
                    │         ┌──────────────────────┘
                    ▼         ▼
             ┌──────────────────┐
             │  Build Query from │
             │  Rubric Keywords  │
             │  "snowflake       │
             │   databricks      │
             │   real-time"      │
             └────────┬─────────┘
                      ▼
        ┌─────────────┴─────────────┐
        ▼                           ▼
  ┌───────────┐              ┌───────────┐
  │  Dense     │              │  Sparse   │
  │  ChromaDB  │              │  BM25     │
  │  (Semantic) │              │  (Keyword) │
  └─────┬─────┘              └─────┬─────┘
        │                          │
        └──────────┬───────────────┘
                   ▼
           ┌──────────────┐
           │  RRF Fusion   │
           │  score(d) =   │
           │  Σ w/(k+rank) │
           └──────┬───────┘
                  ▼
         ┌────────────────┐
         │  Match Evidence │
         │  to Rubric KWs  │──▶ CitedEvidence[]
         │  + Identify Gaps │──▶ gaps_identified[]
         └────────┬───────┘
                  ▼
          ┌───────────────┐
          │  LLM Summary   │
          │  (or Template)  │──▶ ScoreJustification
          └───────────────┘
```

### Complete Data Pipeline (CS1→CS2→CS3→CS4)

```
SEC EDGAR ──┐                               ┌─── Data Infrastructure (0.25)
Job Boards ─┤                               ├─── AI Governance (0.20)
Patents ────┤   Evidence    9 Sources        ├─── Technology Stack (0.15)
Glassdoor ──┤ ──────────▶ ──────────▶ VR ──▶├─── Talent & Skills (0.15)
Board Data ─┤   Mapper      7 Dims         ├─── Leadership (0.10)
Tech Stack ─┤                               ├─── Use Case Portfolio (0.10)
News/PR ────┘                               └─── Culture & Change (0.05)
                                                        │
                                        VR ─────────────┤
                                        HR ─────────────┤──▶ Org-AI-R Score
                                        Synergy ────────┘         │
                                                                  ▼
                                                    ┌─────────────────────┐
                                              CS4:  │  Hybrid Search      │
                                                    │  Score Justification│
                                                    │  IC Meeting Package │
                                                    │  Analyst Notes      │
                                                    └─────────────────────┘
```

---

## Portfolio Results

| Company | Sector | Org-AI-R | VR | HR | Synergy | 95% CI | Expected | Status |
|---------|--------|----------|------|------|---------|--------|----------|--------|
| **NVIDIA** | Technology | **81.73** | 78.35 | 92.04 | 66.32 | [78.8, 84.7] | 85-95 | CI overlaps |
| **Walmart** | Retail | **66.98** | 66.13 | 75.22 | 46.54 | [64.0, 69.9] | 55-65 | Above by ~2 |
| **JPMorgan** | Financial | **63.06** | 55.18 | 83.87 | 36.73 | [60.1, 66.0] | 65-75 | CI overlaps |
| **GE** | Manufacturing | **59.66** | 55.50 | 74.22 | 35.25 | [56.7, 62.6] | 45-55 | Above by ~5 |
| **Dollar General** | Retail | **46.74** | 39.28 | 67.22 | 19.48 | [43.8, 49.7] | 35-45 | Above by ~2 |

*Ranking: NVDA > WMT > JPM > GE > DG ✓*

### CS4 IC Recommendation (NVDA Example)

| Field | Value |
|-------|-------|
| **Recommendation** | 🟢 PROCEED — Strong AI readiness with solid evidence base |
| **Org-AI-R** | 81.7 (VR=78.3, HR=92.0) |
| **Key Strengths** | Data Infrastructure (Level 5), Technology Stack (Level 5), AI Governance (Level 4) |
| **Key Gaps** | No evidence of CAIO, CDO, CTO AI roles |
| **Risk Factors** | Weak evidence for talent, leadership, culture dimensions |
| **Total Evidence** | 337 indexed documents (SEC chunks + Glassdoor + Board + News + Jobs) |

---

## Directory Structure

```
pe-org-air-platform/
├── app/                                 # CS1–CS3 Backend
│   ├── main.py                          # FastAPI application entry point
│   ├── config.py                        # Pydantic settings (env-based)
│   ├── logging.py                       # Structured logging (structlog)
│   ├── models/                          # Pydantic data models
│   │   ├── company.py                   # Company CRUD models
│   │   ├── assessment.py                # Assessment lifecycle models
│   │   ├── dimension.py                 # 7-dimension weights & scores
│   │   ├── document.py                  # SEC document models
│   │   ├── signal.py                    # CS2 signal models + configurable weights
│   │   └── common.py                    # Pagination helpers
│   ├── routers/                         # FastAPI API endpoints
│   │   ├── health.py                    # GET /health (Snowflake/Redis/S3 status)
│   │   ├── companies.py                 # CRUD /api/v1/companies
│   │   ├── assessments.py               # CRUD /api/v1/assessments
│   │   ├── scores.py                    # PUT /api/v1/scores/{id}
│   │   ├── industries.py                # CRUD /api/v1/industries
│   │   ├── config.py                    # GET /api/v1/config/dimension-weights
│   │   ├── documents.py                 # CRUD /api/v1/documents
│   │   ├── signals.py                   # CRUD /api/v1/signals + /evidence
│   │   ├── rubrics.py                   # GET /api/v1/rubrics/{dimension} (CS4 prereq)
│   │   └── pipeline.py                  # Pipeline execution & orchestration
│   ├── services/                        # External service integrations
│   │   ├── snowflake.py                 # Snowflake ORM + CRUD operations
│   │   ├── redis_cache.py               # Redis caching decorators
│   │   └── s3_storage.py                # S3 document storage (optional)
│   ├── pipelines/                       # Data collection pipelines
│   │   ├── sec_edgar.py                 # SEC EDGAR filing downloader
│   │   ├── document_parser.py           # PDF/HTML parser + section extraction
│   │   ├── job_signals.py               # Job posting scraper (Indeed/LinkedIn)
│   │   ├── tech_signals.py              # Technology stack analyzer
│   │   ├── patent_signals.py            # USPTO patent search
│   │   ├── glassdoor_collector.py       # Glassdoor review analyzer (CS3)
│   │   ├── board_analyzer.py            # Board composition analyzer (CS3)
│   │   └── news_collector.py            # News/press release collector (CS3)
│   ├── scoring/                         # CS3 Scoring Engine
│   │   ├── evidence_mapper.py           # 9 sources → 7 dimensions (Table 1)
│   │   ├── rubric_scorer.py             # 5-level rubrics × 7 dimensions
│   │   ├── talent_concentration.py      # Key-person risk (TC)
│   │   ├── utils.py                     # Decimal math utilities
│   │   ├── vr_calculator.py             # Value-Readiness (VR)
│   │   ├── position_factor.py           # Sector-relative positioning (PF)
│   │   ├── hr_calculator.py             # Historical Readiness (HR)
│   │   ├── confidence.py                # SEM-based confidence intervals
│   │   ├── synergy_calculator.py        # VR-HR synergy effects
│   │   ├── org_air_calculator.py        # Final Org-AI-R formula
│   │   └── integration_service.py       # Full pipeline orchestration
│   └── database/
│       └── schema.sql                   # Snowflake DDL + seed data
│
├── src/                                 # CS4 RAG & Search (NEW)
│   ├── config.py                        # CS4 settings (env-based, LLM config)
│   ├── services/
│   │   ├── integration/                 # CS1/CS2/CS3 API Clients
│   │   │   ├── cs1_client.py            # Company metadata (ticker, sector, position)
│   │   │   ├── cs2_client.py            # Evidence loader (docs + signals + local JSON)
│   │   │   └── cs3_client.py            # Scoring client (scores, rubrics, fallback)
│   │   ├── llm/
│   │   │   └── router.py               # LiteLLM multi-provider router + budget
│   │   ├── search/
│   │   │   └── vector_store.py          # ChromaDB with metadata filtering
│   │   ├── retrieval/
│   │   │   ├── dimension_mapper.py      # Signal → Dimension mapping (PDF Table 1)
│   │   │   ├── hybrid.py               # Dense + BM25 + RRF fusion
│   │   │   └── hyde.py                  # Hypothetical Document Embeddings
│   │   ├── justification/
│   │   │   └── generator.py             # Score justification with cited evidence
│   │   ├── workflows/
│   │   │   └── ic_prep.py              # IC meeting prep (parallel, 7 dims)
│   │   └── collection/
│   │       └── analyst_notes.py         # DD evidence collector (4 note types)
│   └── api/                             # CS4 FastAPI Endpoints
│       ├── search.py                    # Search, index, stats, LLM status
│       └── justification.py             # Justification, IC prep, analyst notes
│
├── cs4_api.py                           # CS4 FastAPI app (port 8003)
│
├── exercises/
│   └── complete_pipeline.py             # End-to-end NVDA exercise
│
├── streamlit_app.py                     # 14-page Streamlit dashboard (CS2+CS3+CS4)
│
├── airflow/dags/
│   ├── evidence_collection_dag.py       # CS2+CS3 evidence collection
│   ├── scoring_pipeline_dag.py          # Scoring + validation + aggregation
│   └── evidence_indexing_dag.py         # CS4 nightly evidence indexing (NEW)
│
├── tests/                               # Test suite
│   ├── test_scoring_engine.py           # 49 tests inc. 6 Hypothesis property tests
│   ├── test_scoring_utils.py            # 21 Decimal utility tests
│   ├── test_collectors.py               # 21 Glassdoor + Board tests
│   ├── test_sec_edgar.py                # SEC parser + chunker tests
│   ├── test_cs4_integration.py          # CS1/CS2/CS3 client tests (NEW)
│   ├── test_cs4_rag.py                  # Config, LLM, VectorStore, Hybrid, HyDE (NEW)
│   ├── test_cs4_workflows.py            # Justification, IC Prep, Analyst Notes (NEW)
│   └── test_cs4_api.py                  # FastAPI endpoint tests (NEW)
│
├── results/                             # Portfolio scoring outputs (JSON)
├── data/
│   ├── glassdoor/                       # Cached Glassdoor reviews (real API data)
│   ├── board/                           # Board composition data (real API data)
│   └── news/                            # Cached news articles (real API data)
├── chroma_data/                         # ChromaDB persistent vector store (CS4)
├── docker/
│   ├── compose.yaml                     # 8-service Docker Compose (+CS4 RAG API)
│   ├── Dockerfile                       # FastAPI container
│   ├── Dockerfile.cs4                   # CS4 RAG API container (NEW)
│   ├── Dockerfile.streamlit             # Streamlit container
│   └── .env.example                     # Environment template (no secrets)
├── docs/
│   └── evidence_report.md              # Full evidence & scoring report
├── pyproject.toml                       # Poetry dependencies
├── requirements.txt                     # Pip requirements (exported)
└── .env.example                         # Root environment template
```

---

## Setup Instructions

### Option 1: Docker Compose (Recommended)

Full stack with API, CS4 RAG API, Streamlit, Redis, Airflow, PostgreSQL — **8 services**.

```bash
# 1. Clone the repository
git clone <repository-url>
cd BigDataIA-SPring26-Team-4-case-study-4/pe-org-air-platform

# 2. Configure environment
cp docker/.env.example docker/.env
# Edit docker/.env with your Snowflake credentials and API keys
# Optional: Set CS4_PRIMARY_MODEL=gpt-4o for LLM-powered summaries

# 3. Build and start all services
cd docker
docker compose up --build -d

# 4. Verify all services are running
docker compose ps
# Expected: 7 services running (+ airflow-init exited 0)

# 5. Access the applications
# FastAPI Docs (CS1-CS3): http://localhost:8000/docs
# CS4 RAG API Docs:       http://localhost:8003/docs
# Streamlit UI:            http://localhost:8501
# Airflow UI:              http://localhost:8080 (admin/admin)

# 6. Stop all services
docker compose down
```

### Option 2: Local Development

```bash
# 1. Clone and install
git clone <repository-url>
cd BigDataIA-SPring26-Team-4-case-study-4
poetry install

# 2. Configure environment
cp .env.example .env
# Edit .env with your Snowflake credentials and API keys

# 3. Start CS3 backend API (Terminal 1)
poetry run uvicorn app.main:app --reload --port 8000

# 4. Start CS4 RAG API (Terminal 2)
poetry run uvicorn cs4_api:app --reload --port 8003

# 5. Start Streamlit (Terminal 3)
poetry run streamlit run streamlit_app.py

# 6. Index evidence for search (via Streamlit ⚙️ RAG Settings page)
# Or via API: curl -X POST http://localhost:8003/api/v1/index -d '{"company_id":"NVDA"}'

# 7. Run tests
poetry run pytest -v
```

### CS4 LLM Configuration (Optional)

CS4 works fully without LLM (template-based summaries). To enable LLM-powered summaries and HyDE query enhancement:

```bash
# In .env file — set any LiteLLM-compatible model:
CS4_PRIMARY_MODEL=gpt-4o              # OpenAI
# CS4_PRIMARY_MODEL=claude-sonnet-4-20250514  # Anthropic
# CS4_PRIMARY_MODEL=ollama/llama3     # Local Ollama

# Provider API key (whichever you use):
OPENAI_API_KEY=sk-...
# ANTHROPIC_API_KEY=sk-ant-...

# Optional: task-specific models, budget limit
CS4_FALLBACK_MODEL=gpt-3.5-turbo
CS4_DAILY_BUDGET_USD=50.0
```

---

## Scoring Formulas

**Org-AI-R** = (1 − β) · [α · VR + (1 − α) · HR] + β · Synergy

| Formula | Expression | Constants |
|---------|-----------|-----------|
| **VR** | D̄w × (1 − λ × cv_D) × TalentRiskAdj | λ = 0.25 |
| **HR** | HR_base × (1 + δ × PF) | δ = 0.15 |
| **PF** | 0.6 × VR_component + 0.4 × MCap_component | bounded [-1, 1] |
| **TC** | 0.4×leadership + 0.3×team_size + 0.2×skills + 0.1×mentions | bounded [0, 1] |
| **TalentRiskAdj** | 1 − 0.15 × max(0, TC − 0.25) | |
| **Synergy** | VR × HR / 100 × Alignment × TimingFactor | TimingFactor ∈ [0.8, 1.2] |
| **SEM** | σ × √(1 − ρ), ρ = Spearman-Brown | 95% CI |
| **Final** | (1 − β) × [α × VR + (1 − α) × HR] + β × Synergy | α=0.60, β=0.12 |

### CS2 Signal Weights (Configurable)

| Signal | Default Weight | Source |
|--------|---------------|--------|
| Technology Hiring | **0.30** | Job Postings (Indeed) |
| Innovation Activity | **0.25** | Patents (USPTO) |
| Digital Presence | **0.25** | Tech Stack |
| Leadership Signals | **0.20** | Glassdoor + Board + News |

### 7 AI-Readiness Dimensions

| # | Dimension | Weight | Primary Evidence Source |
|---|-----------|--------|----------------------|
| D1 | Data Infrastructure | 0.25 | Tech Stack (0.60) |
| D2 | AI Governance | 0.20 | SEC Item 1A (0.80), Board (0.70) |
| D3 | Technology Stack | 0.15 | Innovation/Patents (0.50) |
| D4 | Talent & Skills | 0.15 | Job Postings (0.70) |
| D5 | Leadership & Vision | 0.10 | Leadership Signals (0.60) |
| D6 | Use Case Portfolio | 0.10 | SEC Item 1 (0.70) |
| D7 | Culture & Change | 0.05 | Glassdoor (0.80) |

### CS4 Hybrid Retrieval

| Parameter | Value | Source |
|-----------|-------|--------|
| Dense Weight | 0.60 | `CS4_DENSE_WEIGHT` env var |
| Sparse (BM25) Weight | 0.40 | `CS4_BM25_WEIGHT` env var |
| RRF Constant (k) | 60 | `CS4_RRF_K` env var |
| Embedding Model | all-MiniLM-L6-v2 | `CS4_EMBEDDING_MODEL` env var |
| Embedding Dimensions | 384 | Fixed by model |
| Candidate Multiplier | 3× | Retrieve 3×k from each method before fusion |
| HyDE Enhancement | Auto (requires LLM) | Falls back to raw query if no LLM |
| Daily Budget | $50.00 | `CS4_DAILY_BUDGET_USD` env var |

---

## API Endpoints

### CS1/CS2/CS3 API (Port 8000)

All data flows through **FastAPI routers** → **Snowflake**:

| Router | Prefix | Purpose |
|--------|--------|---------|
| `health.py` | `/health` | Health check (Snowflake/Redis/S3 status) |
| `companies.py` | `/api/v1/companies` | Company CRUD with pagination |
| `assessments.py` | `/api/v1/assessments` | Assessment lifecycle management |
| `scores.py` | `/api/v1/scores` | Individual dimension score updates |
| `industries.py` | `/api/v1/industries` | Industry reference data (cached 1hr) |
| `config.py` | `/api/v1/config` | Dimension weight configuration |
| `documents.py` | `/api/v1/documents` | SEC document CRUD |
| `signals.py` | `/api/v1/signals` | External signal CRUD + evidence stats |
| `rubrics.py` | `/api/v1/rubrics` | Dimension rubric criteria (CS4 prereq) |
| `pipeline.py` | `/api/v1/pipeline` | Pipeline execution, scoring, weight recalculation |

### CS4 RAG API (Port 8003)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/search` | GET | Hybrid search with metadata filters (company, dimension, source, confidence) |
| `/api/v1/index` | POST | Index company evidence from CS2 into ChromaDB + BM25 |
| `/api/v1/index/stats` | GET | Indexing statistics (ChromaDB count, BM25 status, fusion config) |
| `/api/v1/llm/status` | GET | LLM provider health, configured models, daily budget |
| `/api/v1/justification/{company}/{dim}` | GET | Score justification with cited evidence and gaps |
| `/api/v1/ic-prep/{company}` | GET | Full IC meeting package (7 dims, recommendation) |
| `/api/v1/analyst-notes/interview` | POST | Submit interview transcript |
| `/api/v1/analyst-notes/dd-finding` | POST | Submit due diligence finding |
| `/api/v1/analyst-notes/data-room` | POST | Submit data room document summary |
| `/api/v1/analyst-notes/meeting` | POST | Submit management meeting notes |
| `/api/v1/analyst-notes/{company}` | GET | List all analyst notes for a company |
| `/health` | GET | CS4 service health check |

---

## Streamlit Dashboard (14 Pages)

### CS2/CS3 Pages (9 pages)

| Page | Features |
|------|----------|
| 📊 Portfolio Overview | KPI metrics, bar charts with CI, VR/HR/Synergy breakdown |
| 🔍 Company Deep Dive | 7-dimension radar chart, score decomposition, scoring parameters |
| 📐 Dimension Analysis | Heatmap, per-dimension comparison, multi-company radar overlay |
| 📡 CS2 Evidence Dashboard | Signal weights from API, evidence stats, quick composite recalculation |
| ⚖️ Signal Weight Configurator | Interactive sliders, live preview, persist to Snowflake via API |
| 🚀 Pipeline Control | Run CS2/CS3/Scoring pipelines via API, progress tracking, task history |
| 🧮 Scoring Methodology | Formulas, dimension weights from API, Sankey diagram, router architecture |
| 📂 Evidence Explorer | Direct API calls to /documents and /signals routers, 6 evidence tabs |
| 🧪 Testing & Coverage | Run pytest from UI, coverage chart, Hypothesis property test details |

### CS4 RAG & Search Pages (5 pages)

| Page | Features |
|------|----------|
| 🔎 Evidence Search | Hybrid retrieval with company/dimension/source/confidence filters, expandable result cards with score badges |
| 📋 Score Justification | Score card, rubric match, IC-ready summary (LLM or template), cited evidence with keyword matches, gap identification |
| 📑 IC Meeting Prep | Executive summary, recommendation badge (PROCEED/CAUTION/DILIGENCE), strengths/gaps/risks columns, 7-dimension expandable justifications |
| 📝 Analyst Notes | 4 note types (Interview, DD Finding, Data Room, Meeting) with forms, recent notes display |
| ⚙️ RAG Settings | Service health, LLM provider status with budget tracker, evidence indexing (single + bulk), index stats, API reference |

---

## Airflow DAGs

| DAG | Schedule | Tasks | Description |
|-----|----------|-------|-------------|
| `evidence_collection_pipeline` | Sundays 4am UTC | 16 | CS2 + CS3 collection (parallel per company) via API |
| `scoring_pipeline` | Mondays 6am UTC | 6 | Score portfolio + validate ranges + aggregate ranking |
| `pe_evidence_indexing` | Daily 2am UTC | 7 | CS4: Fetch new CS2 evidence → index in ChromaDB + BM25 (NEW) |

---

## Testing

```bash
# Run full test suite (CS1-CS4)
poetry run pytest -v

# CS3 scoring tests with coverage
poetry run pytest --cov=app/scoring --cov=src -v

# CS4 tests only
poetry run pytest tests/test_cs4_*.py -v

# Property-based tests only
poetry run pytest tests/test_scoring_engine.py -k "property" -v
```

| Metric | Value |
|--------|-------|
| Total Tests | 255+ |
| CS3 Scoring Coverage | 97% |
| Hypothesis Property Tests | 6 × 500 examples |
| CS4 Test Files | 4 (integration, rag, workflows, api) |

---

## Team Member Contributions

| Member | Contributions |
|--------|--------------|
| **Deep Prajapati** | CS1 API design, CS2 evidence collection (SEC, jobs, patents, tech), CS3 scoring engine (all 11 components), Glassdoor/Board/News collectors, CS4 RAG pipeline (hybrid retrieval, HyDE, justification generator, IC prep workflow, analyst notes), Streamlit dashboard (14 pages), Docker Compose setup, Airflow DAGs (3 DAGs), full integration testing |
| **Tapan Patel** | Airflow DAG design reference, initial Docker setup |
| **Seamus McAvoy** | CS1 API foundation, initial Snowflake schema design, CS2 evidence pipeline contributions |

### AI Tools Used

| Tool | Usage |
|------|-------|
| **Claude (Anthropic)** | Code generation, debugging, architecture design, formula verification, test writing, RAG pipeline design |
| **GitHub Copilot** | Inline code suggestions |

---

## Deliverables Checklist

### Lab 5 — CS3 Scoring (50 points)
- ✅ Evidence Mapper with complete mapping table (10 pts)
- ✅ Rubric Scorer with all 7 dimension rubrics (8 pts)
- ✅ Glassdoor Culture Collector (7 pts)
- ✅ Board Composition Analyzer (7 pts)
- ✅ Talent Concentration Calculator (5 pts)
- ✅ Decimal utilities (3 pts)
- ✅ VR Calculator with audit logging (5 pts)
- ✅ Property-based tests (5 pts)

### Lab 6 — CS3 Portfolio (50 points)
- ✅ Position Factor Calculator (5 pts)
- ✅ Integration Service — full pipeline (15 pts)
- ✅ HR Calculator with δ = 0.15 (5 pts)
- ✅ SEM-based Confidence Calculator (5 pts)
- ✅ Synergy Calculator (5 pts)
- ✅ Org-AI-R Calculator (5 pts)
- ✅ 5-company portfolio results (10 pts)

### Lab 7 — CS4 Foundation & Integration (33 points)
- ✅ CS1 Company Client (5 pts)
- ✅ CS2 Evidence Schema & Loader (8 pts)
- ✅ CS3 Scoring API Client (7 pts)
- ✅ LiteLLM Multi-Provider Router (8 pts)
- ✅ Dimension Mapper (5 pts)

### Lab 8 — CS4 Hybrid RAG & PE Workflows (67 points)
- ✅ Hybrid Retrieval with RRF Fusion (10 pts)
- ✅ HyDE Query Enhancement (7 pts)
- ✅ Score Justification Generator (12 pts)
- ✅ IC Meeting Prep Workflow (10 pts)
- ✅ Analyst Notes Collector (8 pts)
- ✅ Search API with filters (8 pts)
- ✅ Justification API endpoint (7 pts)
- ✅ Unit & integration tests (5 pts)

### Extensions (+10 bonus)
- ✅ Airflow Evidence Indexing DAG (+5 pts)
- ✅ Docker Compose with CS4 RAG API service (+5 pts)

### Testing Requirements
- ✅ ≥80% code coverage (97% achieved on scoring)
- ✅ All property tests pass with 500 examples
- ✅ Portfolio scores validated against expected ranges
- ✅ CS4 tests cover integration, RAG, workflows, and API
