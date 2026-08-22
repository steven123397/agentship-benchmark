#!/usr/bin/env python3

import argparse
import json
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


TERMINAL_STATES = {"rejected", "succeeded", "failed", "cancelled"}


@dataclass(frozen=True)
class HttpResponse:
    status: int
    body: dict


class ContractFailure(AssertionError):
    pass


class UrllibTransport:
    def __init__(self, base_url, timeout=5.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def request(self, method, path, *, json_body=None, headers=None):
        request_headers = {"accept": "application/json", **(headers or {})}
        body = None
        if json_body is not None:
            body = json.dumps(json_body, separators=(",", ":")).encode("utf-8")
            request_headers["content-type"] = "application/json"
        request = Request(
            f"{self.base_url}{path}",
            data=body,
            headers=request_headers,
            method=method,
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                return HttpResponse(response.status, _decode_json(response.read()))
        except HTTPError as error:
            return HttpResponse(error.code, _decode_json(error.read()))
        except URLError as error:
            raise ContractFailure(f"request failed: {method} {path}: {error.reason}") from error


def _decode_json(raw):
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ContractFailure("response is not a UTF-8 JSON object") from error
    if not isinstance(value, dict):
        raise ContractFailure("response JSON must be an object")
    return value


def _envelope(response, expected_status):
    if response.status != expected_status:
        raise ContractFailure(f"expected HTTP {expected_status}, got {response.status}")
    if set(response.body) != {"data", "error"}:
        raise ContractFailure("response must use the exact {data,error} envelope")
    return response.body


def _error_code(response, expected_status):
    body = _envelope(response, expected_status)
    error = body.get("error")
    if not isinstance(error, dict) or not isinstance(error.get("code"), str):
        raise ContractFailure("error response must contain a stable error.code")
    return error["code"]


def _query_run(response, expected_status):
    body = _envelope(response, expected_status)
    data = body.get("data")
    if isinstance(data, dict) and isinstance(data.get("query_run"), dict):
        run = data["query_run"]
    elif isinstance(data, dict) and "id" in data and "status" in data:
        run = data
    else:
        raise ContractFailure("response data must contain query_run facts")
    if not isinstance(run.get("id"), str) or not isinstance(run.get("status"), str):
        raise ContractFailure("query run must contain string id and status")
    return run


class ContractSuite:
    def __init__(self, transport, *, poll_interval=0.25, poll_timeout=30.0):
        self.transport = transport
        self.poll_interval = poll_interval
        self.poll_timeout = poll_timeout
        self.results = []

    def run(self):
        cases = [
            ("health_and_readiness", self._health_and_readiness),
            ("pagination_validation", self._pagination_validation),
            ("missing_run", self._missing_run),
            ("policy_rejection_idempotency", self._policy_rejection_idempotency),
            ("submission_idempotency_and_result", self._submission_idempotency_and_result),
            ("catalog_cast_is_rejected", self._catalog_cast_is_rejected),
        ]
        for name, case in cases:
            try:
                case()
            except Exception as error:
                self.results.append({"name": name, "status": "failed", "detail": str(error)})
            else:
                self.results.append({"name": name, "status": "passed", "detail": None})
        passed = sum(result["status"] == "passed" for result in self.results)
        return {
            "schemaVersion": 1,
            "summary": {"passed": passed, "failed": len(self.results) - passed},
            "cases": self.results,
        }

    def _health_and_readiness(self):
        health = _envelope(self.transport.request("GET", "/health"), 200)
        ready = _envelope(self.transport.request("GET", "/ready"), 200)
        if health["error"] is not None or ready["error"] is not None:
            raise ContractFailure("healthy and ready responses must not contain an error")

    def _pagination_validation(self):
        response = self.transport.request("GET", "/api/v1/query-runs?limit=0")
        if _error_code(response, 422) != "invalid_pagination":
            raise ContractFailure("invalid limit must return invalid_pagination")

    def _missing_run(self):
        path = "/api/v1/query-runs/00000000-0000-4000-8000-000000000000"
        if _error_code(self.transport.request("GET", path), 404) != "query_run_not_found":
            raise ContractFailure("missing run must return query_run_not_found")

    def _policy_rejection_idempotency(self):
        headers = {"Idempotency-Key": f"hidden-reject-{uuid.uuid4()}"}
        first_response = self.transport.request(
            "POST", "/api/v1/query-runs", json_body={"sql": "DELETE FROM customers"}, headers=headers
        )
        first = _query_run(first_response, 422)
        if _error_code(first_response, 422) != "sql_statement_not_allowed" or first["status"] != "rejected":
            raise ContractFailure("disallowed statement must create a rejected run")
        replay_response = self.transport.request(
            "POST", "/api/v1/query-runs", json_body={"sql": "DELETE FROM customers"}, headers=headers
        )
        replay = _query_run(replay_response, 422)
        if replay["id"] != first["id"] or replay["status"] != "rejected":
            raise ContractFailure("rejected idempotency replay must return the original run")

    def _submission_idempotency_and_result(self):
        headers = {"Idempotency-Key": f"hidden-submit-{uuid.uuid4()}"}
        sql = "SELECT count(*) AS customer_count FROM customers"
        first = _query_run(
            self.transport.request("POST", "/api/v1/query-runs", json_body={"sql": sql}, headers=headers),
            202,
        )
        replay = _query_run(
            self.transport.request("POST", "/api/v1/query-runs", json_body={"sql": sql}, headers=headers),
            202,
        )
        if replay["id"] != first["id"]:
            raise ContractFailure("submission replay must return the original run")
        conflict = self.transport.request(
            "POST",
            "/api/v1/query-runs",
            json_body={"sql": "SELECT count(*) AS product_count FROM products"},
            headers=headers,
        )
        if _error_code(conflict, 409) != "idempotency_conflict":
            raise ContractFailure("same key with different SQL must conflict")

        run = self._poll_terminal(first["id"])
        if run["status"] != "succeeded":
            raise ContractFailure(f"known valid query ended as {run['status']}")
        result_body = _envelope(
            self.transport.request("GET", f"/api/v1/query-runs/{first['id']}/result"), 200
        )
        result = result_body["data"]
        if isinstance(result, dict) and isinstance(result.get("result"), dict):
            result = result["result"]
        if not isinstance(result, dict):
            raise ContractFailure("result endpoint must return a result object")
        if result.get("rows") != [["100"]] or result.get("truncated") is not False:
            raise ContractFailure("customer count must preserve bigint string value without truncation")
        columns = result.get("columns")
        if not isinstance(columns, list) or not columns or columns[0].get("type") != "bigint":
            raise ContractFailure("result columns must preserve the bigint type")

        history = _envelope(self.transport.request("GET", "/api/v1/query-runs?limit=1"), 200)
        if history["data"] is None or history["error"] is not None:
            raise ContractFailure("history endpoint must return paginated data")

        retry = self.transport.request("POST", f"/api/v1/query-runs/{run['id']}/retry")
        if _error_code(retry, 409) != "query_run_not_retryable":
            raise ContractFailure("succeeded run must not be retryable")
        cancelled = _query_run(
            self.transport.request("POST", f"/api/v1/query-runs/{run['id']}/cancel"), 200
        )
        if cancelled["id"] != run["id"] or cancelled["status"] != "succeeded":
            raise ContractFailure("late cancellation must preserve succeeded terminal state")

    def _poll_terminal(self, run_id):
        deadline = time.monotonic() + self.poll_timeout
        while time.monotonic() <= deadline:
            run = _query_run(self.transport.request("GET", f"/api/v1/query-runs/{run_id}"), 200)
            if run["status"] in TERMINAL_STATES:
                return run
            time.sleep(self.poll_interval)
        raise ContractFailure(f"run {run_id} did not reach a terminal state")

    def _catalog_cast_is_rejected(self):
        response = self.transport.request(
            "POST", "/api/v1/query-runs", json_body={"sql": "SELECT 'pg_catalog.int4'::regtype::text"}
        )
        run = _query_run(response, 422)
        if _error_code(response, 422) != "sql_object_not_allowed" or run["status"] != "rejected":
            raise ContractFailure("catalog-resolving cast must be rejected before execution")


def main():
    parser = argparse.ArgumentParser(description="Run the DecisionHarbor v0.2.0 hidden HTTP contract suite.")
    parser.add_argument("--api-url", required=True)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--request-timeout", type=float, default=5.0)
    parser.add_argument("--poll-timeout", type=float, default=30.0)
    args = parser.parse_args()
    suite = ContractSuite(
        UrllibTransport(args.api_url, timeout=args.request_timeout),
        poll_timeout=args.poll_timeout,
    )
    report = suite.run()
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.report:
        args.report.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 1 if report["summary"]["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
