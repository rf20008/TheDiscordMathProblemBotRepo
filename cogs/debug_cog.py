import asyncio
import contextlib
import copy
import io
import textwrap
from traceback import format_exception

import disnake
from disnake.ext import commands

from helpful_modules import checks, problems_module
from helpful_modules.custom_bot import TheDiscordMathProblemBot
from helpful_modules.custom_embeds import ErrorEmbed, SimpleEmbed, SuccessEmbed
from helpful_modules.threads_or_useful_funcs import get_log
from .helper_cog import HelperCog
from .interesting_computation_ import InterestingComputationCog
CRTC = InterestingComputationCog.ChineseRemainderTheoremComputer
log = get_log(__name__)


class DebugCog(HelperCog):
    """Commands for debugging :-)"""

    def __init__(self, bot: TheDiscordMathProblemBot):
        super().__init__(bot)

    async def cog_slash_command_check(self, inter: disnake.ApplicationCommandInteraction):
        """A check that makes sure only bot owners can use this cog!"""
        if not await self.bot._is_owner(inter.author):
            raise commands.CheckFailure("You are not the owner of this bot!")
        return True
        # if self.bot.owner_id in [None, [], set()] and self.bot.owner_ids is None:
        #     raise commands.CheckFailure(
        #         "Failing to protect myself (neither owner_id nor owner_ids are defined)"
        #     )
        # if self.bot.owner_id in [None, [], set()]:
        #     raise commands.CheckFailure(
        #         "You're not the owner of this bot! You must be the owner to execute debug commands!"
        #     )
        # if self.bot.owner_id == inter.author.id:
        #     return True
        #
        # try:
        #     if (
        #         self.bot.owner_ids not in [None, [], set()]
        #         and inter.author.id in self.bot.owner_ids
        #     ):
        #         return True
        #     raise commands.CheckFailure("You don't own this bot!")
        # except AttributeError:
        #     raise commands.CheckFailure("You don't own this bot!")

    @commands.is_owner()
    @checks.trusted_users_only()
    @commands.slash_command(
        name="sql",
        description="Run SQL",
        options=[
            disnake.Option(
                name="query",
                description="The query to run",
                type=disnake.OptionType.string,
                required=True,
            )
        ],
    )
    async def sql(self, inter: disnake.ApplicationCommandInteraction, query: str, ephemeral: bool = False):
        """/sql [query: str]
        A debug command to run SQL!
        You must own this bot to run this command!"""
        try:
            assert await self.cog_slash_command_check(inter)
        except AssertionError:
            await inter.send("I don't believe you own me.")
            raise
        except CheckFailure:
            raise
        try:
            result = await self.cache.run_sql(query)
        except BaseException as e:
            await inter.send("An exception occurred while running the SQL!", ephemeral=ephemeral)
            raise

        await inter.send(f"Result: {result}", ephemeral=ephemeral)
        return

    @commands.is_owner()
    @checks.trusted_users_only()
    @commands.slash_command(
        name="eval",
        description="Execute arbitrary python code (only owners can do this)",
        options=[
            disnake.Option(
                name="code",
                description="The code to execute",
                type=disnake.OptionType.string,
                required=True,
            ),
            disnake.Option(
                name = "ephemeral",
                description = "Whether the result of the code should be printed ephemerally",
                type=disnake.OptionType.boolean,
                required=False
            )
        ],
    )
    async def eval(self, inter: disnake.ApplicationCommandInteraction, code: str, ephemeral=False):
        """/eval [code: str]
        Evaluate arbitrary python code.
        Any instances of `\n` in code and stdin will be replaced with a newline character!
        This will happen even in strings. Therefore, be very careful!
        Only the owner can run this command!
        This requires both the owner and the bot to have the Administrator permission.
        """
        new_stdout = io.StringIO()
        new_stderr = io.StringIO()
        try:
            if not await self.cog_slash_command_check(inter):
                await inter.send("I know that you don't own me. You cannot use /eval. Goodbye.")
                return
        except CheckFailure:
            raise

        # the administrator permission requiring was removed
        code_ = "\n".join(code.split("\\n"))  # Split the code by `\n`
        thing_to_run = """async def func(): 
        """  # maybe: just exec() directly
        thing_to_run += textwrap.indent(code_, "    ", predicate=lambda l: True)
        compiled = False
        new_globals = {
            "bot": self.bot,
            "cache": self.cache,
            "self": self,
            "inter": inter,
            "author": inter.author,
        }
        new_globals.update(
            globals()
        )  # credit: https://github.com/Rapptz/RoboDanny/blob/rewrite/cogs/admin.py#L234
        try:
            exec(thing_to_run, new_globals, locals())
            compiled = True
        except BaseException as e:
            compiled = False
            new_stderr.write("".join(format_exception(e)))
        if (
            "func" not in globals().keys()
            and "func" not in locals().keys()
            and compiled is True
        ):
            raise RuntimeError("func is not defined")
        if compiled:
            try:
                with contextlib.redirect_stdout(new_stdout):
                    with contextlib.redirect_stderr(new_stderr):
                        if "func" in globals().keys():
                            print(
                                await globals()["func"](), file=new_stdout
                            )  # Get the 'func' from the global variables and call it
                            log.info("/eval ran (found in globals)")
                        elif "func" in locals().keys():
                            print(
                                await locals()["func"](), file=new_stdout
                            )  # Get func() from locals and call it
                            log.info("/eval ran (found in locals)")
                        else:
                            raise Exception(f"""fatal: func() not defined""")
            except BaseException as e:
                new_stderr.write("".join(format_exception(e)))
        await inter.send(
            embed=SuccessEmbed(
                f"""The code was successfully executed!
stdout: ```{new_stdout.getvalue()} ```
stderr: ```{new_stderr.getvalue()} ```"""
            ),
            ephemeral=ephemeral
        )
        new_stdout.close()
        new_stderr.close()
        return
