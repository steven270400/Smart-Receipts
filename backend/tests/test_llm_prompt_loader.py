import json
import os
import tempfile
import time
import unittest
from pathlib import Path

from backend import llm_service


class LlmPromptLoaderTests(unittest.TestCase):
    def setUp(self):
        self._old_path = llm_service._PROMPT_CONFIG_PATH
        self._old_cache = llm_service._PROMPT_CACHE
        self._old_mtime = llm_service._PROMPT_MTIME

    def tearDown(self):
        llm_service._PROMPT_CONFIG_PATH = self._old_path
        llm_service._PROMPT_CACHE = self._old_cache
        llm_service._PROMPT_MTIME = self._old_mtime

    def _write_prompt_file(self, path: Path, system_text: str) -> None:
        payload = {
            "system": system_text,
            "amount_rules": ["规则A", "规则B"],
            "output_schema": {"amount_id": "string|null"},
        }
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    def test_load_prompt_config_success(self):
        with tempfile.TemporaryDirectory() as td:
            prompt_path = Path(td) / "prompt.json"
            self._write_prompt_file(prompt_path, "中文系统提示词")
            llm_service._PROMPT_CONFIG_PATH = prompt_path
            llm_service._PROMPT_CACHE = None
            llm_service._PROMPT_MTIME = None

            cfg = llm_service._load_prompt_config()
            self.assertEqual(cfg["system"], "中文系统提示词")
            self.assertEqual(cfg["amount_rules"][0], "规则A")
            self.assertIn("amount_id", cfg["output_schema"])

    def test_load_prompt_config_invalid_json(self):
        with tempfile.TemporaryDirectory() as td:
            prompt_path = Path(td) / "prompt.json"
            prompt_path.write_text("{invalid json", encoding="utf-8")
            llm_service._PROMPT_CONFIG_PATH = prompt_path
            llm_service._PROMPT_CACHE = None
            llm_service._PROMPT_MTIME = None

            with self.assertRaises(llm_service.LlmError) as ctx:
                llm_service._load_prompt_config()
            self.assertIn("prompt_config_invalid:json_parse_failed", str(ctx.exception))

    def test_load_prompt_config_missing_required_field(self):
        with tempfile.TemporaryDirectory() as td:
            prompt_path = Path(td) / "prompt.json"
            prompt_path.write_text(
                json.dumps({"amount_rules": ["规则"], "output_schema": {}}),
                encoding="utf-8",
            )
            llm_service._PROMPT_CONFIG_PATH = prompt_path
            llm_service._PROMPT_CACHE = None
            llm_service._PROMPT_MTIME = None

            with self.assertRaises(llm_service.LlmError) as ctx:
                llm_service._load_prompt_config()
            self.assertIn("prompt_config_invalid:system", str(ctx.exception))

    def test_prompt_cache_hot_reload_by_mtime(self):
        with tempfile.TemporaryDirectory() as td:
            prompt_path = Path(td) / "prompt.json"
            self._write_prompt_file(prompt_path, "系统提示词-v1")
            llm_service._PROMPT_CONFIG_PATH = prompt_path
            llm_service._PROMPT_CACHE = None
            llm_service._PROMPT_MTIME = None

            cfg1 = llm_service._load_prompt_config()
            self.assertEqual(cfg1["system"], "系统提示词-v1")

            self._write_prompt_file(prompt_path, "系统提示词-v2")
            now = time.time() + 2.0
            os.utime(prompt_path, (now, now))

            cfg2 = llm_service._load_prompt_config()
            self.assertEqual(cfg2["system"], "系统提示词-v2")


if __name__ == "__main__":
    unittest.main()
