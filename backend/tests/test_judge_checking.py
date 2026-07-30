import pytest

from src.judge import *

@pytest.mark.parametrize("a,b,expected", [
    ("1\n2\n3\n", "1\n2\n3\n", True),
    ("1\n2\n3\n", "1\n2\n3", True),
    ("1\n2\n3\n", "12\n3\n", False),
    ("1\r\n2\r\n3\r", "1\n2\n3\n", True),
    ("1\n\r2\r\n3\r", "1\n2\n3\n", False),
    ("1\r2\r3\r", "1\n2\n3", True),
    ("1 \n2 \n3\n", "1\n2\n3\n", True),
    ("1 \r\n2 \n3\n", "1\n2\n3\n", True),
    ("1 \r2 \n3\n", "1\n2\n3\n", True),
    ("1 \n\r2 \n3\n", "1\n2\n3\n", False),

    ("hello", "hello", True),
    ("hello\n", "hello", True),
    ("hello\n", "hello\n", True),
    ("hello\r", "hello\n", True),
    ("hello\r", "hello\r", True),
    ("hello\r\n", "hello\r\n", True),
    ("hello\r\n", "hello\n", True),
    ("hello\r\n", "hello\r", True),
    ("hello\r \n", "hello\r", True),
    ("hello\r \nHello", "hello\rHello", False),
    ("hello\n\n", "hello", True),
    ("\nhello", "hello", False),
    ("hello", "jello", False),
    ("hello   ", "hello      ", True),
    ("    hello", "hello", False),
    ("1 2 3 4", "1 2 3 4", True),
    ("1  2\n 3 4", "1 2\n 3 4", False),
    ("1 2\n  3 4", "1 2\n 3 4", False),
])
def test_output_checking(a, b, expected):
    assert output_equal(a, b) == expected