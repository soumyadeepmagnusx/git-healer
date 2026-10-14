from githealer.parsers.ci_log_parser import CILogParser

SAMPLE_PYTEST_LOG = """
============================= test session starts =============================
platform linux -- Python 3.11.0, pytest-7.4.0
rootdir: /home/runner/work/my-app
collected 3 items

tests/test_math.py .F.                                                   [100%]

================================== FAILURES ===================================
___________________________ test_divide_by_zero ___________________________

    def test_divide_by_zero():
>       divide(10, 0)

tests/test_math.py:14: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

a = 10, b = 0

    def divide(a, b):
>       return a / b
E       ZeroDivisionError: division by zero

app/math.py:8: ZeroDivisionError
=========================== short test summary info ===========================
FAILED tests/test_math.py::test_divide_by_zero - ZeroDivisionError: division by zero
========================= 1 failed, 2 passed in 0.05s =========================
"""

def test_parse_pytest_failure():
    failures = CILogParser.parse(SAMPLE_PYTEST_LOG)
    assert len(failures) == 1
    f = failures[0]
    assert f.test_name == "test_divide_by_zero"
    assert f.error_type == "ZeroDivisionError"
    assert "division by zero" in f.error_message
    assert f.framework == "pytest"

def test_parse_generic_traceback():
    traceback_log = """
Traceback (most recent call last):
  File "src/main.py", line 42, in process_data
    raise ValueError("Invalid configuration provided")
ValueError: Invalid configuration provided
"""
    failures = CILogParser.parse(traceback_log)
    assert len(failures) >= 1
    assert failures[0].error_type == "ValueError"
    assert "Invalid configuration provided" in failures[0].error_message
