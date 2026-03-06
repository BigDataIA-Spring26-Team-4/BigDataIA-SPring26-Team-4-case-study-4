"""
Airflow DAG for Evidence Collection Pipeline (CS2 + CS3).

Orchestrates data collection for 5 PE portfolio companies via the FastAPI backend:
  1. CS2: SEC filings, job postings, tech stack, patents (parallel per company)
  2. CS3: Glassdoor reviews, board composition, news/press releases (parallel per company)

All tasks communicate with the FastAPI API at http://api:8000.
Data is stored in Snowflake via the API's pipeline endpoints.

Schedule: Weekly on Sundays at 4am UTC
"""

import time
import json
import logging
from datetime import datetime, timedelta
from urllib.request import urlopen, Request
from urllib.error import URLError

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator
from airflow.utils.trigger_rule import TriggerRule

# ── Constants ─────────────────────────────────────────────────────

API_BASE = "http://api:8000"
CS3_TICKERS = ["NVDA", "JPM", "WMT", "GE", "DG"]
POLL_INTERVAL = 5
TASK_TIMEOUT = 300

log = logging.getLogger(__name__)

# ── HTTP Helpers (stdlib only, no requests) ───────────────────────


def _http_get(url, timeout=10):
    req = Request(url)
    resp = urlopen(req, timeout=timeout)
    body = json.loads(resp.read().decode())
    return body, resp.status


def _http_post(url, payload, timeout=30):
    data = json.dumps(payload).encode()
    req = Request(url, data=data, headers={"Content-Type": "application/json"})
    resp = urlopen(req, timeout=timeout)
    body = json.loads(resp.read().decode())
    return body, resp.status


def _wait_for_api(retries=30, delay=10):
    for i in range(retries):
        try:
            _http_get(API_BASE + "/", timeout=5)
            log.info("API is ready")
            return True
        except Exception:
            pass
        log.info("Waiting for API... attempt %d/%d", i + 1, retries)
        time.sleep(delay)
    raise RuntimeError("FastAPI backend not available after retries")


def _run_pipeline_task(endpoint, payload, label):
    body, _ = _http_post(API_BASE + endpoint, payload)
    task_id = body.get("task_id")
    if not task_id:
        raise ValueError("No task_id returned for %s: %s" % (label, body))

    log.info("[%s] Started - task_id=%s", label, task_id)

    elapsed = 0
    while elapsed < TASK_TIMEOUT:
        time.sleep(POLL_INTERVAL)
        elapsed += POLL_INTERVAL
        try:
            status_data, _ = _http_get(
                API_BASE + "/api/v1/pipeline/status/" + task_id
            )
        except Exception:
            continue

        if status_data["status"] == "completed":
            log.info("[%s] Completed in %ds: %s", label, elapsed, status_data.get("result", {}))
            return status_data.get("result", {})
        elif status_data["status"] == "failed":
            error = status_data.get("error", "Unknown")
            raise RuntimeError("[%s] Failed: %s" % (label, error))

    raise TimeoutError("[%s] Timed out after %ds" % (label, TASK_TIMEOUT))


# ── Task Callables ────────────────────────────────────────────────


def check_api_health(**context):
    _wait_for_api()
    try:
        body, _ = _http_get(API_BASE + "/health", timeout=10)
        log.info("API health: %s", body)
    except Exception:
        log.warning("Could not fetch full health, but API root is responding")


def collect_cs2_for_ticker(ticker, **context):
    result = _run_pipeline_task(
        endpoint="/api/v1/pipeline/collect-evidence",
        payload={"ticker": ticker, "skip_sec": True},
        label="CS2-" + ticker,
    )
    context["ti"].xcom_push(key="cs2_" + ticker, value=result)
    return result


def collect_cs3_for_ticker(ticker, **context):
    result = _run_pipeline_task(
        endpoint="/api/v1/pipeline/collect-cs3",
        payload={"ticker": ticker, "skip_sec": False},
        label="CS3-" + ticker,
    )
    context["ti"].xcom_push(key="cs3_" + ticker, value=result)
    return result


def collection_summary(**context):
    ti = context["ti"]
    for ticker in CS3_TICKERS:
        cs2 = ti.xcom_pull(key="cs2_" + ticker) or {}
        cs3 = ti.xcom_pull(key="cs3_" + ticker) or {}
        log.info("%s: CS2=%s, CS3=%s", ticker, cs2, cs3)
    log.info("Evidence collection pipeline completed for all companies")


# ── Default Args ──────────────────────────────────────────────────

default_args = {
    "owner": "pe-org-air-team",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=3),
}

# ── DAG Definition ────────────────────────────────────────────────

with DAG(
    dag_id="evidence_collection_pipeline",
    default_args=default_args,
    description="CS2+CS3: Collect SEC filings, signals, Glassdoor, Board & News data via API",
    schedule_interval="0 4 * * 0",
    start_date=datetime(2026, 2, 1),
    catchup=False,
    max_active_runs=1,
    tags=["cs2", "cs3", "evidence", "collection"],
    doc_md=__doc__,
) as dag:

    start = EmptyOperator(task_id="start")

    health_check = PythonOperator(
        task_id="check_api_health",
        python_callable=check_api_health,
        doc_md="Verify FastAPI backend is healthy before starting",
    )

    cs2_tasks = []
    for ticker in CS3_TICKERS:
        task = PythonOperator(
            task_id="cs2_" + ticker.lower(),
            python_callable=collect_cs2_for_ticker,
            op_kwargs={"ticker": ticker},
            execution_timeout=timedelta(minutes=10),
            doc_md="Collect CS2 evidence (jobs, tech, patents) for " + ticker,
        )
        cs2_tasks.append(task)

    cs3_tasks = []
    for ticker in CS3_TICKERS:
        task = PythonOperator(
            task_id="cs3_" + ticker.lower(),
            python_callable=collect_cs3_for_ticker,
            op_kwargs={"ticker": ticker},
            execution_timeout=timedelta(minutes=10),
            doc_md="Collect CS3 signals (Glassdoor, Board, News) for " + ticker,
        )
        cs3_tasks.append(task)

    summary = PythonOperator(
        task_id="collection_summary",
        python_callable=collection_summary,
        trigger_rule=TriggerRule.ALL_DONE,
        doc_md="Log summary of all collection results",
    )

    end = EmptyOperator(
        task_id="end",
        trigger_rule=TriggerRule.ALL_DONE,
    )

    cs2_done = EmptyOperator(task_id="cs2_done", trigger_rule=TriggerRule.ALL_DONE)
    cs3_done = EmptyOperator(task_id="cs3_done", trigger_rule=TriggerRule.ALL_DONE)

    start >> health_check >> cs2_tasks >> cs2_done >> cs3_tasks >> cs3_done >> summary >> end
