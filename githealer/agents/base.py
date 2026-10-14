from __future__ import annotations

import re
import json
from typing import Optional, Dict, Any
from githealer.llm.client import GeminiClient


class BaseAgent:
    """Base class for specialized GitHealer subagents."""

    def __init__(self, llm_client: Optional[GeminiClient] = None):
        self.llm = llm_client or GeminiClient()

    @staticmethod
    def extract_json(text: str) -> Dict[str, Any]:
        """Safely extract JSON object from markdown fenced blocks or raw text."""
        # Check ```json ... ```
        json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
        if json_match:
            candidate = json_match.group(1).strip()
            try:
                return json.loads(candidate)
            except Exception:
                pass

        # Try finding outermost { ... }
        brace_match = re.search(r"\{[\s\S]*\}", text)
        if brace_match:
            try:
                return json.loads(brace_match.group(0))
            except Exception:
                pass

        # Fallback raw parse
        return json.loads(text)

    @staticmethod
    def extract_code_block(text: str, language: str = "") -> str:
        """Extract code from ```lang ... ``` or return stripped text."""
        pattern = rf"```{language}\s*([\s\S]*?)\s*```"
        match = re.search(pattern, text)
        if match:
            return match.group(1).rstrip()
        generic_match = re.search(r"```\s*([\s\S]*?)\s*```", text)
        if generic_match:
            return generic_match.group(1).rstrip()
        return text.strip()
