import pytest
from calculator import add, subtract, multiply, divide

def test_add():
    assert add(10, 5) == 15

def test_subtract():
    assert subtract(10, 5) == 5

def test_multiply():
    assert multiply(10, 5) == 50

def test_divide():
    assert divide(10, 2) == 5

def test_divide_by_zero():
    # Expects ValueError to be raised on division by zero
    with pytest.raises(ValueError, match="Cannot divide by zero"):
        divide(10, 0)
