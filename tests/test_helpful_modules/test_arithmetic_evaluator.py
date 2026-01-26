"""
This code is inspired by ChatGPT!
Copyright © 2025-present Samuel Guo
You can distribute any version of the Software created and distributed *before* 23:17:55.00 July 28, 2024 GMT-4
under the GNU General Public License version 3 or at your option, any  later option.
But versions of the code created and/or distributed *on or after* that date must be distributed
under the GNU *Affero* General Public License, version 3, or, at your option, any later version.

The Discord Math Problem Bot Repo - ConstantsLoader

This program is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public License
as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
See the GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License along with this program.
If not, see <https://www.gnu.org/licenses/>.

Author: Samuel Guo (64931063+rf20008@users.noreply.github.com)"""
import cmath
import math
import unittest
import sys
import unittest.mock

from helpful_modules import arithmetic_evaluator
from helpful_modules.arithmetic_evaluator import (
    as_int, Token, TokenType, BinaryOperator, UnaryOperator, tokenizeregex, ALL_BINARY_OPERATORS, ALL_UNARY_OPERATORS, ALL_OPERATORS, shunting_yard, evaluate_RPN, evaluate_expr
)
from helpful_modules.errors import (
    CalculatorError,
    CalculatorZeroDivisionError,
    ArithmeticTypeError,
    ArithmeticSyntaxError,
    DomainError,
    ArithmeticOverflowError,
)
class TestTokenType(unittest.TestCase):
    def test_as_int_1(self):
        for op, exp_val in [
            (1, 1),
            (1.0, 1),
            (2, 2),
            (complex(2), 2)
        ]:
            self.assertEqual(as_int(op), exp_val)
    def test_as_int_fails(self):
        for op in [-2.3, 2.3, 1.7, 1+2j, 1-2j, 1.2+2j, 1.2+3.4j, "hehe boi"]:
            with self.subTest(op=op):
                with self.assertRaises(ArithmeticSyntaxError):
                    as_int(op)
    def test_unary_operator_token(self):
        for operand_type in (TokenType.BINARY_OPERATOR, TokenType.UNARY_OPERATOR):
            self.assertTrue(operand_type.is_operand())
            self.assertTrue(operand_type.is_opera())
            self.assertFalse(operand_type.is_parenthesis())
    def test_numeric_token(self):
        T = TokenType.NUMBER
        self.assertFalse(T.is_operand())
        self.assertFalse(T.is_opera())
        self.assertFalse(T.is_parenthesis())
    def test_parenthesis_token(self):
        for operand_type in (TokenType.LEFT_PARENTHESIS, TokenType.RIGHT_PARENTHESIS):
            self.assertFalse(operand_type.is_operand())
            self.assertTrue(operand_type.is_opera())
            self.assertTrue(operand_type.is_parenthesis())
    def test_invalid_token(self):
        self.assertFalse(TokenType.INVALID.is_operand())
        self.assertFalse(TokenType.INVALID.is_opera())
        self.assertFalse(TokenType.INVALID.is_parenthesis())


class TestUnaryOperator(unittest.TestCase):
    def test_unary_operator_str(self):
        for operator in UnaryOperator:
            #print(operator)
            self.assertEqual(operator.value, str(operator))
    def test_unary_operator_evaluate(self):
        expected_values = [
            ('sin', 1, cmath.sin(1)),
            ('cos', 0, cmath.cos(0)),
            ('tan', -3.1, cmath.tan(-3.1)),
            ('csc', 1+1j, 1/cmath.sin(1+1j)),
            ('cot', -1, 1/cmath.tan(-1)),
            ('sec', 3, 1/cmath.cos(3)),
            ('exp', 9, cmath.exp(9)),
            ('sqrt', 1, cmath.sqrt(1)),
            ('abs', 1, 1),
            ('abs', 3+4j, 5),
            ('abs', -3, 3),
            ('asin', -.1, cmath.asin(-.1)),
            ('acos', 1, cmath.acos(1)),
            ('atan', 1.7, cmath.atan(1.7)),
            ('floor', 1.7, 1),
            ('floor', 1.3, 1),
            ('floor', -1.3, -2),
            ('floor', -1.7, -2),
            ('floor', 1, 1),
            ('floor', 2, 2),
            ('floor', -3.14159, -4),
            ('floor', 3+0j, 3),
            ('floor', -3+0j, -3),
            ('floor', complex(1), 1),
            ('ceil', 1.7, 2),
            ('ceil', 1.3, 2),
            ('ceil', -1.3, -1),
            ('ceil', 1, 1),
            ('ceil', 2, 2),
            ('ceil', -3.14159, -3),
            ('ceil', 3+0j, 3),
            ('ceil', -3+0j, -3),
            ('ceil', -1.7, -1),
            ('ceil', complex(1), 1),
            ('ln', 1, 0),
            ('neg', 1, -1),
            ('neg', 3+4j, -3-4j),
            ('not', 1, ~1)
        ]
        for operand_name, operand, expected_result in expected_values:
            with self.subTest(operand_name=operand_name):
                operator = UnaryOperator(operand_name)
                self.assertEqual(operator.value, operand_name)
                self.assertEqual(operator.evaluate(operand), expected_result)
    def test_exp_fail_too_big_1(self):
        with self.assertRaises(ArithmeticOverflowError):
            UnaryOperator.EXP.evaluate(303030)
    def test_exp_fail_too_small_1(self):
        with self.assertRaises(ArithmeticOverflowError):
            UnaryOperator.EXP.evaluate(-303030)
    def test_exp_fail_too_small_2(self):
        with self.assertRaises(ArithmeticOverflowError):
            UnaryOperator.EXP.evaluate(-303030+3j)
    def test_exp_fail_too_big_2(self):
        with self.assertRaises(ArithmeticOverflowError):
            UnaryOperator.EXP.evaluate(303030-3j)
    def test_exp_not_fail_for_limit(self):
        UnaryOperator.EXP.evaluate(math.log(sys.float_info.max))
    def test_floor_fails(self):
        for operand_to_fail in [-3j, 1+2j, 1-2j, 1j, -2j]:
            with self.subTest(operand_to_fail=operand_to_fail):
                with self.assertRaises(DomainError):
                    UnaryOperator.FLOOR.evaluate(operand_to_fail)
    def test_ceil_fails(self):
        for operand_to_fail in [-3j, 1+2j, 1-2j, 1j, -2j]:
            with self.subTest(operand_to_fail=operand_to_fail):
                with self.assertRaises(DomainError):
                    UnaryOperator.CEIL.evaluate(operand_to_fail)
    def test_ln_fails_at_0(self):
        with self.assertRaises(DomainError):
            UnaryOperator.LN.evaluate(0)
    def test_not_for_ints(self):
        for i in range(-16, 16):
            with self.subTest(num=i):
                self.assertEqual(UnaryOperator.BNOT.evaluate(i), ~i)
                self.assertEqual(UnaryOperator.BNOT.evaluate(i + 0.0), ~i)
                self.assertEqual(UnaryOperator.BNOT.evaluate(complex(i)), ~i)
    def test_not_fails_for_floats(self):
        for i in range(-16, 16):
            with self.subTest(num=i):
                with self.assertRaises(DomainError):
                    UnaryOperator.BNOT.evaluate(i+0.5)
    def test_not_fails_for_complex_floats(self):
        for a in range(-4, 4):
            for b in [-1, 1]:
                z = a+b*1j
                with self.subTest(z=z):
                    with self.assertRaises(ArithmeticTypeError):
                        UnaryOperator.BNOT.evaluate(z)
class TestBinaryOperators(unittest.TestCase):
    def test_basic_operands(self):
        for operator_name, operand1, operand2, expected_result in [
            ('^', 2, 3, 8),
            ('^', -1, 3, -1),
            ('&', 1, 2, 1&2),
            ('&', -1, -2, (-1)&(-2)),
            ('|', 1, 2, 1|2),
            ('|', 0, 9, 9),
            ('%', 3, 3, 0),
            ('%', 3, 4, 3),
            ('%', 3, 2, 1),
            ('+', 3, 4, 7),
            ('-', 3, 4, -1),
            ('*', 3, 4, 12),
            ('*', 2, 120, 240),
            ('/', 120, 2, 60),
            ('/', 0, 2, 0)
        ]:
            with self.subTest(operator_name=operator_name, operand1=operand1, operand2=operand2, expected_result=expected_result):
                operator = BinaryOperator(operator_name)
                computed_val = operator(operand1, operand2)
                self.assertEqual(
                    computed_val,
                    expected_result,
                    msg=f'I expected {operand1}{operator_name}{operand2} to be {expected_result} but got {computed_val}')
    def test_exponential_overflow(self):
        for operand1, operand2 in (
            (2, 65),
            (1.001, 3000000),
            (-2, 65),
            (-2, 66),
            (1+1j, 130)
        ):
          with self.subTest(operand1=operand1, operand2=operand2):
              with self.assertRaises(ArithmeticOverflowError, msg=f"{operand1}**{operand2}"):
                BinaryOperator.EXPONENT(operand1, operand2)
    def test_and_and_or(self):
        for operator_name, operand1, operand2, expected_result in [
            ('|', 1, 2, 3),
            ('&', 1, 2, 0)
        ]:
            with unittest.mock.patch('helpful_modules.arithmetic_evaluator.as_int', side_effect=int) as mock_int:
                operator = BinaryOperator(operator_name)
                computed_val = operator(operand1, operand2)
                self.assertEqual(computed_val, expected_result)
                calls = [unittest.mock.call(1), unittest.mock.call(2)]
                mock_int.assert_has_calls(calls)
                self.assertEqual(mock_int.call_count, 2)
    def test_modulo_by_0(self):
        with self.assertRaises(ZeroDivisionError):
            BinaryOperator.MODULO(3, 0)
    def test_division_by_0(self):
        with self.assertRaises(ZeroDivisionError):
            BinaryOperator.DIVIDE(3, 0)


class TestToken(unittest.TestCase):
    def test_init(self):
        T = Token(TokenType.NUMBER, 42)
        self.assertEqual(T.token_type, TokenType.NUMBER)
        self.assertEqual(T.token_value, 42)
    def test_str(self):
        T = Token(TokenType.NUMBER, 42)
        self.assertEqual(str(T), "<Token token_type=NUMBER token_value=42>")
    def test_operand(self):
        for token, should_be_operand in [
            (Token(TokenType.NUMBER, 42), False),
            (Token(TokenType.UNARY_OPERATOR, UnaryOperator.SIN), True),
            (Token(TokenType.BINARY_OPERATOR, BinaryOperator.PLUS), True),
            (Token(TokenType.LEFT_PARENTHESIS, "("), False),
            (Token(TokenType.RIGHT_PARENTHESIS, ")"), False),
            (Token(TokenType.INVALID, "HEHE BOI"), False)
        ]:
            with self.subTest(token=token, should_be_operand=should_be_operand):
                self.assertEqual(token.is_operand(), should_be_operand)
    def test_number(self):
        for token, should_be_operand in [
            (Token(TokenType.NUMBER, 32), True),
            (Token(TokenType.UNARY_OPERATOR, UnaryOperator.COS), False),
            (Token(TokenType.BINARY_OPERATOR, BinaryOperator.MINUS), False),
            (Token(TokenType.LEFT_PARENTHESIS, "("), False),
            (Token(TokenType.RIGHT_PARENTHESIS, ")"), False),
            (Token(TokenType.INVALID, [34,23]), False)
        ]:
            with self.subTest(token=token, should_be_operand=should_be_operand):
                self.assertEqual(token.is_number(), should_be_operand, msg=f"{token.is_operand()} is not {should_be_operand} as token is {token}")
    def test_evaluate(self):
        self.assertEqual(Token(TokenType.NUMBER, 42).evaluate(), 42)
    def test_evaluate_invalid(self):
        for token_failing in [
            Token(TokenType.UNARY_OPERATOR, UnaryOperator.COS),
            Token(TokenType.BINARY_OPERATOR, BinaryOperator.TIMES),
            Token(TokenType.LEFT_PARENTHESIS, "("),
            Token(TokenType.RIGHT_PARENTHESIS, ")"),
            Token(TokenType.INVALID, [34, 23]),
        ]:
            with self.subTest(token_failing=token_failing):
                with self.assertRaises(ValueError):
                    token_failing.evaluate()
    def test_is_parenthesis(self):
        for token, should_be_operand in [
            (Token(TokenType.NUMBER, 32), False),
            (Token(TokenType.UNARY_OPERATOR, UnaryOperator.COS), False),
            (Token(TokenType.BINARY_OPERATOR, BinaryOperator.MINUS), False),
            (Token(TokenType.LEFT_PARENTHESIS, "("), True),
            (Token(TokenType.RIGHT_PARENTHESIS, ")"), True),
            (Token(TokenType.INVALID, [34, 23]), False)
        ]:
            with self.subTest(token=token, should_be_operand=should_be_operand):
                self.assertEqual(token.is_parenthesis(), should_be_operand, msg=f"{token.is_parenthesis()} is not {should_be_operand} as token is {token}")
class TestTokenizer(unittest.TestCase):
    def test_tokenize_unaries(self):
        for unaryOp in UnaryOperator:
            with self.subTest(unaryOp=unaryOp):
                self.assertEqual(
                    tokenizeregex(unaryOp.value + "()"),
                    [
                        Token(TokenType.UNARY_OPERATOR, unaryOp),
                        Token(TokenType.LEFT_PARENTHESIS, "("),
                        Token(TokenType.RIGHT_PARENTHESIS, ")")
                    ]
                )
        # ---------- Type checking ----------

    def test_non_string_input_raises(self):
        for bad in [123, None, [], {}, 1.2]:
            with self.subTest(bad=bad):
                with self.assertRaises(TypeError):
                    tokenizeregex(bad)

        # ---------- Integer tokens ----------

    def test_simple_integer(self):
        tokens = tokenizeregex("123")
        self.assertEqual(tokens[0].token_type, TokenType.NUMBER)
        self.assertEqual(tokens[0].token_value, 123)

    def test_integer_too_long(self):
        expr = "1" * 21
        with self.assertRaises(ArithmeticSyntaxError):
            tokenizeregex(expr)

    def test_integer_too_large(self):
        expr = str(2 ** 64 + 1)
        with self.assertRaises(ArithmeticOverflowError):
            tokenizeregex(expr)

        # ---------- Float tokens ----------

    def test_simple_float(self):
        tokens = tokenizeregex("3.14")
        self.assertEqual(tokens[0].token_type, TokenType.NUMBER)
        self.assertEqual(tokens[0].token_value, 3.14)

    def test_float_too_long(self):
        expr = "1." + "0" * 40
        with self.assertRaises(ArithmeticSyntaxError):
            tokenizeregex(expr)

    def test_invalid_float(self):
        self.assertEqual(tokenizeregex("1.2.3"), [Token(TokenType.NUMBER, 1.2), Token(TokenType.NUMBER, 0.3)])

        # ---------- Parentheses ----------

    def test_balanced_parentheses(self):
        tokens = tokenizeregex("(1+2)")
        self.assertEqual(tokens[0].token_type, TokenType.LEFT_PARENTHESIS)
        self.assertEqual(tokens[4].token_type, TokenType.RIGHT_PARENTHESIS)

    def test_too_many_right_parentheses(self):
        with self.assertRaises(ArithmeticSyntaxError):
            tokenizeregex(")1+2")

    def test_too_many_left_parentheses(self):
        with self.assertRaises(ArithmeticSyntaxError):
            tokenizeregex("(1+2")

        # ---------- Binary operators ----------

    def test_all_binary_operators(self):
        for op in ALL_BINARY_OPERATORS:
            with self.subTest(op=op):
                tokens = tokenizeregex(f"1{op}2")
                self.assertEqual(tokens[1].token_type, TokenType.BINARY_OPERATOR)
                self.assertIsInstance(tokens[1].token_value, BinaryOperator)

        # ---------- Unary operators ----------

    def test_all_unary_operators(self):
        for op in ALL_UNARY_OPERATORS:
            with self.subTest(op=op):
                tokens = tokenizeregex(f"{op}1")
                self.assertEqual(tokens[0].token_type, TokenType.UNARY_OPERATOR)
                self.assertIsInstance(tokens[0].token_value, UnaryOperator)

        # ---------- Invalid tokens ----------

    def test_variables_not_allowed(self):
        for expr in ["x", "abc", "a+1"]:
            with self.subTest(expr=expr):
                with self.assertRaises(ArithmeticSyntaxError):
                    tokenizeregex(expr)

    def test_unknown_symbol(self):
        for expr in ["@", "$", "#"]:
            with self.subTest(expr=expr):
                with self.assertRaises(ArithmeticSyntaxError):
                    tokenizeregex(expr)

        # ---------- Sequence validation ----------

    def test_consecutive_operands(self):
        self.assertEqual(tokenizeregex("1 2"), [Token(TokenType.NUMBER, 1), Token(TokenType.NUMBER, 2)])

    def test_ending_with_operand(self):
        with self.assertRaises(ArithmeticSyntaxError):
            tokenizeregex("1+2+")

    def test_starting_with_binary_operator(self):
        for op in ALL_BINARY_OPERATORS:
            with self.subTest(op=op):
                with self.assertRaises(ValueError):
                    tokenizeregex(f"{op}1")

        # ---------- Valid expressions ----------

    def test_simple_expression(self):
        tokens = tokenizeregex("1+2")
        self.assertEqual(len(tokens), 3)

    def test_nested_expression(self):
        tokens = tokenizeregex("((1+2)*3)")
        self.assertTrue(all(isinstance(t, Token) for t in tokens))

    def test_complex_expression(self):
        tokens = tokenizeregex("(1+(2*3))*4")
        self.assertEqual(tokens[0].token_type, TokenType.LEFT_PARENTHESIS)
        self.assertEqual(tokens[-2].token_type, TokenType.BINARY_OPERATOR)
    def test_single_number_in_parens(self):
        tokenizeregex("(1)")

    def test_nested_parentheses(self):
        tokenizeregex("(((1)))")

    def test_simple_binary_expression(self):
        tokenizeregex("(1+2)")

    def test_multiple_binary_ops(self):
        tokenizeregex("((1+2)*(3-4))")

    def test_unary_inside_binary(self):
        tokenizeregex("(1+(-2))")

    def test_unary_chain(self):
        tokenizeregex("(-(-1))")

    def test_complex_mixed_expression(self):
        tokenizeregex("((1+2)*(3+(-4)))")
    def test_token_sequence_types(self):
        tokens = tokenizeregex("((1+2)*3)")
        types = [t.token_type for t in tokens]
        self.assertEqual(
            types,
            [
                TokenType.LEFT_PARENTHESIS,
                TokenType.LEFT_PARENTHESIS,
                TokenType.NUMBER,
                TokenType.BINARY_OPERATOR,
                TokenType.NUMBER,
                TokenType.RIGHT_PARENTHESIS,
                TokenType.BINARY_OPERATOR,
                TokenType.NUMBER,
                TokenType.RIGHT_PARENTHESIS,
            ]
        )

    def test_number_followed_by_left_paren(self):
        tokenizeregex("(1(2))")

    def test_right_paren_followed_by_number(self):
        tokenizeregex("((1)2)")
    def test_max_int_boundary(self):
        tokenizeregex(f"({2 ** 64 - 1})")

    def test_zero(self):
        tokenizeregex("(0)")

    def test_negative_zero(self):
        tokenizeregex("(-0)")

    def test_float_precision(self):
        tokenizeregex("(0.0000000001)")
    def test_single_letter_variable(self):
        with self.assertRaises(ArithmeticSyntaxError) as exc:
            print(tokenizeregex("(x)"))
        print(exc)
    def test_variable_with_numbers(self):
        with self.assertRaises(ArithmeticSyntaxError) as exc:
            tokenizeregex("(x1)")

    def test_mixed_alpha_numeric(self):
        with self.assertRaises(ArithmeticSyntaxError) as exc:
            tokenizeregex("(1+a)")

    def test_unknown_characters(self):
        for ch in ["@", "#", "$", "!", "?"]:
            with self.subTest(ch=ch):
                with self.assertRaises(ArithmeticSyntaxError):
                    tokenizeregex(f"({ch})")

    def test_tokenize_positive(self):
        for i in range(32):
            self.assertEqual(tokenizeregex(str(i)), [Token(TokenType.NUMBER, i)])
    def test_tokenize_negative(self):
        with self.assertRaises(ArithmeticSyntaxError):
            tokenizeregex("-321")

    def test_tokenize_small_expression(self):
        TOKENS = arithmetic_evaluator.tokenizeregex("3+4")
        self.assertEqual(len(TOKENS), 3)
        self.assertEqual(TOKENS[0], Token(TokenType.NUMBER, 3))
        self.assertEqual(TOKENS[1], Token(TokenType.BINARY_OPERATOR, BinaryOperator.PLUS))
        self.assertEqual(TOKENS[2], Token(TokenType.NUMBER, 4))


class TestShuntingYard(unittest.TestCase):

    def assertRPN(self, tokens, expected_values):
        """Helper to compare token values in RPN output"""
        output = shunting_yard(tokens)
        result = [t.token_value if t.token_type != TokenType.NUMBER else t.token_value for t in output]
        self.assertEqual(result, expected_values)

    # ------------------------------
    # Simple number
    # ------------------------------
    def test_single_number(self):
        tokens = tokenizeregex("42")
        self.assertRPN(tokens, [42])

    # ------------------------------
    # Simple binary operations
    # ------------------------------
    def test_simple_add(self):
        tokens = tokenizeregex("1+2")
        self.assertRPN(tokens, [1, 2, '+'])

    def test_simple_subtract(self):
        tokens = tokenizeregex("5-3")
        self.assertRPN(tokens, [5, 3, '-'])

    def test_simple_multiply(self):
        tokens = tokenizeregex("2*4")
        self.assertRPN(tokens, [2, 4, '*'])

    def test_simple_divide(self):
        tokens = tokenizeregex("8/2")
        self.assertRPN(tokens, [8, 2, '/'])

    # ------------------------------
    # Operator precedence
    # ------------------------------
    def test_precedence_mixed(self):
        tokens = tokenizeregex("1+2*3")
        # '*' has higher precedence than '+'
        self.assertRPN(tokens, [1, 2, 3, '*', '+'])

    def test_precedence_with_parens(self):
        tokens = tokenizeregex("(1+2)*3")
        # parentheses force addition first
        self.assertRPN(tokens, [1, 2, '+', 3, '*'])

    # ------------------------------
    # Multiple operators same precedence
    # ------------------------------
    def test_left_associativity(self):
        tokens = tokenizeregex("5-3-1")
        # left-associative: (5-3)-1
        self.assertRPN(tokens, [5, 3, '-', 1, '-'])

    def test_mixed_same_precedence(self):
        tokens = tokenizeregex("4+2-1")
        # left-associative: ((4+2)-1)
        self.assertRPN(tokens, [4, 2, '+', 1, '-'])

    # ------------------------------
    # Nested parentheses
    # ------------------------------
    def test_nested_parentheses(self):
        tokens = tokenizeregex("((1+2)*(3-4))")
        print(tokens)
        self.assertRPN(tokens, [1, 2, '+', 3, 4, '-', '*'])

    def test_deeply_nested(self):
        tokens = tokenizeregex("(((1+2)+3)*((4-5)/6))")

        self.assertRPN(tokens, [1, 2, '+', 3, '+', 4, 5, '-', 6, '/', '*'])

    # ------------------------------
    # Mismatched parentheses
    # ------------------------------
    def test_extra_left_paren(self):

        with self.assertRaises(ArithmeticSyntaxError):
            tokens = tokenizeregex("((1+2)")
            shunting_yard(tokens)

    def test_extra_right_paren(self):

        with self.assertRaises(ArithmeticSyntaxError):
            tokens = tokenizeregex("(1+2))")
            shunting_yard(tokens)

    # ------------------------------
    # Single number in parentheses
    # ------------------------------
    def test_number_in_parens(self):
        tokens = tokenizeregex("(42)")
        self.assertRPN(tokens, [42])

    # ------------------------------
    # Multiple same-precedence operators
    # ------------------------------
    def test_multiplication_and_division(self):
        tokens = tokenizeregex("8*2/4")
        # left-associative: ((8*2)/4)
        self.assertRPN(tokens, [8, 2, '*', 4, '/'])

    def test_addition_and_subtraction(self):
        tokens = tokenizeregex("7+3-2")
        # left-associative: ((7+3)-2)
        self.assertRPN(tokens, [7, 3, '+', 2, '-'])

class TestEvaluateRPN(unittest.TestCase):

    def evalRPN_helper(self, expression, expected):
        tokens = shunting_yard(tokenizeregex(expression))
        result = evaluate_RPN(tokens)
        self.assertEqual(result, expected)

    # ------------------------------
    # Simple numbers
    # ------------------------------
    def test_single_number(self):
        self.evalRPN_helper("42", 42)

    # ------------------------------
    # Simple binary operations
    # ------------------------------
    def test_addition(self):
        self.evalRPN_helper("1+2", 3)

    def test_subtraction(self):
        self.evalRPN_helper("5-3", 2)

    def test_multiplication(self):
        self.evalRPN_helper("2*3", 6)

    def test_division(self):
        self.evalRPN_helper("8/2", 4)

    # ------------------------------
    # Mixed operations with precedence
    # ------------------------------
    def test_mixed_precedence(self):
        self.evalRPN_helper("1+2*3", 7)

    def test_parentheses_precedence(self):
        self.evalRPN_helper("(1+2)*3", 9)

    # ------------------------------
    # Multiple same-precedence operators
    # ------------------------------
    def test_left_associativity(self):
        self.evalRPN_helper("5-3-1", 1)

    def test_multiple_multiplication_division(self):
        self.evalRPN_helper("8*2/4", 4)

    # ------------------------------
    # Overflow check
    # ------------------------------
    def test_overflow_1(self):
        big = 2**63
        tokens = [Token(TokenType.NUMBER, big), Token(TokenType.NUMBER, 2),
                  Token(TokenType.BINARY_OPERATOR, BinaryOperator("*"))]
        with self.assertRaises(ArithmeticOverflowError):
            evaluate_RPN(tokens)

    # ------------------------------
    # Not enough operands
    # ------------------------------
    def test_not_enough_operands(self):
        tokens = [Token(TokenType.BINARY_OPERATOR, BinaryOperator("+"))]
        with self.assertRaises(ArithmeticSyntaxError):
            evaluate_RPN(tokens)

        tokens = [Token(TokenType.NUMBER, 1), Token(TokenType.BINARY_OPERATOR, BinaryOperator("+"))]
        with self.assertRaises(ArithmeticSyntaxError):
            evaluate_RPN(tokens)

    # ------------------------------
    # Invalid final stack size
    # ------------------------------
    def test_final_stack_not_one(self):
        tokens = [Token(TokenType.NUMBER, 1), Token(TokenType.NUMBER, 2)]
        with self.assertRaises(ArithmeticSyntaxError):
            evaluate_RPN(tokens)

    def test_single_number(self):
        tokens = [Token(TokenType.NUMBER, 42)]
        result = evaluate_RPN(tokens)
        self.assertEqual(result, 42)

    def test_simple_addition(self):
        tokens = [
            Token(TokenType.NUMBER, 1),
            Token(TokenType.NUMBER, 2),
            Token(TokenType.BINARY_OPERATOR, BinaryOperator("+"))
        ]
        result = evaluate_RPN(tokens)
        self.assertEqual(result, 3)

    def test_simple_multiplication(self):
        tokens = [
            Token(TokenType.NUMBER, 2),
            Token(TokenType.NUMBER, 3),
            Token(TokenType.BINARY_OPERATOR, BinaryOperator("*"))
        ]
        result = evaluate_RPN(tokens)
        self.assertEqual(result, 6)

    def test_multiple_operations(self):
        # expression: 1 2 3 * +  => 1 + (2*3) = 7
        tokens = [
            Token(TokenType.NUMBER, 1),
            Token(TokenType.NUMBER, 2),
            Token(TokenType.NUMBER, 3),
            Token(TokenType.BINARY_OPERATOR, BinaryOperator("*")),
            Token(TokenType.BINARY_OPERATOR, BinaryOperator("+"))
        ]
        result = evaluate_RPN(tokens)
        self.assertEqual(result, 7)

    def test_not_enough_operands(self):
        tokens = [Token(TokenType.BINARY_OPERATOR, BinaryOperator("+"))]
        with self.assertRaises(ArithmeticSyntaxError):
            evaluate_RPN(tokens)

    def test_too_many_operands_left(self):
        tokens = [
            Token(TokenType.NUMBER, 1),
            Token(TokenType.NUMBER, 2)
        ]
        with self.assertRaises(ArithmeticSyntaxError):
            evaluate_RPN(tokens)

    def test_overflow_2(self):
        big = 2 ** 63
        tokens = [
            Token(TokenType.NUMBER, big),
            Token(TokenType.NUMBER, 2),
            Token(TokenType.BINARY_OPERATOR, BinaryOperator("*"))
        ]
        with self.assertRaises(ArithmeticOverflowError):
            evaluate_RPN(tokens)

    def eval_expr(self, expression, expected):
        """Tokenize, convert to RPN, then evaluate"""
        tokens = tokenizeregex(expression)
        rpn = shunting_yard(tokens)
        result = evaluate_RPN(rpn)
        self.assertAlmostEqual(result, expected, places=10)  # allow float rounding
    def test_sin_exp(self):
        self.eval_expr("sin(5)", math.sin(5))

    @unittest.mock.patch("helpful_modules.arithmetic_evaluator.evaluate_RPN")
    @unittest.mock.patch("helpful_modules.arithmetic_evaluator.shunting_yard")
    @unittest.mock.patch("helpful_modules.arithmetic_evaluator.tokenizeregex")
    def test_call_order(self, mock_tokenize, mock_shunting, mock_eval):
        # Arrange: set return values
        mock_tokenize.return_value = ["TOKENS"]
        mock_shunting.return_value = ["RPN"]
        mock_eval.return_value = 42

        # Act
        result = evaluate_expr("1+2")

        # Assert final value is returned correctly
        self.assertEqual(result, 42)

        # Assert each function called once
        mock_tokenize.assert_called_once_with("1+2")
        mock_shunting.assert_called_once_with(["TOKENS"])
        mock_eval.assert_called_once_with(["RPN"])

        # Assert call order
        calls = [
            unittest.mock.call("1+2"),  # tokenizeregex called first
            unittest.mock.call(["TOKENS"]),  # shunting_yard called second
            unittest.mock.call(["RPN"])  # evaluate_RPN called last
        ]

        # Check order using mock_calls
        self.assertEqual(
            [mock_tokenize.call_args, mock_shunting.call_args, mock_eval.call_args],
            calls
        )
    def test_fails_ERROR(self):
        with self.assertRaises(Exception) as cm:
            evaluate_expr("1.2.3")
        #print(cm.exception)
if __name__ == "__main__":
    unittest.main()