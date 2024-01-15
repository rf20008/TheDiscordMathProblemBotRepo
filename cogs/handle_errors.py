import sys
import traceback

import disnake
from .helper_cog import *


class ErrorHandlerCog(HelperCog):
    def __init__(self, bot):
        self.bot = bot
        self.slash = bot.slash

    async def handle_errors(self, inter, error):
        "Function called when a slash command errors"

        if print_stack_traceback[0]:
            # print the traceback to the file
            print(
                "\n".join(
                    traceback.format_exception(
                        etype=type(error), value=error, tb=error.__traceback__
                    )
                ),
                file=print_stack_traceback[1],
            )

        if isinstance(error, OnCooldown):
            await ctx.reply(str(error))
            return
        error_traceback_as_obj = traceback.format_exception(
            etype=type(error), value=error, tb=error.__traceback__
        )
        log_error(error)  # Log the error
        if isinstance(error, NotOwner):
            await ctx.reply(embed=ErrorEmbed("You are not the owner of this bot."))
            return
    # Embed = ErrorEmbed(custom_title="⚠ Oh no! Error: " + str(type(error)), description=("Command raised an exception:" + str(error)))

    error_traceback = "\n".join(error_traceback_as_obj)

    await ctx.reply(
        embed=ErrorEmbed(
            nextcord.utils.escape_markdown(error_traceback),
            custom_title="Oh, no! An exception occurred",
            footer=f"Time: {str(asctime())} Commit hash: {get_git_revision_hash()} ",
        )
    )
