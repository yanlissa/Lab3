import pytest

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import calc
from calc import Number, UnaryOp, BinaryOp


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
    ],
)
def test_parser_success(expr, expected_ast):
    ast = calc.parser(calc.lexer(expr))
    assert ast == expected_ast


# некорректные выражения
@pytest.mark.parametrize(
    "expr",
    [
        "",            # пустая строка
        "2 @ 4",       # неподдерживаемый оператор
        "2 /",         # обрезанное выражение
        "1 1 + 2",     # "слипшиеся" числа
        "1 + 4i",      # комплексное число
        "abc",         # неизвестные символы
        "1..5",        # два раза точка
        "1+",          # конец на операторе
    ],
)
def test_parser_fail(expr):
    with pytest.raises(ValueError):
        calc.parser(calc.lexer(expr))