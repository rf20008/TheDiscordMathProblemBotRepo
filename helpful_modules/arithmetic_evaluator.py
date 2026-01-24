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
class TokenType(enum.StrEnum):
    NUMBER = "NUMBER"
    PLUS = "PLUS"
    MINUS = "MINUS"
    TIMES = "TIMES"
    DIVIDE = "DIVIDE"
    LEFT_PARENTHESIS = "LEFT_PARENTHESIS"
    RIGHT_PARENTHESIS = "RIGHT_PARENTHESIS"
    EXPONENT = "EXPONENT"
    BITWISE_AND = "BITWISE_AND"
    BITWISE_OR = "BITWISE_OR"
    MODULO = "MODULO"
    INVALID = "INVALID"
    def __str__(self):
        return self.value
    def is_operand(self):
        return self.value in ["PLUS", "MINUS", "TIMES", "DIVIDE", "EXPONENT", "BITWISE_AND", "BITWISE_OR", "MODULO"]
    def is_opera(self):
        return self.is_operand() or self.is_parenthesis()
    def is_parenthesis(self):
        return self.value in ["LEFT_PARENTHESIS", "RIGHT_PARENTHESIS"]
precedence = {
    "ADD": 1, "MINUS": 1,
    '+': 1, '-': 1,
    "TIMES": 2, "DIVIDE": 2,
    '*': 2, '/': 2,
    "BITWISE_AND": 3,
    '&': 3,
    "BITWISE_OR": 4,
    '|': 4,
    "MODULO": 5,
    '%': 5,
    "EXPONENT": 6,
    '^': 6,
    "INVALID": -1000
}

associativity = {
    "ADD": "left",
    '+': "left",
    "MINUS": "left",
    "-": "left",
    "TIMES": "left",
    "*": "left",
    "DIVIDE": "left",
    "BITWISE_AND": "left",
    "&": "left",
    "BITWISE_OR": "left",
    "|": "left",
    "MODULO": "left",
    "%": "left",
    "EXPONENT": "right",
    "^": "right"
}

@dataclasses.dataclass
class Token:
    token_type: TokenType
    token_value: str | int | float
    def is_operand(self):
        return self.token_type.is_operand()
    def is_number(self):
        return self.token_type == TokenType.NUMBER
def tokenizeregex(expression: str) -> list[Token]:
    if not isinstance(expression, str):
        raise TypeError("expression must be a string")
    tokens: list[Token] = []
    nesting_level = 0
    for potential_match in re.finditer(r'\.\d+|\d+(?:\.\d*)?|\+|-|\*|/|\(|\)|\^|&|\||\%|\$', expression):
        token_str = potential_match.group()
        token_type: TokenType = TokenType.INVALID
        if token_str.isdigit():
            if len(token_str) > 20:
                raise ValueError("Tokens must be less than 20 characters long")
            token_value = int(token_str)
            if abs(token_value) > 2**64:
                raise ValueError("Tokens must be less in absolute value than 2**64")
            token_type = TokenType.NUMBER
        elif token_str.isalpha():
            raise ValueError("Variables are not allowed!")

        elif token_str == "+":
            token_type = TokenType.PLUS
            token_value = "+"
        elif token_str == "-":
            token_type = TokenType.MINUS
            token_value = "-"
        elif token_str == "*":
            token_type = TokenType.TIMES
            token_value = "*"
        elif token_str == "/":
            token_type = TokenType.DIVIDE
            token_value = "/"
        elif token_str == "(":
            token_type = TokenType.LEFT_PARENTHESIS
            token_value = "("
            nesting_level += 1
        elif token_str == ")":
            token_type = TokenType.RIGHT_PARENTHESIS
            token_value = ")"
            nesting_level -= 1
            if nesting_level < 0:
                raise ValueError("Invalid expression: too many right parentheses")
        elif token_str == "^":
            token_type = TokenType.EXPONENT
            token_value = "^"
        elif token_str == "&":
            token_type = TokenType.BITWISE_AND
            token_value = "&"
        elif token_str == "|":
            token_type = TokenType.BITWISE_OR
            token_value = "|"
        elif token_str == "%":
            token_type = TokenType.MODULO
            token_value = "%"
        else:
            if bool(re.fullmatch(r"^\.\d+|\d+(?:\.\d*)?$", token_str)):
                if len(token_str) > 40:
                    raise ValueError("Tokens must be less than 40 characters long")
                token_value = float(token_str)
                token_type = TokenType.NUMBER
            else:
                raise ValueError(f"Invalid token: {token_str}")

        tokens.append(Token(token_type, token_value))
        if len(tokens)>=2 and tokens[-1].is_operand() and tokens[-2].is_operand():
            raise ValueError("Invalid expression: two consecutive operands")
    if nesting_level > 0:
        raise ValueError("Invalid expression: too many left parentheses")
    if nesting_level < 0:
        raise ValueError("Invalid expression: too many right parentheses")
    if len(tokens)>=1 and tokens[-1].is_operand():
        raise ValueError("Invalid expression: ending with an operand")
    if len(tokens)>=1 and tokens[0].is_operand():
        raise ValueError(f"Invalid expression: starting with an operand; {tokens}")

    return tokens

def shunting_yard(tokens: list[Token]) -> list[Token]:
    output_queue = collections.deque()
    operator_stack = []
    for token in tokens:
        if token.token_type == TokenType.NUMBER:
            output_queue.append(token.token_value)
            continue
        elif token.token_type.is_operand():
            current_operator = token.token_value
            while (
                len(operator_stack) > 0
                and operator_stack[-1] != "("
                and (precedence[operator_stack[-1]] > precedence[current_operator]
                    or (precedence[operator_stack[-1]] == precedence[current_operator]
                        and associativity[current_operator] == "left"
                    )
                )
            ):
                output_queue.append(operator_stack.pop())
            operator_stack.append(current_operator)
            continue
        elif token.token_type == TokenType.LEFT_PARENTHESIS:
            operator_stack.append(token.token_value)
            continue
        elif token.token_type == TokenType.RIGHT_PARENTHESIS:
            while len(operator_stack)>0 and operator_stack[-1] != '(':
                if len(operator_stack) == 0:
                    raise ValueError("Mismatched parenthesis")
                output_queue.append(operator_stack.pop())
            if len(operator_stack) == 0 or operator_stack[-1] != "(":
                raise ValueError("Mismatched parenthesis")
            operator_stack.pop()
    while len(operator_stack)>0:
        if operator_stack[-1] in "()":
            raise ValueError("Mismatched parenthesis")
        output_queue.append(operator_stack.pop())
    L = list(output_queue)
    for i, item in enumerate(L):
        if isinstance(item, (int, float)):
            L[i] = Token(TokenType.NUMBER, item)
        if isinstance(item, str):
            match item:
                case "+":
                    L[i] = Token(TokenType.PLUS, "+")
                case "-":
                    L[i] = Token(TokenType.MINUS, "-")
                case "*":
                    L[i] = Token(TokenType.TIMES, "*")
                case "/":
                    L[i] = Token(TokenType.DIVIDE, "/")
                case "^":
                    L[i] = Token(TokenType.EXPONENT, "^")
                case "&":
                    L[i] = Token(TokenType.BITWISE_AND, "&")
                case "|":
                    L[i] = Token(TokenType.BITWISE_OR, "|")
                case "%":
                    L[i] = Token(TokenType.MODULO, "%")
                case _:
                    raise ValueError(f"Unknown token: {item}")
    return L
def evaluate_RPN(tokens):
    #print(f"Entered EVALUATION! {tokens}")
    stack = []
    for token in tokens:
        #print(stack)
        if token.is_number():
            stack.append(token)
            continue
        else:
            if len(stack) < 2:
                raise ValueError("Not enough operands")
            if stack[-1].is_operand() or stack[-2].is_operand():
                raise ValueError("One operand is itself an operator")
            result = None
            if not stack[-1].is_number() or not stack[-2].is_number():
                raise ValueError("One operand is itself an operator")
            #print(stack)
            op_2 = stack.pop().token_value
            op_1 = stack.pop().token_value
            #print(stack)
            result = None
            #print(token.token_value)
            match token.token_value:

                case "+":
                    result = op_1+op_2
                case "-":
                    result = op_1-op_2
                case "*":
                    result = op_1*op_2
                case "/":
                    if op_2 == 0:
                        raise ZeroDivisionError("Division by 0")
                    result = op_1/op_2
                case "^":
                    if op_2*math.log(abs(op_1), 2) > 64:
                        raise ValueError("Overflow! All intermediate results must be less than 2**64")
                    result = op_1**op_2
                case "&":
                   result = op_1&op_2
                case "|":
                    result = op_1|op_2
                case "%":
                    if op_2 == 0:
                        raise ZeroDivisionError("Modulo by 0")
                    result = op_1%op_2
                case _:
                    raise ValueError(f"Unknown operand: {token.token_type}")
            if abs(result)>=2**64:
                raise ValueError(f"All results must be less in absolute value than 2**64, but your result={result}>{2**64}")
            stack.append(Token(TokenType.NUMBER, result))
    if len(stack) != 1:
        raise ValueError(f"Invalid expression: {stack}")
    return stack[0].token_value

def evaluate_expr(expression):
    return evaluate_RPN(shunting_yard(tokenizeregex(expression)))
#assert evaluate_expr("3+4")==7
expression = input("Enter an expression: ")
tokens = tokenizeregex(expression)
#print(tokens)
output_queue = shunting_yard(tokens)
#print(output_queue)
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

