"""Kiem thu FastAPI contract cua web demo."""

import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from app import app


class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_health_endpoint(self):
        response = self.client.get("/api/health")

        self.assertEqual(200, response.status_code)
        self.assertEqual({"status": "ok", "service": "topic36-api"}, response.json())

    @unittest.skipUnless(Path("dist/index.html").is_file(), "frontend build is absent")
    def test_production_bundle_is_served_by_fastapi(self):
        response = self.client.get("/")

        self.assertEqual(200, response.status_code)
        self.assertIn('<div id="root"></div>', response.text)
        self.assertIn('/assets/index-', response.text)

    def test_simulate_returns_real_deterministic_session(self):
        payload = {"mssv": "2312345", "steps": 3}

        first = self.client.post("/api/simulate", json=payload)
        second = self.client.post("/api/simulate", json=payload)

        self.assertEqual(200, first.status_code)
        self.assertEqual(first.json(), second.json())
        self.assertEqual(3, len(first.json()["timeline"]))
        self.assertEqual(3, len(first.json()["sensors"]))

    def test_simulate_rejects_invalid_input_without_stack_trace(self):
        invalid_payloads = (
            {"mssv": "   ", "steps": 10},
            {"mssv": "2312345", "steps": 0},
            {"mssv": "2312345", "steps": 201},
            {"mssv": "2312345", "steps": 1.5},
            {"mssv": "A" * 65, "steps": 10},
        )

        for payload in invalid_payloads:
            with self.subTest(payload=payload):
                response = self.client.post("/api/simulate", json=payload)
                self.assertEqual(422, response.status_code)
                self.assertNotIn("Traceback", response.text)


if __name__ == "__main__":
    unittest.main()
