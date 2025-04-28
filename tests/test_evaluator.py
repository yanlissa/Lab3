import pytest

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import calc
from calc import Number, BinaryOp


# обычные вычисления (этап 1)
@pytest.mark.parametrize(
    ("expr", "result"),
    [
        ("2+2",           4.0),
        ("10-3",          7.0),
        ("2*3/4",         1.5),
        ("-3+5*2",        7.0),
        ("1+2*3-4/5",     1 + 2*3 - 4/5),
        ("-5",           -5.0),
    ],
)
def test_calc_ok(expr, result):
    assert calc.calc(expr) == result

# новые тесты для этапа 2 (интеграционные)
@pytest.mark.parametrize(
    ("expr", "result"),
    [
        ("1.25e+09", 1250000000.0),
        ("3^4", 81.0),
        ("1 + 2 * (3 + 4)", 1 + 2 * (3 + 4)),
        ("(15e-2 * 10 ^ 2) * (1/3)", 5.0),
    ],
)
def test_calc_stage2(expr, result):
    assert calc.evaluate(calc.parser(calc.lexer(expr))) == result

# деление на ноль
def test_division_by_zero():
    with pytest.raises(ValueError, match="Division by zero"):
        calc.calc("1 / 0")


# арифметическое переполнение
def test_overflow():
    huge = BinaryOp(Number(1e308), "*", Number(10.0))
    with pytest.raises(ValueError, match="Arithmetic overflow"):
        calc.evaluate(huge)


# ветка “неизвестный оператор”
def test_unknown_operator():
    bad_ast = BinaryOp(Number(1), "@", Number(2))
    with pytest.raises(ValueError, match="Unknown operator"):
        calc.evaluate(bad_ast)