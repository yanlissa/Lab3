import pytest

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import calc
from calc import Number, UnaryOp, BinaryOp, Function
import math


#корректные выражения
@pytest.mark.parametrize(
    ("expr", "expected_ast"),
    [
        # одно число (1‑, 2‑, 3‑значные / дробные)
        ("7",      Number(7.0)),
        ("42",     Number(42.0)),
        ("123",    Number(123.0)),
        ("3.14",   Number(3.14)),
        (".5",     Number(0.5)),
        # унарный минус
        ("-8",     UnaryOp("-", Number(8.0))),
        ("--8",    UnaryOp(op='-', expr=UnaryOp(op='-', expr=Number(value=8.0)))),
        # комбинации операций (+, -, *, /) без скобок
        ("1+2",          BinaryOp(Number(1), "+", Number(2))),
        ("1+2*3",        BinaryOp(Number(1), "+",
                                  BinaryOp(Number(2), "*", Number(3)))),
        ("-4+3*2/1",
         BinaryOp(UnaryOp("-", Number(4)), "+",
                  BinaryOp(BinaryOp(Number(3), "*", Number(2)),
                           "/", Number(1)))),
        # научная нотация и скобки (этап 2)
        ("1.25e+09", Number(1250000000.0)),
        ("3^4", BinaryOp(Number(3), "^", Number(4))),
        ("1 + 2 * (3 + 4)",
         BinaryOp(Number(1), "+",
                  BinaryOp(Number(2), "*",
                           BinaryOp(Number(3), "+", Number(4))))),
        # функции и константы (этап 3)
        ("pi", Number(math.pi)),
        ("e", Number(math.e)),
        ("sin(90)", Function("sin", Number(90.0))),
        ("sqrt(4^2*5+1)",
         Function("sqrt",
                BinaryOp(
                    BinaryOp(
                        BinaryOp(Number(4), "^", Number(2)),
                        "*",
                        Number(5)
                    ),
                    "+",
                    Number(1)
        ))),
    ],
)
def test_parser_success(expr, expected_ast):
    ast = calc.parser(calc.lexer(expr))
    assert ast == expected_ast


# некорректные выражения
@pytest.mark.parametrize(
    ("expr", "expected_error"),
    [
        ("",            "Unexpected end of expression"),
        ("2 @ 4",       "Invalid character: '@'"),
        ("2 /",         "Invalid expression"),
        ("1 1 + 2",     "Invalid number: digits separated by space"),
        ("1 + 4i",      "Unknown function or constant: i"),
        ("abc",         "Unknown function or constant: abc"),
        ("1..5",        "Invalid number format"),
        ("1+",          "Invalid expression"),
        ("(1+",         "Mismatched parentheses"),
        ("sin 90",      "Expected '\\(' after function sin"),
        ("sin(90",      "Mismatched parentheses"),
        ("(90",         "Mismatched parentheses"),
        ("unknown(1)",  "Unknown function or constant: unknown"),
    ],
)
def test_parser_fail(expr, expected_error):
    with pytest.raises(ValueError, match=expected_error):
        calc.parser(calc.lexer(expr))