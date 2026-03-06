"""
Airflow DAG for Org-AI-R Scoring Pipeline (CS3).

Orchestrates the complete scoring pipeline for 5 PE portfolio companies:
  NVDA, JPM, WMT, GE, DG

Stages:
  1. Wait for evidence collection DAG (ExternalTaskSensor)
  2. Score all 5 companies via API (POST /api/v1/pipeline/score-portfolio)
  3. Validate scores: expected ranges, ranking, 7 dimensions present
  4. Aggregate final portfolio summary

Schedule: Weekly on Mondays at 6am UTC (after evidence collection on Sundays)
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
from airflow.sensors.external_task import ExternalTaskSensor
from airflow.utils.trigger_rule import TriggerRule

# ── Constants ─────────────────────────────────────────────────────

API_BASE = "http://api:8000"
CS3_TICKERS = ["NVDA", "JPM", "WMT", "GE", "DG"]

EXPECTED_RANGES = {
    "NVDA": (85, 95),
    "JPM":  (65, 75),
    "WMT":  (55, 65),
    "GE":   (45, 55),
    "DG":   (35, 45),
}

TOLERANCE = 10

log = logging.getLogger(__name__)

# ── HTTP Helpers (stdlib only) ────────────────────────────────────


def _http_get(url, timeout=10):
    req = Request(url)
    resp = urlopen(req, timeout=timeout)
    return json.loads(resp.read().decode()), resp.status


def _http_post(url, payload=None, timeout=60):
    data = json.dumps(payload or {}).encode()
    req = Request(url, data=data, headers={"Content-Type": "application/json"})
    resp = urlopen(req, timeout=timeout)
    return json.loads(resp.read().decode()), resp.status


# ── Task Callables ────────────────────────────────────────────────


def score_all_companies(**context):
    log.info("Starting portfolio scoring via API...")

    # Wait for API
    for i in range(20):
        try:
            _http_get(API_BASE + "/", timeout=5)
            break
        except Exception:
            time.sleep(5)

    result, _ = _http_post(
        API_BASE + "/api/v1/pipeline/score-portfolio",
        timeout=120,
    )

    scored = result.get("scored", {})
    errors = result.get("errors", {})

    log.info("Scored %d companies", result.get("total_scored", 0))
    for ticker, scores in scored.items():
        log.info("  %s: Org-AI-R = %.1f", ticker, scores.get("final_score", 0))
    if errors:
        log.warning("Errors: %s", errors)

    context["ti"].xcom_push(key="scoring_result", value=result)
    context["ti"].xcom_push(key="scored", value=scored)

    if result.get("total_scored", 0) < 5:
        raise RuntimeError(
            "Only scored %d/5 companies. Errors: %s" % (result.get("total_scored", 0), errors)
        )

    return result


def validate_results(**context):
    ti = context["ti"]
    scored = ti.xcom_pull(task_ids="score_portfolio", key="scored") or {}

    if not scored:
        raise ValueError("No scores found from scoring task")

    errors = []
    warnings = []
    summary_lines = []
    scores = {}

    for ticker in CS3_TICKERS:
        # Fetch evidence summary from API
        try:
            data, _ = _http_get(
                API_BASE + "/api/v1/pipeline/evidence-summary/" + ticker,
                timeout=10,
            )
            log.info("  %s: %d docs, %d signals",
                     ticker, data.get("document_count", 0), data.get("signal_count", 0))
        except Exception as e:
            log.warning("Could not fetch evidence summary for %s: %s", ticker, e)

        if ticker in scored:
            score = scored[ticker].get("final_score", 0)
            scores[ticker] = score

            low, high = EXPECTED_RANGES[ticker]
            in_range = (low - TOLERANCE) <= score <= (high + TOLERANCE)
            status = "PASS" if in_range else "WARN"
            summary_lines.append(
                "  [%s] %s: %.1f (expected %d-%d, tolerance +/-%d)"
                % (status, ticker, score, low, high, TOLERANCE)
            )
            if not in_range:
                warnings.append(
                    "%s: %.1f outside expected %d-%d +/- %d"
                    % (ticker, score, low, high, TOLERANCE)
                )
        else:
            errors.append("%s: Missing from scoring results" % ticker)

    # Check ranking
    if len(scores) == 5:
        highest = max(scores, key=scores.get)
        lowest = min(scores, key=scores.get)

        if highest != "NVDA":
            warnings.append(
                "NVDA (%.1f) is not highest - %s (%.1f) is"
                % (scores.get("NVDA", 0), highest, scores[highest])
            )
        if lowest != "DG":
            warnings.append(
                "DG (%.1f) is not lowest - %s (%.1f) is"
                % (scores.get("DG", 0), lowest, scores[lowest])
            )

    log.info("=" * 55)
    log.info("PORTFOLIO VALIDATION SUMMARY")
    log.info("=" * 55)
    for line in summary_lines:
        log.info(line)
    if warnings:
        log.warning("Warnings:")
        for w in warnings:
            log.warning("  %s", w)
    log.info("=" * 55)

    ti.xcom_push(key="scores", value=scores)
    ti.xcom_push(key="summary", value="\n".join(summary_lines))
    ti.xcom_push(key="warnings", value=warnings)

    if errors:
        raise ValueError("Validation errors:\n" + "\n".join(errors))

    log.info("Validation passed!")
    return scores


def aggregate_portfolio(**context):
    ti = context["ti"]
    scores = ti.xcom_pull(task_ids="validate_results", key="scores") or {}

    if not scores:
        log.warning("No scores to aggregate")
        return {}

    avg = sum(scores.values()) / len(scores)
    ranked = sorted(scores.items(), key=lambda x: -x[1])

    log.info("=" * 55)
    log.info("FINAL PORTFOLIO RANKING (Org-AI-R Scores)")
    log.info("=" * 55)
    for rank, (ticker, score) in enumerate(ranked, 1):
        exp = EXPECTED_RANGES.get(ticker, (0, 100))
        status = "OK" if exp[0] <= score <= exp[1] else "~"
        log.info("  #%d %s: %.1f %s", rank, ticker, score, status)
    log.info("  Portfolio Average: %.1f", avg)
    log.info("=" * 55)

    return {"scores": scores, "average": round(avg, 2)}


# ── Default Args ──────────────────────────────────────────────────

default_args = {
    "owner": "pe-org-air-team",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=3),
}

# ── DAG Definition ────────────────────────────────────────────────

with DAG(
    dag_id="scoring_pipeline",
    default_args=default_args,
    description="CS3: Full Org-AI-R scoring + validation for 5 portfolio companies via API",
    schedule_interval="0 6 * * 1",
    start_date=datetime(2026, 2, 1),
    catchup=False,
    max_active_runs=1,
    tags=["cs3", "scoring", "org-air", "validation"],
    doc_md=__doc__,
) as dag:

    start = EmptyOperator(task_id="start")

    wait_for_evidence = ExternalTaskSensor(
        task_id="wait_for_evidence_collection",
        external_dag_id="evidence_collection_pipeline",
        external_task_id="end",
        allowed_states=["success"],
        failed_states=["failed", "upstream_failed"],
        mode="reschedule",
        poke_interval=10,
        timeout=30,
        soft_fail=True,
        doc_md="Wait for evidence_collection_pipeline to complete (soft-fail if not run)",
    )

    score = PythonOperator(
        task_id="score_portfolio",
        python_callable=score_all_companies,
        execution_timeout=timedelta(minutes=15),
        trigger_rule=TriggerRule.ALL_DONE,
        doc_md="Score all 5 companies via POST /api/v1/pipeline/score-portfolio",
    )

    validate = PythonOperator(
        task_id="validate_results",
        python_callable=validate_results,
        trigger_rule=TriggerRule.ALL_DONE,
        doc_md="Validate scores: expected ranges, ranking, completeness",
    )

    aggregate = PythonOperator(
        task_id="aggregate_portfolio",
        python_callable=aggregate_portfolio,
        trigger_rule=TriggerRule.ALL_DONE,
        doc_md="Log final portfolio ranking and average score",
    )

    end = EmptyOperator(
        task_id="end",
        trigger_rule=TriggerRule.ALL_DONE,
    )

    start >> wait_for_evidence >> score >> validate >> aggregate >> end
