import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from contract_harness import ContractSuite, HttpResponse


RUN_ID = "11111111-1111-4111-8111-111111111111"
REJECTED_ID = "22222222-2222-4222-8222-222222222222"


def envelope(*, data=None, error=None):
    return {"data": data, "error": error}


class ScriptedTransport:
    def __init__(self, exchanges):
        self.exchanges = list(exchanges)

    def request(self, method, path, *, json_body=None, headers=None):
        expected_method, expected_path, response = self.exchanges.pop(0)
        if (method, path) != (expected_method, expected_path):
            raise AssertionError(
                f"expected {expected_method} {expected_path}, got {method} {path}"
            )
        return response


class ContractSuiteTests(unittest.TestCase):
    def test_compliant_public_contract_passes(self):
        rejected = {"query_run": {"id": REJECTED_ID, "status": "rejected"}}
        queued = {"query_run": {"id": RUN_ID, "status": "queued"}}
        succeeded = {"query_run": {"id": RUN_ID, "status": "succeeded"}}
        transport = ScriptedTransport(
            [
                ("GET", "/health", HttpResponse(200, envelope(data={"status": "ok"}))),
                ("GET", "/ready", HttpResponse(200, envelope(data={"status": "ready"}))),
                ("GET", "/api/v1/query-runs?limit=0", HttpResponse(422, envelope(error={"code": "invalid_pagination"}))),
                ("GET", "/api/v1/query-runs/00000000-0000-4000-8000-000000000000", HttpResponse(404, envelope(error={"code": "query_run_not_found"}))),
                ("POST", "/api/v1/query-runs", HttpResponse(422, envelope(data=rejected, error={"code": "sql_statement_not_allowed"}))),
                ("POST", "/api/v1/query-runs", HttpResponse(422, envelope(data=rejected, error={"code": "sql_statement_not_allowed"}))),
                ("POST", "/api/v1/query-runs", HttpResponse(202, envelope(data=queued))),
                ("POST", "/api/v1/query-runs", HttpResponse(202, envelope(data=queued))),
                ("POST", "/api/v1/query-runs", HttpResponse(409, envelope(error={"code": "idempotency_conflict"}))),
                ("GET", f"/api/v1/query-runs/{RUN_ID}", HttpResponse(200, envelope(data=succeeded))),
                ("GET", f"/api/v1/query-runs/{RUN_ID}/result", HttpResponse(200, envelope(data={"columns": [{"name": "customer_count", "type": "bigint"}], "rows": [["100"]], "truncated": False}))),
                ("GET", "/api/v1/query-runs?limit=1", HttpResponse(200, envelope(data={"items": [succeeded["query_run"]], "next_cursor": None}))),
                ("POST", f"/api/v1/query-runs/{RUN_ID}/retry", HttpResponse(409, envelope(error={"code": "query_run_not_retryable"}))),
                ("POST", f"/api/v1/query-runs/{RUN_ID}/cancel", HttpResponse(200, envelope(data=succeeded))),
                ("POST", "/api/v1/query-runs", HttpResponse(422, envelope(data=rejected, error={"code": "sql_object_not_allowed"}))),
            ]
        )

        report = ContractSuite(transport, poll_interval=0, poll_timeout=1).run()

        self.assertEqual(report["summary"], {"passed": 6, "failed": 0})
        self.assertFalse(transport.exchanges)


if __name__ == "__main__":
    unittest.main()
