import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import HTTPException

import app


class GroqConfigurationTests(unittest.TestCase):
    def test_uses_groq_sdk_with_supported_model_settings(self):
        completion = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="Mock coaching reply"))])
        with patch.dict(os.environ, {"GROQ_API_KEY": "unit-test-key"}, clear=True):
            with patch("app.Groq") as mocked_groq:
                mocked_groq.return_value.chat.completions.create.return_value = completion
                result = app.ask_ai([{"role": "user", "content": "Review this resume."}])

        mocked_groq.assert_called_once_with(
            api_key="unit-test-key",
            base_url="https://api.groq.com",
        )
        self.assertEqual(result, "Mock coaching reply")
        mocked_groq.return_value.chat.completions.create.assert_called_once_with(
            model="openai/gpt-oss-120b",
            messages=[{"role": "user", "content": "Review this resume."}],
            temperature=1,
            max_completion_tokens=2048,
            top_p=1,
            reasoning_effort="medium",
            stream=False,
            stop=None,
        )

    def test_missing_local_key_returns_setup_error(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(HTTPException) as error:
                app.ask_ai([{"role": "user", "content": "Review this resume."}])

        self.assertEqual(error.exception.status_code, 503)
        self.assertIn(".env.local", error.exception.detail)


if __name__ == "__main__":
    unittest.main()