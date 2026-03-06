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

The PE Org-AI-R platform enables private equity firms to systematically assess the AI-readiness of portfolio companies using a data-driven scoring framework. It collects evidence from 9 real data sources, maps them to 7 AI-readiness dimensions, and produces calibrated Org-AI-R scores with confidence intervals.

### Case Studies Implemented

| Case Study | Focus | Key Components |
|------------|-------|---------------|
| **CS1** | API & Database Design | FastAPI REST API, Snowflake schema, Redis caching, Pydantic models |
| **CS2** | Evidence Collection | SEC EDGAR filings, job postings, patents, tech stack signals |
| **CS3** | AI Scoring Engine | Evidence mapper, rubric scorer, VR/HR/Synergy calculations, 5-company portfolio |

**Course**: DAMG 7245 — Big Data and Intelligent Analytics (Spring 2026)

### Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend API** | Python 3.12, FastAPI, Pydantic v2 |
| **Database** | Snowflake (cloud data warehouse) |
| **Cache** | Redis 7 (Alpine) |
| **Frontend** | Streamlit 1.54, Plotly |
| **Orchestration** | Apache Airflow 2.8 |
| **Containerization** | Docker Compose (7 services) |
| **Testing** | Pytest, Hypothesis (property-based) |
| **External APIs** | SEC EDGAR, Wextractor (Glassdoor), sec-api.io (Board), USPTO PatentsView, GNews, python-jobspy |

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Docker Compose Stack                         │
│                                                                     │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────────────┐   │
│  │  Streamlit    │──▶│  FastAPI      │──▶│  Snowflake           │   │
│  │  (Port 8501)  │   │  (Port 8000)  │   │  (Cloud DW)          │   │
│  └──────────────┘   └──────┬───────┘   └──────────────────────┘   │
│                            │                                        │
│                     ┌──────┴───────┐                               │
│                     │  Redis Cache  │                               │
│                     │  (Port 6379)  │                               │
│                     └──────────────┘                               │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    Apache Airflow                             │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌────────────────────┐  │  │
│  │  │  Webserver   │  │  Scheduler  │  │  PostgreSQL (meta) │  │  │
│  │  │ (Port 8080)  │  │             │  │  (Port 5432)       │  │  │
│  │  └─────────────┘  └─────────────┘  └────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘

                    ┌─── External Data Sources ───┐
                    │  SEC EDGAR  │  Wextractor    │
                    │  sec-api.io │  USPTO Patents │
                    │  GNews API  │  python-jobspy │
                    └─────────────────────────────┘
```

### Data Pipeline Flow

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
                                        Synergy ────────┘
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

---

## Directory Structure

```
pe-org-air-platform/
├── app/
│   ├── main.py                      # FastAPI application entry point
│   ├── config.py                    # Pydantic settings (env-based)
│   ├── logging.py                   # Structured logging (structlog)
│   ├── models/                      # Pydantic data models
│   │   ├── company.py               # Company CRUD models
│   │   ├── assessment.py            # Assessment lifecycle models
│   │   ├── dimension.py             # 7-dimension weights & scores
│   │   ├── document.py              # SEC document models
│   │   ├── signal.py                # CS2 signal models + configurable weights
│   │   └── common.py                # Pagination helpers
│   ├── routers/                     # FastAPI API endpoints
│   │   ├── health.py                # GET /health (Snowflake/Redis/S3 status)
│   │   ├── companies.py             # CRUD /api/v1/companies
│   │   ├── assessments.py           # CRUD /api/v1/assessments
│   │   ├── scores.py                # PUT /api/v1/scores/{id}
│   │   ├── industries.py            # CRUD /api/v1/industries
│   │   ├── config.py                # GET /api/v1/config/dimension-weights
│   │   ├── documents.py             # CRUD /api/v1/documents
│   │   ├── signals.py               # CRUD /api/v1/signals + /evidence
│   │   └── pipeline.py              # Pipeline execution & orchestration
│   ├── services/                    # External service integrations
│   │   ├── snowflake.py             # Snowflake ORM + CRUD operations
│   │   ├── redis_cache.py           # Redis caching decorators
│   │   └── s3_storage.py            # S3 document storage (optional)
│   ├── pipelines/                   # Data collection pipelines
│   │   ├── sec_edgar.py             # SEC EDGAR filing downloader
│   │   ├── document_parser.py       # PDF/HTML parser + section extraction
│   │   ├── job_signals.py           # Job posting scraper (Indeed/LinkedIn)
│   │   ├── tech_signals.py          # Technology stack analyzer
│   │   ├── patent_signals.py        # USPTO patent search
│   │   ├── glassdoor_collector.py   # Glassdoor review analyzer (CS3)
│   │   ├── board_analyzer.py        # Board composition analyzer (CS3)
│   │   └── news_collector.py        # News/press release collector (CS3)
│   ├── scoring/                     # CS3 Scoring Engine
│   │   ├── evidence_mapper.py       # 9 sources → 7 dimensions (Table 1)
│   │   ├── rubric_scorer.py         # 5-level rubrics × 7 dimensions
│   │   ├── talent_concentration.py  # Key-person risk (TC)
│   │   ├── utils.py                 # Decimal math utilities
│   │   ├── vr_calculator.py         # Value-Readiness (VR)
│   │   ├── position_factor.py       # Sector-relative positioning (PF)
│   │   ├── hr_calculator.py         # Historical Readiness (HR)
│   │   ├── confidence.py            # SEM-based confidence intervals
│   │   ├── synergy_calculator.py    # VR-HR synergy effects
│   │   ├── org_air_calculator.py    # Final Org-AI-R formula
│   │   └── integration_service.py   # Full pipeline orchestration
│   └── database/
│       └── schema.sql               # Snowflake DDL + seed data
├── airflow/                         # Airflow DAGs
│   └── dags/
│       ├── evidence_collection_dag.py  # CS2+CS3 evidence collection
│       └── scoring_pipeline_dag.py     # Scoring + validation + aggregation
├── scripts/                         # Standalone pipeline scripts
│   ├── collect_cs3_evidence.py
│   ├── score_sec_text_v2.py
│   ├── scrape_jobs_v2.py
│   ├── score_portfolio.py
│   └── ...
├── tests/                           # Test suite (255 tests, 97% coverage)
│   ├── test_scoring_engine.py       # 49 tests inc. 6 Hypothesis property tests
│   ├── test_scoring_utils.py        # 21 Decimal utility tests
│   ├── test_collectors.py           # 21 Glassdoor + Board tests
│   └── test_sec_edgar.py            # SEC parser + chunker tests
├── results/                         # Portfolio scoring outputs (JSON)
├── data/
│   ├── glassdoor/                   # Cached Glassdoor reviews
│   ├── board/                       # Board composition data
│   └── news/                        # Cached news articles
├── docker/
│   ├── compose.yaml                 # 7-service Docker Compose
│   ├── Dockerfile                   # FastAPI container
│   ├── Dockerfile.streamlit         # Streamlit container
│   └── .env.example                 # Environment template (no secrets)
├── docs/
│   └── evidence_report.md           # Full evidence & scoring report
├── streamlit_app.py                 # 9-page Streamlit dashboard
├── pyproject.toml                   # Poetry dependencies
├── requirements.txt                 # Pip requirements (exported)
└── .env.example                     # Root environment template
```

---

## Setup Instructions

### Option 1: Docker Compose (Recommended)

Full stack with API, Streamlit, Redis, Airflow, PostgreSQL — **7 services**.

```bash
# 1. Clone the repository
git clone <repository-url>
cd BigDataIA-SPring26-Team-4-case-study-3/pe-org-air-platform

# 2. Configure environment
cp docker/.env.example docker/.env
# Edit docker/.env with your Snowflake credentials and API keys

# 3. Build and start all services
cd docker
docker compose up --build -d

# 4. Verify all services are running
docker compose ps
# Expected: 6 services running (+ airflow-init exited 0)

# 5. Access the applications
# FastAPI Docs:  http://localhost:8000/docs
# Streamlit UI:  http://localhost:8501
# Airflow UI:    http://localhost:8080 (admin/admin)

# 6. Stop all services
docker compose down
```

### Option 2: Local Development

```bash
# 1. Clone and install
git clone <repository-url>
cd BigDataIA-SPring26-Team-4-case-study-3/pe-org-air-platform
poetry install

# 2. Configure environment
cp .env.example .env
# Edit .env with your Snowflake credentials and API keys

# 3. Start FastAPI backend
poetry run uvicorn app.main:app --reload

# 4. Start Streamlit (separate terminal)
poetry run streamlit run streamlit_app.py

# 5. Run scoring pipeline
poetry run python -m scripts.score_portfolio

# 6. Run tests
poetry run pytest -v --cov=app/scoring
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

---

## API Endpoints

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
| `pipeline.py` | `/api/v1/pipeline` | Pipeline execution, scoring, weight recalculation |

---

## Streamlit Dashboard (9 Pages)

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

---

## Airflow DAGs

| DAG | Schedule | Tasks | Description |
|-----|----------|-------|-------------|
| `evidence_collection_pipeline` | Sundays 4am UTC | 16 | CS2 + CS3 collection (parallel per company) via API |
| `scoring_pipeline` | Mondays 6am UTC | 6 | Score portfolio + validate ranges + aggregate ranking |

---

## Testing

```bash
# Run full test suite
poetry run pytest -v

# With coverage report
poetry run pytest --cov=app/scoring -v

# Property-based tests only
poetry run pytest tests/test_scoring_engine.py -k "property" -v
```

| Metric | Value |
|--------|-------|
| Total Tests | 255 |
| Code Coverage | 97% |
| Hypothesis Property Tests | 6 × 500 examples |
| Test Run Time | ~33s |

---

## Team Member Contributions

| Member | Contributions |
|--------|--------------|
| **Deep Prajapati** | CS1 API design, CS2 evidence collection (SEC, jobs, patents, tech), CS3 scoring engine (all 11 components), Glassdoor/Board/News collectors, Streamlit dashboard (9 pages), Docker Compose setup, Airflow DAGs, full integration testing |
| **Tapan Patel** | Airflow DAG design reference, initial Docker setup |
| **Naman Patel** | _[Add contributions]_ |

### AI Tools Used

| Tool | Usage |
|------|-------|
| **Claude (Anthropic)** | Code generation, debugging, architecture design, formula verification, test writing |
| **GitHub Copilot** | Inline code suggestions |

---

## Deliverables Checklist

### Lab 5 (50 points)
- ✅ Evidence Mapper with complete mapping table (10 pts)
- ✅ Rubric Scorer with all 7 dimension rubrics (8 pts)
- ✅ Glassdoor Culture Collector (7 pts)
- ✅ Board Composition Analyzer (7 pts)
- ✅ Talent Concentration Calculator (5 pts)
- ✅ Decimal utilities (3 pts)
- ✅ VR Calculator with audit logging (5 pts)
- ✅ Property-based tests (5 pts)

### Lab 6 (50 points)
- ✅ Position Factor Calculator (5 pts)
- ✅ Integration Service — full pipeline (15 pts)
- ✅ HR Calculator with δ = 0.15 (5 pts)
- ✅ SEM-based Confidence Calculator (5 pts)
- ✅ Synergy Calculator (5 pts)
- ✅ Org-AI-R Calculator (5 pts)
- ✅ 5-company portfolio results (10 pts)

### Testing Requirements
- ✅ ≥80% code coverage (97% achieved)
- ✅ All property tests pass with 500 examples
- ✅ Portfolio scores validated against expected ranges
