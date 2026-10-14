from __future__ import annotations

import json
import os
import urllib.request
import urllib.error
from typing import Optional, Dict, Any


class GeminiClient:
    """Lightweight, resilient client for Gemini models using standard library HTTP."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-2.5-flash"):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self.model = model
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"

    def is_available(self) -> bool:
        """Return True if an API key is configured."""
        return bool(self.api_key and len(self.api_key.strip()) > 5)

    def generate(self, prompt: str, system_instruction: Optional[str] = None, temperature: float = 0.2) -> str:
        """Call Gemini generateContent endpoint."""
        if not self.is_available():
            raise ValueError(
                "Gemini API key is not configured. Set the GEMINI_API_KEY environment variable "
                "or pass it in .githealer.yaml. (Run `githealer demo` to test with mock offline solver)."
            )

        url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"

        contents = [{"parts": [{"text": prompt}]}]
        body: Dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": 4096
            }
        }

        if system_instruction:
            body["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }

        payload = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"}
        )

        try:
            with urllib.request.urlopen(req, timeout=45) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                candidates = res_data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "")
                return ""
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8", "replace")
            raise RuntimeError(f"Gemini API HTTP {e.code}: {error_body}")
        except Exception as e:
            raise RuntimeError(f"Gemini API Request failed: {str(e)}")
