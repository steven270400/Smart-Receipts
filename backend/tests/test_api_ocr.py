import os
import unittest
from unittest.mock import patch


class OcrApiTests(unittest.TestCase):
    def setUp(self):
        self._old_env = dict(os.environ)
        os.environ["SKIP_DB_INIT"] = "1"

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._old_env)

    def test_ocr_api_returns_single_extracted_info_dict(self):
        from fastapi.testclient import TestClient
        from backend import main as backend_main

        client = TestClient(backend_main.app)

        texts = ["TOTAL 5.20", "Date 2026/3/9", "支付宝"]
        extracted = {
            "merchant": None,
            "amount": 5.20,
            "date": "2026-03-09",
            "payment_method": "支付宝",
            "category": "其他",
        }
        llm_meta = {"llm_enabled": True, "invoked": True, "model": "fake"}
        saved_payloads: list[dict] = []

        with (
            patch.object(backend_main, "recognize_text", return_value=texts),
            patch.object(backend_main, "extract_receipt_info_with_meta", return_value=(extracted, llm_meta)),
            patch.object(backend_main, "save_receipt", side_effect=lambda payload: saved_payloads.append(payload)),
        ):
            resp = client.post(
                "/ocr",
                files={"file": ("test.png", b"fake-image-bytes", "image/png")},
            )

        self.assertEqual(resp.status_code, 200)
        body = resp.json()

        self.assertIn("extracted_info", body)
        extracted_info = body["extracted_info"]
        self.assertEqual(
            set(extracted_info.keys()),
            {"merchant", "amount", "date", "payment_method", "category"},
        )
        self.assertNotIn("llm_meta", extracted_info)

        # Ensure llm_meta is stored only inside extracted_json passed to save_receipt.
        self.assertEqual(len(saved_payloads), 1)
        self.assertIn("extracted_json", saved_payloads[0])
        self.assertIn("llm_meta", saved_payloads[0]["extracted_json"])

    def test_ocr_api_llm_failure_still_falls_back_and_returns_200(self):
        from fastapi.testclient import TestClient
        from backend import main as backend_main

        client = TestClient(backend_main.app)

        texts = ["TOTAL 5.20", "Date 2026/3/9"]
        extracted = {
            "merchant": None,
            "amount": 5.20,
            "date": "2026-03-09",
            "payment_method": None,
            "category": "其他",
        }
        llm_meta = {"llm_enabled": True, "invoked": True, "error": "timeout"}

        with (
            patch.object(backend_main, "recognize_text", return_value=texts),
            patch.object(backend_main, "extract_receipt_info_with_meta", return_value=(extracted, llm_meta)),
            patch.object(backend_main, "save_receipt", return_value=None),
        ):
            resp = client.post(
                "/ocr",
                files={"file": ("test.png", b"fake-image-bytes", "image/png")},
            )

        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertTrue(body["saved"])
        self.assertEqual(body["save_reason"], "ok")


if __name__ == "__main__":
    unittest.main()

