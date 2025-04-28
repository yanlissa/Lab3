import pytest
import time

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.setrecursionlimit(2000)

import calc

# нагрузочные тесты
def test_performance_long_expression():
    long_expr = "1+" * 499 + "1"  # Строка длиной ~1000 символов
    start_time = time.time()
    calc.calc(long_expr)
    elapsed = (time.time() - start_time) * 1000  # В миллисекундах
    assert elapsed < 200, f"Performance test failed: {elapsed}ms"

# нагрузочные тесты: выражения, которые должны вычисляться успешно
@pytest.mark.parametrize(
    "expr,expected_result",
    [
        ("1-" * 499 + "1", -498.0),
        ("1*" * 499 + "1", 1.0),
        ("2*" * 499 + "2", 2**500),
        ("1/" * 499 + "1", 1.0),
        ("1^" * 499 + "1", 1.0),
        ("sin(" * 100 + "0" + ")" * 100, 0.0),
        ("tg(" * 100 + "0" + ")" * 100, 0.0),
        ("sqrt(" * 100 + "1" + ")" * 100, 1.0),
        ("1+2*3-4/5+" * 99 + "1", 1 + 99 * (1 + 2 * 3 - 4/5)),
    ],
)
def test_performance_variants_success(expr, expected_result):
    start_time = time.time()
    result = calc.calc(expr)
    elapsed = (time.time() - start_time) * 1000
    assert abs(result - expected_result) < 1e-10, f"Expected {expected_result}, got {result}"
    assert elapsed < 200, f"Performance test failed for {expr}: {elapsed}ms"
    
# нагрузочные тесты: выражения, которые должны вызывать переполнение
@pytest.mark.parametrize(
    "expr",
    [
        "2^" * 10 + "1",
        "2^" * 499 + "2",
        "exp(" * 100 + "1" + ")" * 100,
    ],
)
def test_performance_variants_overflow(expr):
    start_time = time.time()
    try:
        result = calc.calc(expr)
        assert False, "Expected overflow, but got a result"
    except ValueError as e:
        elapsed = (time.time() - start_time) * 1000
        assert "Arithmetic overflow" in str(e), f"Expected 'Arithmetic overflow', got {str(e)}"
        assert elapsed < 200, f"Performance test failed for {expr}: {elapsed}ms"

# тесты из задания
def test_performance_specific_cases():
    # 1+1+... (250 раз)
    expr1 = "1+" * 249 + "1"
    start_time = time.time()
    result = calc.calc(expr1)
    elapsed = (time.time() - start_time) * 1000
    assert result == 250.0
    assert elapsed < 200, f"Performance test failed for expr1: {elapsed}ms"

    # 1+1+...+1+ (249 раз)
    expr2 = "1+" * 249
    start_time = time.time()
    try:
        calc.calc(expr2)
    except ValueError as e:
        elapsed = (time.time() - start_time) * 1000
        assert "Invalid expression" in str(e)
        assert elapsed < 200, f"Performance test failed for expr2: {elapsed}ms"

    # Большие числа
    expr3 = "1" + "0" * 100 + "+" + "1" + "0" * 100 + "+" + "1" + "0" * 100 + "+" + "1" + "0" * 100
    start_time = time.time()
    result = calc.calc(expr3)
    elapsed = (time.time() - start_time) * 1000
    assert result == 4e100
    assert elapsed < 200, f"Performance test failed for expr3: {elapsed}ms"

    # 1 ^ 36893488147419103232
    expr4 = "1 ^ 36893488147419103232"
    start_time = time.time()
    result = calc.calc(expr4)
    elapsed = (time.time() - start_time) * 1000
    assert result == 1.0
    assert elapsed < 200, f"Performance test failed for expr4: {elapsed}ms"

    # 1.000000000000001 ^ 36893488147419103232
    expr5 = "1.000000000000001 ^ 36893488147419103232"
    start_time = time.time()
    with pytest.raises(ValueError, match="Arithmetic overflow"):
        calc.calc(expr5)
    elapsed = (time.time() - start_time) * 1000
    assert elapsed < 200, f"Performance test failed for expr5: {elapsed}ms"

    # 1+1+... (1026 раз)
    expr6 = "1+" * 1025 + "1"
    start_time = time.time()
    result = calc.calc(expr6)
    elapsed = (time.time() - start_time) * 1000
    assert result == 1026.0