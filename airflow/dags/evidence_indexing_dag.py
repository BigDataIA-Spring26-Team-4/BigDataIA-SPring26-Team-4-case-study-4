"""
Airflow DAG for CS4 Evidence Indexing Pipeline.

Extension A: Automated nightly pipeline to fetch new CS2 evidence
and index it in CS4's hybrid retrieval store (ChromaDB + BM25).

Flow:
  1. Check CS4 RAG API is healthy
  2. For each portfolio company, call POST /api/v1/index
     (fetches unindexed evidence from CS2, maps to dimensions, indexes)
  3. Verify index stats after completion

Schedule: Daily at 2 AM UTC (after evidence collection finishes)

Follows same patterns as existing DAGs:
  - stdlib urllib only (no requests/httpx in Airflow)
  - PythonOperator tasks
  - XCom for passing data between tasks
  - Retry with exponential backoff
"""

import json
import time
import logging
from datetime import datetime, timedelta
from urllib.request import urlopen, Request
from urllib.error import URLError

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator
from airflow.utils.trigger_rule import TriggerRule

# ── Constants ─────────────────────────────────────────────────────

# CS4 RAG API (Docker service name + port)
CS4_API_BASE = "http://cs4-rag-api:8003"

# All portfolio companies to index
PORTFOLIO_TICKERS = ["NVDA", "JPM", "WMT", "GE", "DG"]

log = logging.getLogger(__name__)


# ── HTTP Helpers (stdlib only, matching existing DAG pattern) ─────


def _http_get(url, timeout=10):
    """GET request using stdlib only."""
    req = Request(url)
    resp = urlopen(req, timeout=timeout)
    body = json.loads(resp.read().decode())
    return body, resp.status


def _http_post(url, payload, timeout=60):
    """POST request using stdlib only."""
    data = json.dumps(payload).encode()
    req = Request(url, data=data, headers={"Content-Type": "application/json"})
    resp = urlopen(req, timeout=timeout)
    body = json.loads(resp.read().decode())
    return body, resp.status


def _wait_for_cs4_api(retries=30, delay=10):
    """Wait for CS4 RAG API to become available."""
    for i in range(retries):
        try:
            body, status = _http_get(CS4_API_BASE + "/health", timeout=5)
            if body.get("status") == "healthy":
                log.info("CS4 RAG API is healthy")
                return True
        except Exception:
            pass
        log.info(
            "Waiting for CS4 RAG API... attempt %d/%d", i + 1, retries
        )
        time.sleep(delay)
    raise RuntimeError("CS4 RAG API not available after %d retries" % retries)


# ── Task Callables ────────────────────────────────────────────────


def check_cs4_health(**context):
    """Verify CS4 RAG API is running and healthy."""
    _wait_for_cs4_api()

    body, _ = _http_get(CS4_API_BASE + "/health", timeout=10)
    log.info("CS4 Health: %s", body)

    # Also check index stats before indexing
    stats, _ = _http_get(CS4_API_BASE + "/api/v1/index/stats", timeout=10)
    log.info(
        "Pre-indexing stats: %d documents indexed",
        stats.get("dense", {}).get("total_documents", 0),
    )

    context["ti"].xcom_push(key="pre_index_count", value=(
        stats.get("dense", {}).get("total_documents", 0)
    ))


def index_company_evidence(ticker, **context):
    """
    Fetch and index evidence for a single company.

    Calls CS4's POST /api/v1/index endpoint which:
      1. Fetches evidence from CS2 API
      2. Maps to dimensions via DimensionMapper
      3. Indexes into ChromaDB (dense) + BM25 (sparse)
      4. Marks evidence as indexed in CS2
    """
    log.info("[%s] Starting evidence indexing...", ticker)

    try:
        body, status = _http_post(
            CS4_API_BASE + "/api/v1/index",
            payload={
                "company_id": ticker,
                "min_confidence": 0.0,
            },
            timeout=120,
        )

        docs_indexed = body.get("documents_indexed", 0)
        message = body.get("message", "")

        log.info("[%s] Indexed %d documents: %s", ticker, docs_indexed, message)

        context["ti"].xcom_push(
            key="indexed_" + ticker,
            value={
                "ticker": ticker,
                "documents_indexed": docs_indexed,
                "message": message,
            },
        )
        return docs_indexed

    except Exception as e:
        log.error("[%s] Indexing failed: %s", ticker, str(e))
        context["ti"].xcom_push(
            key="indexed_" + ticker,
            value={
                "ticker": ticker,
                "documents_indexed": 0,
                "error": str(e),
            },
        )
        raise


def verify_index_stats(**context):
    """Verify index stats after indexing all companies."""
    ti = context["ti"]

    # Collect results
    total_indexed = 0
    results = {}
    for ticker in PORTFOLIO_TICKERS:
        result = ti.xcom_pull(key="indexed_" + ticker) or {}
        results[ticker] = result
        total_indexed += result.get("documents_indexed", 0)

    # Get post-indexing stats
    stats, _ = _http_get(CS4_API_BASE + "/api/v1/index/stats", timeout=10)
    post_count = stats.get("dense", {}).get("total_documents", 0)
    pre_count = ti.xcom_pull(
        task_ids="check_cs4_health", key="pre_index_count"
    ) or 0

    # Log summary
    log.info("=" * 55)
    log.info("EVIDENCE INDEXING SUMMARY")
    log.info("=" * 55)
    for ticker, result in results.items():
        count = result.get("documents_indexed", 0)
        error = result.get("error")
        status = "ERROR: %s" % error if error else "OK"
        log.info("  %s: %d documents %s", ticker, count, status)
    log.info("-" * 55)
    log.info("  Total indexed this run: %d", total_indexed)
    log.info("  Index before: %d documents", pre_count)
    log.info("  Index after:  %d documents", post_count)
    log.info("=" * 55)

    ti.xcom_push(key="indexing_summary", value={
        "total_indexed": total_indexed,
        "pre_count": pre_count,
        "post_count": post_count,
        "by_company": results,
    })

    return total_indexed


# ── Default Args ──────────────────────────────────────────────────

default_args = {
    "owner": "pe-analytics",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 3,
    "retry_delay": timedelta(minutes=5),
    "retry_exponential_backoff": True,
}

# ── DAG Definition ────────────────────────────────────────────────

with DAG(
    dag_id="pe_evidence_indexing",
    default_args=default_args,
    description=(
        "CS4: Nightly pipeline to fetch new CS2 evidence "
        "and index in CS4 hybrid retrieval store"
    ),
    schedule_interval="0 2 * * *",  # 2 AM daily
    start_date=datetime(2026, 2, 20),
    catchup=False,
    max_active_runs=1,
    tags=["cs4", "rag", "indexing", "evidence"],
    doc_md=__doc__,
) as dag:

    start = EmptyOperator(task_id="start")

    health_check = PythonOperator(
        task_id="check_cs4_health",
        python_callable=check_cs4_health,
        doc_md="Verify CS4 RAG API is healthy before indexing",
    )

    # Create one task per company for parallel indexing
    index_tasks = []
    for ticker in PORTFOLIO_TICKERS:
        task = PythonOperator(
            task_id="index_" + ticker.lower(),
            python_callable=index_company_evidence,
            op_kwargs={"ticker": ticker},
            execution_timeout=timedelta(minutes=10),
            doc_md="Fetch and index CS2 evidence for " + ticker,
        )
        index_tasks.append(task)

    index_done = EmptyOperator(
        task_id="index_done",
        trigger_rule=TriggerRule.ALL_DONE,
    )

    verify = PythonOperator(
        task_id="verify_index_stats",
        python_callable=verify_index_stats,
        trigger_rule=TriggerRule.ALL_DONE,
        doc_md="Verify index counts after all companies are indexed",
    )

    end = EmptyOperator(
        task_id="end",
        trigger_rule=TriggerRule.ALL_DONE,
    )

    # Chain: start → health → parallel index per company → verify → end
    start >> health_check >> index_tasks >> index_done >> verify >> end
