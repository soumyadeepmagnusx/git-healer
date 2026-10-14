from __future__ import annotations

import re
from typing import List, Optional
from githealer.models import TestFailure


class CILogParser:
    """Parses raw CI / build logs into structured TestFailure objects."""

    @classmethod
    def parse(cls, log_content: str) -> List[TestFailure]:
        failures: List[TestFailure] = []

        # Strip ANSI escape codes
        clean_log = re.sub(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])", "", log_content)

        # 1. Try Pytest parser
        pytest_failures = cls._parse_pytest(clean_log)
        if pytest_failures:
            failures.extend(pytest_failures)

        # 2. Try Node / Jest parser if no pytest failures found
        if not failures:
            jest_failures = cls._parse_jest(clean_log)
            if jest_failures:
                failures.extend(jest_failures)

        # 3. Try Go test parser
        if not failures:
            go_failures = cls._parse_go(clean_log)
            if go_failures:
                failures.extend(go_failures)

        # 4. Fallback to generic Python traceback or generic error parser
        if not failures:
            generic_failures = cls._parse_python_traceback(clean_log)
            if generic_failures:
                failures.extend(generic_failures)

        # 5. Last-ditch generic extractor
        if not failures:
            failures = cls._parse_generic(clean_log)

        return failures

    @staticmethod
    def _parse_pytest(log: str) -> List[TestFailure]:
        failures = []

        # Pattern 1: Summary lines: FAILED tests/test_calc.py::test_divide_by_zero - ZeroDivisionError: division by zero
        summary_pattern = re.compile(
            r"FAILED\s+([^\s:]+)::([^\s\-]+)(?:\s*-\s*([A-Za-z0-9_]+Error|[A-Za-z0-9_]+Exception|[A-Za-z0-9_]+)?(?::\s*(.*))?)?",
            re.MULTILINE
        )

        # Pattern 2: Detailed block header: ________________________ test_name ________________________
        block_pattern = re.compile(
            r"_{10,}\s+([A-Za-z0-9_]+(?:::?[A-Za-z0-9_]+)*)\s+_{10,}(.*?)(?=(?:_{10,}\s+[A-Za-z0-9_]+|\Z|=+ short test summary info =+))",
            re.DOTALL
        )

        blocks = {m.group(1): m.group(2) for m in block_pattern.finditer(log)}

        for m in summary_pattern.finditer(log):
            file_path = m.group(1)
            test_name = m.group(2)
            error_type = m.group(3) or "AssertionError"
            error_message = (m.group(4) or "").strip()

            stack = ""
            for b_name, b_text in blocks.items():
                if test_name in b_name or b_name in test_name:
                    stack = b_text.strip()
                    # Try to extract file and line from stack if not found
                    line_match = re.search(r"(\S+\.py):(\d+):", stack)
                    if line_match:
                        file_path = line_match.group(1)
                        line_number = int(line_match.group(2))
                    break
            else:
                line_number = None

            failures.append(TestFailure(
                test_name=test_name,
                file_path=file_path,
                line_number=line_number if 'line_number' in locals() and line_number else None,
                error_type=error_type,
                error_message=error_message,
                stack_trace=stack or log[-2000:],
                framework="pytest"
            ))

        return failures

    @staticmethod
    def _parse_jest(log: str) -> List[TestFailure]:
        failures = []
        # Pattern: FAIL src/utils.test.ts or ✕ should do something
        file_matches = re.findall(r"FAIL\s+([^\s\n]+\.(?:js|jsx|ts|tsx))", log)
        test_matches = re.findall(r"[✕×]\s+([^\n\r]+)", log)

        if file_matches or test_matches:
            target_file = file_matches[0] if file_matches else None
            for test_desc in (test_matches or ["Jest test failure"]):
                failures.append(TestFailure(
                    test_name=test_desc.strip(),
                    file_path=target_file,
                    error_type="JestFailure",
                    error_message=test_desc.strip(),
                    stack_trace=log[-2500:],
                    framework="jest"
                ))

        return failures

    @staticmethod
    def _parse_go(log: str) -> List[TestFailure]:
        failures = []
        # Pattern: --- FAIL: TestAdd (0.00s)
        matches = re.finditer(r"---\s+FAIL:\s+([A-Za-z0-9_]+)\s+\([^\)]+\)\s*\n\s*([^\n:]+):(\d+):\s*(.*)", log)
        for m in matches:
            failures.append(TestFailure(
                test_name=m.group(1),
                file_path=m.group(2),
                line_number=int(m.group(3)),
                error_type="GoTestFailure",
                error_message=m.group(4).strip(),
                stack_trace=log[-1500:],
                framework="go"
            ))
        return failures

    @staticmethod
    def _parse_python_traceback(log: str) -> List[TestFailure]:
        failures = []
        # Look for standard Python Traceback
        tb_matches = re.finditer(
            r"Traceback \(most recent call last\):\s*\n(.*?)\n([A-Za-z0-9_]+Error|[A-Za-z0-9_]+Exception):\s*(.*)",
            log,
            re.DOTALL
        )
        for m in tb_matches:
            tb_body = m.group(1)
            err_type = m.group(2)
            err_msg = m.group(3).strip()

            # Find last File line
            file_matches = list(re.finditer(r'File "([^"]+)", line (\d+), in (\S+)', tb_body))
            if file_matches:
                last_file = file_matches[-1]
                failures.append(TestFailure(
                    test_name=last_file.group(3),
                    file_path=last_file.group(1),
                    line_number=int(last_file.group(2)),
                    error_type=err_type,
                    error_message=err_msg,
                    stack_trace=f"Traceback (most recent call last):\n{tb_body}\n{err_type}: {err_msg}",
                    framework="python"
                ))
        return failures

    @staticmethod
    def _parse_generic(log: str) -> List[TestFailure]:
        lines = [line.strip() for line in log.splitlines() if line.strip()]
        error_lines = [l for l in lines if any(k in l.lower() for k in ["error:", "failed:", "fatal:", "panic:"])]

        msg = error_lines[-1] if error_lines else "Unknown CI failure"
        return [
            TestFailure(
                test_name="CI_Failure",
                error_type="BuildError",
                error_message=msg[:300],
                stack_trace="\n".join(lines[-40:]),
                framework="generic"
            )
        ]
