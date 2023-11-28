"""A cog made to test TheDiscordMathProblemBot's connection to Discord. This doesn't provide the bot extra functionality.
This cog, like everything else in this repository, is licensed under GPLv3 (or later)"""
import typing

import disnake

from .helper_cog import HelperCog


class TestCog(HelperCog):
    """A cog made to test the bot's connection to Discord. This cog does not provide extra functionality"""

    def __init__(self, bot: disnake.ext.commands.Bot):
        super().__init__(bot)

    @disnake.ext.commands.slash_command(
        name="_test",
        description="A command that when executed, returns the string 'test' & takes no arguments",
    )
    async def _test(
        self, inter: disnake.ApplicationCommandInteraction
    ) -> typing.Optional[disnake.InteractionMessage]:
        """/_test
        This makes the bot return Test. This doesn't take any arguments. The purpose of this command is to test the bot!
        """
        return await inter.send("Test")

    @disnake.ext.commands.command(name="_test")
    async def test(self, ctx):
        """Returns test & takes no arguments. Useful only for debugging purposes"""
        return await ctx.send("test")
