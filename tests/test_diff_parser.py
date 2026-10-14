from githealer.parsers.diff_parser import DiffParser

def test_generate_diff():
    orig = "def hello():\n    return 'world'\n"
    mod = "def hello():\n    return 'GitHealer'\n"
    diff = DiffParser.generate_diff(orig, mod, filename="test.py")
    assert "-    return 'world'" in diff
    assert "+    return 'GitHealer'" in diff

def test_validate_syntax_valid_python():
    code = "def valid():\n    pass\n"
    valid, err = DiffParser.validate_syntax(code, "test.py")
    assert valid is True
    assert err is None

def test_validate_syntax_invalid_python():
    code = "def invalid(:\n    pass\n"
    valid, err = DiffParser.validate_syntax(code, "test.py")
    assert valid is False
    assert err is not None
