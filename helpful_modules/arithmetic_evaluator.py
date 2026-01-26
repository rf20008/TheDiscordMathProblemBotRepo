"""You can distribute any version of the Software created and distributed *before* 23:17:55.00 July 28, 2024 GMT-4
under the GNU General Public License version 3 or at your option, any  later option.
But versions of the code created and/or distributed *on or after* that date must be distributed
under the GNU *Affero* General Public License, version 3, or, at your option, any later version.

The Discord Math Problem Bot Repo - Arithmetic Evaluator

This program is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public License
as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
See the GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License along with this program.
If not, see <https://www.gnu.org/licenses/>.

Author: Samuel Guo (64931063+rf20008@users.noreply.github.com)"""

import re
import dataclasses
import enum
import collections
import math
import cmath
import sys


from .errors import (
    CalculatorError,
    ArithmeticTypeError,
    ArithmeticSyntaxError,
    ArithmeticOverflowError,
    DomainError,
    CalculatorZeroDivisionError,
)

MAX_FLOAT = sys.float_info.max
MAX_LN = math.log(MAX_FLOAT)


def as_int(x: float | complex | int) -> int:
    if not isinstance(x, (float, complex, int)):
        raise ArithmeticTypeError("x is not a float, complex, or int")
    if isinstance(x, complex):
        if x.imag != 0:
            raise ArithmeticTypeError("x is not an integer as it is nonreal")
        x = x.real
    if isinstance(x, float):
        if not x.is_integer():
            raise ArithmeticTypeError("x is not an integer")
    return int(x)


class TokenType(enum.StrEnum):
    NUMBER = "NUMBER"
    BINARY_OPERATOR = "BINARY_OPERATOR"
    UNARY_OPERATOR = "UNARY_OPERATOR"
    LEFT_PARENTHESIS = "LEFT_PARENTHESIS"
    RIGHT_PARENTHESIS = "RIGHT_PARENTHESIS"

    INVALID = "INVALID"

    def __str__(self):
        return self.value

    def is_operand(self):
        return self.value in ["BINARY_OPERATOR", "UNARY_OPERATOR"]

    def is_opera(self):
        return self.is_operand() or self.is_parenthesis()

    def is_parenthesis(self):
        return self.value in ["LEFT_PARENTHESIS", "RIGHT_PARENTHESIS"]


precedence = {
    "ADD": 1,
    "MINUS": 1,
    "+": 1,
    "-": 1,
    "TIMES": 2,
    "DIVIDE": 2,
    "*": 2,
    "/": 2,
    "BITWISE_AND": 3,
    "&": 3,
    "BITWISE_OR": 4,
    "|": 4,
    "MODULO": 5,
    "%": 5,
    "EXPONENT": 6,
    "^": 6,
    "INVALID": -1000,
}


class UnaryOperator(enum.StrEnum):
    SIN = "sin"
    COS = "cos"
    TAN = "tan"
    CSC = "csc"
    COT = "cot"
    SEC = "sec"
    EXP = "exp"
    SQRT = "sqrt"
    ABS = "abs"
    ASIN = "asin"
    ATAN = "atan"
    ACOS = "acos"
    CBRT = "cbrt"
    FLOOR = "floor"
    CEIL = "ceil"
    LN = "ln"
    NEG = "neg"
    BNOT = "not"

    def __str__(self):
        return self.value

    def __call__(self, thing: complex | float | int) -> complex | float | int:
        return self.evaluate(thing)

    def evaluate(self, thing: complex | float | int) -> complex:
        match self.value:
            case "sin":
                return cmath.sin(thing)
            case "cos":
                return cmath.cos(thing)
            case "tan":
                return cmath.tan(thing)
            case "csc":
                return 1 / cmath.sin(thing)
            case "cot":
                return 1 / cmath.tan(thing)
            case "sec":
                return 1 / cmath.cos(thing)
            case "exp":
                if abs(thing.real) > MAX_LN:
                    raise ArithmeticOverflowError(f"Exponent of {thing} is too large")
                return cmath.exp(thing)
            case "sqrt":
                return cmath.sqrt(thing)
            case "abs":
                return abs(thing)
            case "asin":
                return cmath.asin(thing)
            case "atan":
                return cmath.atan(thing)
            case "acos":
                return cmath.acos(thing)
            case "cbrt":
                return pow(thing, 1 / 3)
            case "floor":
                if thing.imag != 0:
                    raise DomainError(
                        "Floor of {thing} does not exist as it is complex"
                    )
                return complex(math.floor(thing.real))
            case "ceil":
                if thing.imag != 0:
                    raise DomainError(
                        f"Ceil of {thing} does not exist as it is complex"
                    )
                return complex(math.ceil(thing.real))
            case "ln":
                if thing == 0:
                    raise DomainError(
                        f"The natural logarithm of {thing} does not exist as it is complex"
                    )
                return cmath.log(thing)
            case "neg":
                return -thing
            case "not":
                return ~as_int(thing)
            case _:
                raise ArithmeticSyntaxError(f"Unknown operator: {self.value}")


for operator_name in UnaryOperator:
    precedence[operator_name.value] = 1001


class BinaryOperator(enum.StrEnum):
    EXPONENT = "^"
    BITWISE_AND = "&"
    BITWISE_OR = "|"
    MODULO = "%"
    PLUS = "+"
    MINUS = "-"
    TIMES = "*"
    DIVIDE = "/"

    def __call__(self, arg1: float, arg2: float) -> float:
        """Return arg1 OP arg2"""
        match self.value:
            case "^":
                if (cmath.log(arg1) * arg2).real >= 64 * math.log(2, math.e):
                    raise ArithmeticOverflowError(
                        f"{arg1} raised to the {arg2} is too large"
                    )
                return arg1**arg2
            case "&":
                return as_int(arg1) & as_int(arg2)
            case "|":
                return as_int(arg1) | as_int(arg2)
            case "%":
                if arg2 == 0:
                    raise CalculatorZeroDivisionError("Modulo by 0")
                return arg1 % arg2
            case "+":
                return arg1 + arg2
            case "-":
                return arg1 - arg2
            case "*":
                return arg1 * arg2
            case "/":
                if arg2 == 0:
                    raise CalculatorZeroDivisionError("Division by 0")
                return arg1 / arg2
            case _:
                raise ArithmeticSyntaxError(f"Unknown binary operator: {self.value}")


associativity = {
    "ADD": "left",
    "+": "left",
    "MINUS": "left",
    "-": "left",
    "TIMES": "left",
    "*": "left",
    "/": "left",
    "DIVIDE": "left",
    "BITWISE_AND": "left",
    "&": "left",
    "BITWISE_OR": "left",
    "|": "left",
    "MODULO": "left",
    "%": "left",
    "EXPONENT": "right",
    "^": "right",
}


@dataclasses.dataclass
class Token:
    token_type: TokenType
    token_value: str | int | float | BinaryOperator | UnaryOperator

    def __str__(self):
        return f"<Token token_type={self.token_type} token_value={self.token_value}>"

    def is_operand(self):
        return self.token_type.is_operand()

    def is_number(self):
        return self.token_type == TokenType.NUMBER

    def evaluate(self):
        if not self.is_number():
            raise ArithmeticTypeError("Cannot evaluate operand by itself")
        return self.token_value

    def is_parenthesis(self):
        return self.token_type in [
            TokenType.LEFT_PARENTHESIS,
            TokenType.RIGHT_PARENTHESIS,
        ]


ALL_UNARY_OPERATORS = set([op.value for op in UnaryOperator])
ALL_BINARY_OPERATORS = set(op.value for op in BinaryOperator)
ALL_OPERATORS = ALL_UNARY_OPERATORS | ALL_BINARY_OPERATORS
func_pattern = r"(?P<FUNC>\b(?:" + "|".join(list(ALL_UNARY_OPERATORS)) + r")(?=\())"
number_pattern = r"(?P<NUM>\.\d+|\d+(?:\.\d*)?)"
operator_pattern = r"(?P<OP>\+|-|\*|/|\^|\$)"
paren_pattern = r"(?P<PAREN>\(|\))"
token_pattern = rf"{func_pattern}|{number_pattern}|{operator_pattern}|{paren_pattern}"


def tokenizeregex(expression: str) -> list[Token]:
    if not isinstance(expression, str):
        raise TypeError("expression must be a string")
    tokens: list[Token] = []
    nesting_level = 0
    end_token = 0
    for potential_match in re.finditer(token_pattern, expression):
        if (
            potential_match.start() > end_token
            and expression[end_token : potential_match.start()].strip()
        ):
            PMS = potential_match.start()
            skipped_part = expression[end_token:PMS]
            raise ArithmeticSyntaxError(
                f"Token ({skipped_part}) skipped between position {end_token} and {PMS}"
            )
        end_token = potential_match.end()
        token_str = potential_match.group()
        # token_type: TokenType = TokenType.INVALID
        if potential_match.group("NUM"):
            token_type = TokenType.NUMBER
            if token_str.isdigit():
                if len(token_str) > 20:
                    raise ArithmeticSyntaxError(
                        "Tokens must be less than 20 characters long"
                    )
                token_value = int(token_str)
                if abs(token_value) > 2**64:
                    raise ArithmeticOverflowError(
                        f"The token {token_str} is too big. Integer tokens must be less in absolute value than 2**64"
                    )
            else:
                try:
                    if len(token_str) > 40:
                        raise ArithmeticSyntaxError(
                            f"The token {token_str} is too long. Tokens must be less than 40 characters long"
                        )
                    token_value = float(token_str)
                    tokens.append(Token(token_type, token_value))
                    continue
                except ValueError:
                    raise ValueError(
                        f"Invalid token at position {potential_match.start()}: {token_str}"
                    )
        elif token_str == "(":
            token_type = TokenType.LEFT_PARENTHESIS
            token_value = "("
            nesting_level += 1
        elif token_str == ")":
            token_type = TokenType.RIGHT_PARENTHESIS
            token_value = ")"
            nesting_level -= 1
            if nesting_level < 0:
                raise ArithmeticSyntaxError(
                    f"Invalid expression: too many right parentheses at position {potential_match.start()}"
                )
        elif token_str in ALL_BINARY_OPERATORS:
            token_type = TokenType.BINARY_OPERATOR
            token_value = BinaryOperator(token_str)
        elif token_str in ALL_UNARY_OPERATORS:
            token_type = TokenType.UNARY_OPERATOR
            token_value = UnaryOperator(token_str)
        else:
            raise ArithmeticSyntaxError(
                f"Unknown token at position {potential_match.start()}: {token_str}"
            )
        tokens.append(Token(token_type, token_value))
        if len(tokens) >= 2 and tokens[-1].is_operand() and tokens[-2].is_operand():
            raise ArithmeticSyntaxError("Invalid expression: two consecutive operands")
    if nesting_level > 0:
        raise ArithmeticSyntaxError("Invalid expression: too many left parentheses")
    if nesting_level < 0:
        raise ArithmeticSyntaxError("Invalid expression: too many right parentheses")
    if len(tokens) >= 1 and tokens[-1].is_operand():
        raise ArithmeticSyntaxError("Invalid expression: ending with an operator")
    if len(tokens) >= 1 and tokens[0].token_type == TokenType.BINARY_OPERATOR:
        raise ArithmeticSyntaxError(
            f"Invalid expression: starting with an binary operator"
        )
    return tokens


def shunting_yard(tokens: list[Token]) -> list[Token]:
    if not all(isinstance(token, Token) for token in tokens):
        raise TypeError("`tokens` must be a sequence of Tokens")
    output_queue = collections.deque()
    operator_stack = []
    for i, token in enumerate(tokens):
        if token.token_type == TokenType.NUMBER:
            output_queue.append(token)
            continue
        elif token.token_type == TokenType.UNARY_OPERATOR:
            operator_stack.append(token)
        elif token.token_type == TokenType.BINARY_OPERATOR:
            current_operator = token.token_value.value
            cur_op_prec = precedence[current_operator]
            while (
                len(operator_stack) > 0  # we need an operator
                and operator_stack[-1].token_type
                != TokenType.LEFT_PARENTHESIS  # that's not a left parenthesis
                and (
                    precedence[operator_stack[-1].token_value.value]
                    > cur_op_prec  # of higher preceence
                    or (
                        precedence[operator_stack[-1].token_value.value]
                        == cur_op_prec  # or left associative
                        and associativity[current_operator] == "left"
                    )
                )
            ):
                output_queue.append(operator_stack.pop())
            operator_stack.append(token)
            continue
        elif token.token_type == TokenType.LEFT_PARENTHESIS:
            operator_stack.append(token)
            continue
        elif token.token_type == TokenType.RIGHT_PARENTHESIS:
            while (
                len(operator_stack) > 0
                and operator_stack[-1].token_type != TokenType.LEFT_PARENTHESIS
            ):
                if len(operator_stack) == 0:
                    raise ArithmeticSyntaxError("Mismatched parenthesis")
                output_queue.append(operator_stack.pop())
            if not (
                len(operator_stack) > 0
                and operator_stack[-1].token_type == TokenType.LEFT_PARENTHESIS
            ):
                raise ArithmeticSyntaxError(
                    f"Mismatched parenthesis. On token#{i}, operator stack is: {operator_stack} and output queue is: {output_queue}"
                )
            operator_stack.pop()
            if (
                len(operator_stack) > 0
                and operator_stack[-1].token_type == TokenType.UNARY_OPERATOR
            ):
                output_queue.append(operator_stack.pop())
    while len(operator_stack) > 0:
        if operator_stack[-1].is_parenthesis():
            raise ArithmeticSyntaxError("Mismatched parenthesis")
        output_queue.append(operator_stack.pop())
    return list(output_queue)


def evaluate_RPN(tokens) -> complex | int | float:
    if not all(isinstance(token, Token) for token in tokens):
        raise TypeError("`tokens` must be a sequence of Tokens")
    # print(f"Entered EVALUATION! {tokens}")
    stack = []
    for token in tokens:
        # print(stack)
        if token.is_number():
            stack.append(token)
            continue
        elif token.token_type == TokenType.UNARY_OPERATOR:
            if len(stack) < 1:
                raise ArithmeticSyntaxError("Not enough operands")
            if not stack[-1].is_number():
                raise ArithmeticSyntaxError("The operand is not a number")
            assert isinstance(token.token_value, UnaryOperator)
            operand = stack.pop().token_value
            result = token.token_value(operand)
            if abs(result) >= 2**64:
                raise ArithmeticOverflowError(
                    f"All results must be less in absolute value than 2**64, but your result={result}>{2**64}"
                )
            stack.append(Token(TokenType.NUMBER, result))
        elif token.token_type == TokenType.BINARY_OPERATOR:
            if len(stack) < 2:
                raise ArithmeticSyntaxError("Not enough operands")
            if stack[-1].is_operand() or stack[-2].is_operand():
                raise ArithmeticSyntaxError("One operand is itself an operator")
            if not stack[-1].is_number() or not stack[-2].is_number():
                raise ArithmeticSyntaxError("One operand is itself an operator")
            # print(stack)
            op_2 = stack.pop().token_value
            op_1 = stack.pop().token_value
            assert isinstance(token.token_value, BinaryOperator)
            result = token.token_value(op_1, op_2)  # type: ignore
            if abs(result) >= 2**64:
                raise ArithmeticOverflowError(
                    f"All results must be less in absolute value than 2**64, but your result={result}>{2**64}"
                )
            stack.append(Token(TokenType.NUMBER, result))
    if len(stack) != 1:
        raise ArithmeticSyntaxError(
            f"Invalid expression. There must be exactly one final result when finished evaluating."
        )
    return stack[0].token_value


def evaluate_expr(expression):
    return evaluate_RPN(shunting_yard(tokenizeregex(expression)))


# assert evaluate_expr("3+4")==7
if __name__ == "__main__":
    expression = input("Enter an expression: ")
    tokens = tokenizeregex(expression)
    print("tokens", tokens)
    output_queue = shunting_yard(tokens)
    print("queue", output_queue)
    answer = evaluate_RPN(output_queue)
    print(answer)
    print(f"{tokens}\n{output_queue}\n{answer}")


##def tokenize(expression: str) -> list:
##    if not isinstance(expression, str):
##        raise TypeError("The expression must be a string")
##    tokens = []
##    nesting_level = 0
##    current_token = ""
##    for char in expression:
##        if char.isspace():
##            tokens.append(current_token)
##            current_token = ""
##        elif char in "+-*/()&^|":
##            if current_token != "":
##                tokens.append(current_token)
##                current_token = ""
##            current_token += char
##            if len(current_token)>1:
##                raise ValueError(f"Lexical error: invalid token {current_token}; operators must be one character long")
##            if current_token == "(":
##                nesting_level += 1
##            if current_token == ")":
##                nesting_level -= 1
##                if nesting_level < 0:
##                    raise ValueError("Semantic error: too many right parentheses")
##            tokens.append(current_token)
##            current_token = ""
##        elif char.isnumeric():
##            current_token += char
##    if nesting_level > 0:
##        raise ValueError("Semantic error: unclosed parentheses")
##    if current_token != "":
##        tokens.append(current_token)
##    return tokens
