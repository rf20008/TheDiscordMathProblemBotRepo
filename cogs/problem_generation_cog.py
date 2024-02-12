import random
import typing
from copy import copy

import disnake
from disnake import *
from disnake.ext import commands

from helpful_modules import (
    checks,
    problems_module,
)
from helpful_modules.custom_bot import TheDiscordMathProblemBot
from helpful_modules.custom_embeds import ErrorEmbed, SuccessEmbed, SimpleEmbed
from helpful_modules.problem_generator import *
from helpful_modules.threads_or_useful_funcs import generate_new_id

from .helper_cog import HelperCog
class ProblemGenerationCog(HelperCog):
    def __init__(self, bot: TheDiscordMathProblemBot):
        super().__init__(bot)
        self.bot: TheDiscordMathProblemBot = bot
        # checks = self.checks
        checks.setup(bot)
    @commands.slash_command(
        name="generate_new_problems",
        description="Generates new problems",
        options=[
            Option(
                name="num_new_problems_to_generate",
                description="the number of problems that should be generated",
                type=OptionType.integer,
                required=True,
            )
        ],
    )
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def generate_new_problems(
        self,
        inter: disnake.ApplicationCommandInteraction,
        num_new_problems_to_generate: int,
    ) -> typing.Optional[disnake.Message]:
        """/generate_new_problems [num_new_problems_to_generate: int]
        Generate new Problems."""
        # TODO: problem_generator class (and use formulas :-))
        await inter.response.defer()
        if inter.author.id not in self.bot.trusted_users:
            await inter.send(embed=ErrorEmbed("You aren't trusted!"), ephemeral=True)
            return
        if num_new_problems_to_generate > 200:
            return await inter.send(
                embed=ErrorEmbed(
                    "You are trying to create too many problems. Try something smaller than or equal to 200."
                ),
                ephemeral=True,
            )

        for i in range(num_new_problems_to_generate):  # basic problems for now.... :(
            # TODO: linear equations, etc

            operation = random.choice(["+", "-", "*", "/", "^"])
            if operation == "^":
                num1 = random.randint(1, 20)
                num2 = random.randint(1, 20)
            else:
                num1 = random.randint(-1000, 1000)
                num2 = random.randint(-1000, 1000)
                while num2 == 0 and operation == "/":  # Prevent ZeroDivisionError
                    num2 = random.randint(-1000, 1000)

            if operation == "^":
                try:
                    answer = num1**num2

                except OverflowError:  # Too big?
                    try:
                        del answer
                    except NameError:
                        pass
                    continue
            elif operation == "+":
                answer = num1 + num2
            elif operation == "-":
                answer = num1 - num2
            elif operation == "*":
                answer = num1 * num2
            elif operation == "/":
                answer = round(num1 * 100 / num2) / 100

            while True:
                problem_id = generate_new_id()
                if problem_id not in [
                    problem.id for problem in await self.cache.get_global_problems()
                ]:  # All problem_ids
                    break
            question = (
                f"What is {num1} "
                + {
                    "*": "times",
                    "+": "times",
                    "-": "minus",
                    "/": "divided by",
                    "^": "to the power of",
                }[operation]
                + f" {str(num2)}?"
            )
            Problem = problems_module.BaseProblem(
                question=question,
                answer=str(answer),
                author=845751152901750824,
                guild_id=None,
                id=problem_id,
                cache=copy(self.cache),
            )
            await self.cache.add_problem(problem_id, Problem)
        await inter.send(
            embed=SuccessEmbed(
                f"Successfully created {str(num_new_problems_to_generate)} new problems!"
            ),
            ephemeral=True,
        )
def setup(bot: TheDiscordMathProblemBot):
    bot.add_cog(ProblemGenerationCog(bot))


def teardown(bot):
    bot.remove_cog("ProblemGenerationCog")