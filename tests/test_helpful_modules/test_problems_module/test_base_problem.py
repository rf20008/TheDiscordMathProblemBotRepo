import unittest
import unittest.mock
import disnake
from helpful_modules.problems_module import BaseProblem, PMDeprecationWarning


# Define a standard sample problem for testing
sample_problem = BaseProblem(
    question="What is 2+2?",
    id=-1,
    author=-123456789,
    guild_id="-987654321",
    answer="4",
    voters=[],
    solvers=[],
    cache=None,
    answers=["4"],
    tolerance=0.001
)

class TestBaseProblem(unittest.TestCase):
    def test_init(self):
        problem = sample_problem
        self.assertEqual(problem.question, "What is 2+2?")
        self.assertEqual(problem.id, -1)
        self.assertEqual(problem.author, -123456789)
        self.assertEqual(problem.guild_id, "-987654321")
        self.assertEqual(problem.answer, "4")
        self.assertEqual(problem.voters, [])
        self.assertEqual(problem.solvers, [])
        self.assertIsNone(problem._cache)
        self.assertEqual(problem.answers, ["4"])
        self.assertEqual(problem.tolerance, 0.1)

    def test_from_row(self):
        row = {
            "question": "What is 3+3?",
            "problem_id": -2,
            "guild_id": None,
            "author": "-987654321",
            "answers": ["6"],
            "voters": [],
            "solvers": [],
            "tolerance": 0.2
        }
        problem = BaseProblem.from_row(row)
        self.assertEqual(problem.question, "What is 3+3?")
        self.assertEqual(problem.id, -2)
        self.assertEqual(problem.author, "-987654321")
        self.assertIsNone(problem.guild_id)
        self.assertEqual(problem.answers, ["6"])
        self.assertEqual(problem.tolerance, 0.2)

    def test_from_dict(self):
        problem_dict = {
            "question": "What is 4+4?",
            "id": "-3",
            "guild_id": "-987654321",
            "voters": [],
            "solvers": [],
            "author": -123456789,
            "answers": ["8"],
            "tolerance": 0.3
        }
        problem = BaseProblem.from_dict(problem_dict)
        self.assertEqual(problem.question, "What is 4+4?")
        self.assertEqual(problem.id, -3)
        self.assertEqual(problem.author, -123456789)
        self.assertEqual(problem.guild_id, "-987654321")
        self.assertEqual(problem.answers, ["8"])
        self.assertEqual(problem.tolerance, 0.3)

    def test_to_dict(self):
        problem_dict = sample_problem.to_dict()
        expected_dict = {
            "type": "MathProblem",
            "question": "What is 2+2?",
            "id": "-1",
            "guild_id": "-987654321",
            "voters": [],
            "solvers": [],
            "author": -123456789,
            "answers": ["4"],
            "tolerance": 0.1
        }
        self.assertEqual(problem_dict, expected_dict)

    # Tests for other methods...
    def test_add_voter(self):
        problem = sample_problem
        problem.add_voter("-987654321")  # Adding a voter
        self.assertIn("-987654321", problem.voters)

    def test_add_solver(self):
        problem = sample_problem
        problem.add_solver(unittest.mock.AsyncMock(spec=disnake.User, id=-987654321))  # type: ignore  # Adding a solver
        self.assertIn("-987654321", problem.solvers)

    def test_add_answer(self):
        problem = sample_problem
        problem.add_answer("8")  # Adding an answer
        self.assertIn("8", problem.answers)

    def test_get_answer(self):
        problem = sample_problem
        with self.assertRaises(PMDeprecationWarning):
            problem.get_answer()  # Deprecated method

    def test_get_answers(self):
        problem = sample_problem
        with self.assertRaises(PMDeprecationWarning):
            problem.get_answers()  # Deprecated method

    def test_get_question(self):
        problem = sample_problem
        self.assertEqual(problem.get_question(), "What is 2+2?")

    def test_check_answer_and_add_checker(self):
        problem = sample_problem
        problem.check_answer_and_add_checker("4", "-987654321")  # Checking answer and adding a solver
        self.assertIn("-987654321", problem.solvers)

    def test_check_answer(self):
        problem = sample_problem
        self.assertTrue(problem.check_answer("4"))  # Checking correct answer
        self.assertFalse(problem.check_answer("5"))  # Checking incorrect answer

    def test_my_id(self):
        problem = sample_problem
        self.assertEqual(problem.my_id(), [-1, "-987654321"])

    def test_get_voters(self):
        problem = sample_problem
        self.assertEqual(problem.get_voters(), [])

    def test_get_num_voters(self):
        problem = sample_problem
        self.assertEqual(problem.get_num_voters(), 0)

    def test_is_voter(self):
        problem = sample_problem
        self.assertFalse(problem.is_voter("-987654321"))  # Not a voter

    def test_get_solvers(self):
        problem = sample_problem
        self.assertEqual(problem.get_solvers(), [])

    def test_is_solver(self):
        problem = sample_problem
        self.assertFalse(problem.is_solver("-987654321")) # Not a solver

    def test_get_author(self):
        problem = sample_problem
        self.assertEqual(problem.get_author(), -123456789)

    def test__int_guild_id(self):
        problem = sample_problem
        self.assertEqual(problem._int_guild_id, -1)

    def test_is_author(self):
        problem = sample_problem
        self.assertTrue(problem.is_author(-123456789))  # Is the author

    def test___eq__(self):
        problem1 = sample_problem
        problem2 = sample_problem
        self.assertEqual(problem1, problem2)  # Problems are equal

    def test___repr__(self):
        problem = sample_problem
        self.assertEqual(
            repr(problem),
            "BaseProblem(question='What is 2+2?', answers = ['4'], id = -1, guild_id=-1, voters=[],solvers=[],author=-987654321,cache=None )"
        )  # Representation matches expected value

    def test___str__(self):
        problem = sample_problem
        self.assertEqual(
            str(problem),
            "Question: 'What is 2+2?', \n        id: -1, \n        guild_id: -1, \n        solvers: [],\n        author: <@-987654321>\n        "
        )  # String representation matches expected value

    def test___deepcopy__(self):
        import copy
        problem = sample_problem
        copied_problem = copy.deepcopy(problem)
        self.assertEqual(problem, copied_problem)  # Deepcopy matches original object

    def test_get_extra_stuff(self):
        problem = sample_problem
        self.assertEqual(problem.get_extra_stuff(), {})  # No extra stuff present


if __name__ == "__main__":
    unittest.main()
