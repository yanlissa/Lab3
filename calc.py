from __future__ import annotations

import argparse
import math
import sys
from dataclasses import dataclass
from typing import List, Union

# Лексер
@dataclass(slots=True)
class Token:
    type: str
    value: Union[str, float]


def lexer(expr: str) -> List[Token]:
    tokens: List[Token] = []
    i = 0
    last: str | None = None

    while i < len(expr):
        ch = expr[i]

        # пробелы
        if ch.isspace():
            i += 1
            continue

        # число (целое или десятичная дробь)
        if ch.isdigit() or ch == ".":
            num = ""
            dot_seen = False
            while i < len(expr) and (expr[i].isdigit() or expr[i] == "."):
                if expr[i] == ".":
                    if dot_seen:
                        raise ValueError("Invalid number format")
                    dot_seen = True
                num += expr[i]
                i += 1

            # Пропускаем пробелы после числа
            j = i
            while j < len(expr) and expr[j].isspace():
                j += 1

            # Проверяем, есть ли ещё одно число после пробелов
            if j < len(expr) and (expr[j].isdigit() or expr[j] == "."):
                raise ValueError("Invalid number: digits separated by space")

            tokens.append(Token("NUMBER", float(num)))
            last = "NUMBER"
            continue

        # операторы
        if ch in "+-*/":
            if ch == "-" and (last is None or last in {"OPERATOR", "UNARY_MINUS"}):
                tokens.append(Token("UNARY_MINUS", ch))
            else:
                tokens.append(Token("OPERATOR", ch))
            last = "OPERATOR"
            i += 1
            continue

        raise ValueError(f"Invalid character: {ch!r}")

    return tokens


# AST
@dataclass(slots=True, eq=True)
class Number:
    value: float


@dataclass(slots=True, eq=True)
class UnaryOp:
    op: str           # «‑»
    expr: "Expr"


@dataclass(slots=True, eq=True)
class BinaryOp:
    left: "Expr"
    op: str           # + - * /
    right: "Expr"


Expr = Union[Number, UnaryOp, BinaryOp]

# Парсер
def parser(tokens: List[Token]) -> Expr:
    """Возвращает AST либо бросает ValueError."""

    def parse_expression(pos: int, min_prec: int = 0) -> tuple[Expr, int]:
        node, pos = parse_atom(pos)

        while pos < len(tokens) and tokens[pos].type == "OPERATOR":
            op = tokens[pos].value
            prec = {"+": 1, "-": 1, "*": 2, "/": 2}[op]
            if prec < min_prec:
                break
            pos += 1
            rhs, pos = parse_expression(pos, prec + 1)
            node = BinaryOp(node, op, rhs)

        return node, pos

    def parse_atom(pos: int) -> tuple[Expr, int]:
        if pos >= len(tokens):
            raise ValueError("Unexpected end of expression") # пустая строка или незаконченное выражение

        tok = tokens[pos]

        if tok.type == "NUMBER":
            return Number(tok.value), pos + 1

        if tok.type == "UNARY_MINUS":
            expr, next_pos = parse_atom(pos + 1)
            return UnaryOp("-", expr), next_pos

        raise ValueError(f"Unexpected token: {tok.type}") # токен, который парсер не ожидает

    ast, idx = parse_expression(0)
    if idx != len(tokens):
        raise ValueError("Invalid expression")
    return ast


# Вычисления
def _check(val: float) -> float:
    if math.isinf(val) or math.isnan(val):
        raise ValueError("Arithmetic overflow") # подготовка к этапу 3
    return val


def evaluate(ast: Expr) -> float:
    if isinstance(ast, Number):
        return ast.value

    if isinstance(ast, UnaryOp):
        res = -evaluate(ast.expr)
        return _check(res)

    if isinstance(ast, BinaryOp):
        left = evaluate(ast.left)
        right = evaluate(ast.right)

        if ast.op == "+":
            res = left + right
        elif ast.op == "-":
            res = left - right
        elif ast.op == "*":
            res = left * right
        elif ast.op == "/":
            if right == 0:
                raise ValueError("Division by zero")
            res = left / right
        else:
            raise ValueError(f"Unknown operator {ast.op}") # передан неизвестный оператор

        return _check(res)

    raise TypeError("Unknown AST node") # передан объект, не являющийся Number, UnaryOp или BinaryOp


def calc(expr: str) -> float:
    return evaluate(parser(lexer(expr)))


#CLI
def _cli() -> int:      # pragma: no cover
    p = argparse.ArgumentParser(description="Stage‑1 CLI calculator")
    p.add_argument("expression", help='Напр.: "1 + 2*3 - 4/5"')
    args = p.parse_args()

    try:
        print(calc(args.expression))
        return 0
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":     # pragma: no cover
    sys.exit(_cli())