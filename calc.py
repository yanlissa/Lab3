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

        # число (целое, дробное или научная нотация)
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
                
            # Проверяем научную нотацию (например, 1e-3)
            if i < len(expr) and expr[i].lower() == "e":
                num += expr[i]
                i += 1
                if i < len(expr) and expr[i] in "+-":
                    num += expr[i]
                    i += 1
                if i >= len(expr) or not expr[i].isdigit():
                    raise ValueError("Invalid number format")
                while i < len(expr) and expr[i].isdigit():
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
        
        # функции и константы
        if ch.isalpha():
            name = ""
            while i < len(expr) and expr[i].isalpha():
                name += expr[i]
                i += 1
            functions = {"sqrt", "sin", "cos", "tg", "ctg", "ln", "exp"}
            constants = {"pi": math.pi, "e": math.e}
            if name in functions:
                tokens.append(Token("FUNCTION", name))
                last = "FUNCTION"
            elif name in constants:
                tokens.append(Token("NUMBER", constants[name]))
                last = "NUMBER"
            else:
                raise ValueError(f"Unknown function or constant: {name}")
            continue
        
        # операторы
        if ch in "+-*/^":
            if ch == "-" and (last is None or last in {"OPERATOR", "UNARY_MINUS", "("}):
                tokens.append(Token("UNARY_MINUS", ch))
            else:
                tokens.append(Token("OPERATOR", ch))
            last = "OPERATOR"
            i += 1
            continue
        
        # скобки
        if ch in "()":
            tokens.append(Token(ch, ch))
            last = ch
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
    op: str           # + - * / ^
    right: "Expr"

@dataclass(slots=True, eq=True)
class Function:
    name: str
    arg: "Expr"

Expr = Union[Number, UnaryOp, BinaryOp, Function]

# Парсер
def parser(tokens: List[Token]) -> Expr:
    """Возвращает AST либо бросает ValueError."""

    def parse_expression(pos: int, min_prec: int = 0) -> tuple[Expr, int]:
        node, pos = parse_atom(pos)

        while pos < len(tokens) and tokens[pos].type == "OPERATOR":
            op = tokens[pos].value
            prec = {"+": 1, "-": 1, "*": 2, "/": 2, "^": 3}[op]
            if prec < min_prec:
                break
            pos += 1
            if pos >= len(tokens):
                raise ValueError("Invalid expression")
            rhs, pos = parse_expression(pos, prec + 1)
            node = BinaryOp(node, op, rhs)

        return node, pos

    def parse_atom(pos: int) -> tuple[Expr, int]:
        if pos >= len(tokens):
            if any(token.type == "(" for token in tokens[:pos]):
                raise ValueError("Mismatched parentheses")
            raise ValueError("Unexpected end of expression") # пустая строка или незаконченное выражение

        tok = tokens[pos]

        if tok.type == "NUMBER":
            return Number(tok.value), pos + 1
        
        if tok.type == "FUNCTION":
            func_name = tok.value
            if pos + 1 >= len(tokens) or tokens[pos + 1].type != "(":
                raise ValueError(f"Expected '(' after function {func_name}")
            arg, next_pos = parse_expression(pos + 2)
            if next_pos >= len(tokens) or tokens[next_pos].type != ")":
                raise ValueError("Mismatched parentheses")
            return Function(func_name, arg), next_pos + 1

        if tok.type == "UNARY_MINUS":
            expr, next_pos = parse_atom(pos + 1)
            return UnaryOp("-", expr), next_pos
        
        if tok.type == "(":
            expr, next_pos = parse_expression(pos + 1)
            if next_pos >= len(tokens) or tokens[next_pos].type != ")":
                raise ValueError("Mismatched parentheses")
            return expr, next_pos + 1

        raise ValueError(f"Unexpected token: {tok.type}") # токен, который парсер не ожидает

    ast, idx = parse_expression(0)
    if idx != len(tokens):
        raise ValueError("Invalid expression")
    return ast


# Вычисления
def _check(val: float) -> float:
    if math.isinf(val) or math.isnan(val):
        raise ValueError("Arithmetic overflow") # переполнение
    return val


def evaluate(ast: Expr, angle_unit: str = "radian") -> float:
    if isinstance(ast, Number):
        return ast.value

    if isinstance(ast, UnaryOp):
        res = -evaluate(ast.expr, angle_unit)
        return _check(res)

    if isinstance(ast, BinaryOp):
        left = evaluate(ast.left, angle_unit)
        right = evaluate(ast.right, angle_unit)

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
        elif ast.op == "^":
            res = left ** right
        else:
            raise ValueError(f"Unknown operator {ast.op}") # передан неизвестный оператор

        return _check(res)

    if isinstance(ast, Function):
        arg = evaluate(ast.arg, angle_unit)
        if ast.name == "sqrt":
            if arg < 0:
                raise ValueError("Square root of negative number")
            return math.sqrt(arg)
        elif ast.name == "sin":
            return math.sin(math.radians(arg) if angle_unit == "degree" else arg)
        elif ast.name == "cos":
            return math.cos(math.radians(arg) if angle_unit == "degree" else arg)
        elif ast.name == "tg":
            return math.tan(math.radians(arg) if angle_unit == "degree" else arg)
        elif ast.name == "ctg":
            tan_val = math.tan(math.radians(arg) if angle_unit == "degree" else arg)
            if tan_val == 0:
                raise ValueError("Cotangent undefined")
            return 1 / tan_val
        elif ast.name == "ln":
            if arg <= 0:
                raise ValueError("Logarithm of non-positive number")
            return math.log(arg)
        elif ast.name == "exp":
            return math.exp(arg)
        else:
            raise ValueError(f"Unknown function: {ast.name}")
    
    raise TypeError("Unknown AST node") # передан объект, не являющийся Number, UnaryOp или BinaryOp


def calc(expr: str, angle_unit: str = "radian") -> float:
    return evaluate(parser(lexer(expr)), angle_unit)


#CLI
def _cli() -> int:      # pragma: no cover
    p = argparse.ArgumentParser(description="Stage‑3 CLI calculator")
    p.add_argument("expression", help='Examples: calc.py \"sin(pi/2)\"')
    p.add_argument(
        "--angle-unit",
        choices=["radian", "degree"],
        default="radian",
        help="Unit for trigonometric functions (default: radian)"
    )
    args = p.parse_args()

    try:
        result = calc(args.expression, args.angle_unit)
        print(f"{result:.5f}")
        return 0
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":     # pragma: no cover
    sys.exit(_cli())