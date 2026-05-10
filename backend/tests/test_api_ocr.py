import os
import unittest
from unittest.mock import patch

try:
    import multipart  # noqa: F401

    HAS_MULTIPART = True
except Exception:
    HAS_MULTIPART = False


class OcrApiTests(unittest.TestCase):
    def setUp(self):
        self._old_env = dict(os.environ)
        os.environ["SKIP_DB_INIT"] = "1"

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._old_env)

    @unittest.skipUnless(HAS_MULTIPART, "python-multipart is not installed")
    def test_ocr_api_returns_unified_response(self):
        from fastapi.testclient import TestClient
        from backend import main as backend_main

        client = TestClient(backend_main.app)

        ocr_payload = {
            "ocr_result": ["TOTAL 5.20"],
            "extracted_info": {
                "merchant": None,
                "amount": 5.20,
                "transaction_time": "2026-03-09 00:00:00",
                "payment_method": "???",
                "category": "??",
            },
            "saved": True,
            "save_reason": "ok",
            "llm_meta": {
                "selected_amount_id": "a0",
                "match_status": "matched",
                "match_failure_reason": None,
                "amount_override_reason": None,
            },
            "ocr_meta": {"ocr_elapsed_ms": 10, "llm_enabled": True, "llm_fallback": False},
        }

        with patch("backend.routers.ocr_router.process_ocr_upload", return_value=ocr_payload):
            resp = client.post(
                "/ocr",
                files={"file": ("test.png", b"fake-image-bytes", "image/png")},
            )

        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["code"], 0)
        self.assertEqual(body["message"], "success")
        self.assertIn("data", body)
        self.assertIn("extracted_info", body["data"])
        self.assertIn("transaction_time", body["data"]["extracted_info"])
        self.assertIn("llm_meta", body["data"])
        self.assertEqual(body["data"]["llm_meta"]["match_status"], "matched")


if __name__ == "__main__":
    unittest.main()
