import json
import typing
from asyncio import sleep as asyncio_sleep
from copy import copy
from io import BytesIO  # For file submitting!
from os import cpu_count
from sys import version, version_info
from time import asctime
from typing import Union

import disnake
from disnake.ext import commands
from mpmath import *

from helpful_modules import (checks, problems_module,
                             the_documentation_file_loader)
from helpful_modules.custom_bot import TheDiscordMathProblemBot
from helpful_modules.custom_buttons import (BasicButton, ConfirmationButton,
                                            MyView)
from helpful_modules.custom_embeds import ErrorEmbed, SimpleEmbed, SuccessEmbed
from helpful_modules.save_files import FileSaver
from helpful_modules.threads_or_useful_funcs import (
    get_git_revision_hash, miller_robin_primality_test)

from .deletion_view import GuildDataDeletionView
from .helper_cog import HelperCog

CAN_SEND_MESSAGES_TO = (
    disnake.MessageInteraction,
    disnake.ApplicationCommandInteraction,
    disnake.Interaction,
    disnake.abc.Messageable,
    disnake.TextChannel,
    disnake.PartialMessageable,
    commands.Context,
    disnake.VoiceChannel,
    disnake.Thread,
    disnake.abc.GuildChannel,
)
GUILD_DATA_DELETION_TIMEOUT = 250
TEN_BILLION = 10_000_000_000


# TODO: Split this into different cogs for readability purpose


class MiscCommandsCog(HelperCog):
    def __init__(self, bot: TheDiscordMathProblemBot):
        super().__init__(bot)
        checks.setup(bot)  # Sadly, Interactions do not have a bot parameter
        self.bot: TheDiscordMathProblemBot = bot
        self.cache: problems_module.MathProblemCache = bot.cache

    @commands.cooldown(1, 15, commands.BucketType.user)
    @commands.slash_command(
        name="info",
        description="Bot info!",
        options=[
            disnake.Option(
                name="include_extra_info",
                description="Whether to include extra, technical info",
                required=False,
                type=disnake.OptionType.boolean,
            )
        ],
    )
    async def info(
            self,
            inter: disnake.ApplicationCommandInteraction,
            include_extra_info: bool = False,
    ):
        """/info [include_extra_info: bool = False]
        Show bot info. include_extra_info shows technical information!"""
        embed = SimpleEmbed(title="Bot info", description="")
        embed = embed.add_field(
            name="Original Bot Developer", value="ay136416#2707", inline=False
        )  # Could be sufficient for attribution (except for stating changes).
        embed = embed.add_field(
            name="Github Repository Link", value=self.bot.constants.SOURCE_CODE_LINK
        )
        embed = embed.add_field(
            name="Latest Git Commit Hash",
            value=str(get_git_revision_hash()),
            inline=False,
        )
        embed = embed.add_field(
            name="Current Latency to Discord",
            value=f"{round(self.bot.latency * 10000) / 10}ms",
            inline=False,
        )
        current_version_info = version_info
        python_version_as_str = f"""Python {
        current_version_info.major
        }.{
        current_version_info.minor
        }.{
        current_version_info.micro}{
        current_version_info.releaselevel
        }"""

        embed = embed.add_field(
            name="Python version", value=python_version_as_str, inline=False
        )  # uh oh
        if include_extra_info:
            embed = embed.add_field(
                name="Python version given by sys.version", value=str(version)
            )

            # embed = embed.add_field(
            #    name="Nextcord version", value=str(disnake.__version__)
            # )
            embed = embed.add_field(
                name="Disnake version", value=str(disnake.__version__)
            )
            embed = embed.add_field(
                name="""CPU count 
                (which may not necessarily be the amount of CPU available to the bot due to a Python limitation)""",
                value=str(cpu_count()),
            )
            embed = embed.add_field(
                name="License",
                value="""This bot is licensed under GPLv3. 
                Please see [the official GPLv3 website that explains the GPLv3](https://www.gnu.org/licenses/gpl-3.0.en.html) for more details.""",
                # noqa: E501
            )
            embed = embed.add_field(
                name="Uptime",
                value=(
                    f"""The bot started at {disnake.utils.format_dt(self.bot.timeStarted)} and has been up for {round(self.bot.uptime)} seconds."""
                ),
            )

        await inter.send(embed=embed)

    @commands.cooldown(1, 5, commands.BucketType.user)  # 5 second user cooldown
    @commands.cooldown(
        20, 50, commands.BucketType.default
    )  # 20 times before a global cooldown of 50 seconds is established
    @commands.guild_only()  # Due to bugs, it doesn't work in DM's
    @commands.slash_command(
        name="list_trusted_users", description="list all trusted users"
    )
    async def list_trusted_users(self, inter):
        """/list_trusted_users
        List all trusted users in username#discriminator format (takes no arguments)"""
        # await inter.send(type=5)  # Defer
        # Deferring might be unnecessary & and cause errors
        # We might not be able to respond in time because of the 100ms delay between user fetching
        # This is to respect the API rate limit.

        # We don't need a try/except
        result = await self.cache.run_sql("SELECT * FROM user_data")
        trusted_users = []
        for item in result:
            if item["trusted"]:
                trusted_users.append(item["user_id"])
        if len(trusted_users) == 0:
            await inter.send("There are no trusted users.")
            return
            # raise Exception("There are no trusted users!")

        __trusted_users = ""

        for user_id in trusted_users:
            try:
                user = await self.bot.fetch_user(user_id)
                __trusted_users += f"""{user.name}#{user.discriminator}
            """
            except (disnake.NotFound, disnake.NotFound):
                # A user with this ID does not exist
                try:
                    user_data = await self.bot.cache.get_user_data(
                        user_id, default=problems_module.UserData.default()
                    )
                    user_data.trusted = False
                    await self.cache.set_user_data(user_id, user_data)

                    try:
                        del f
                    except NameError:
                        pass
                except BaseException as e:
                    raise RuntimeError(
                        "Could not save the files after removing the nonexistent trusted user!!"
                    ) from e
            except (
                    disnake.Forbidden,
                    disnake.Forbidden,
            ) as exc:  # Cannot fetch this user!
                raise RuntimeError("Cannot fetch users") from exc
            else:
                await asyncio_sleep(
                    0.1
                )  # 100 ms between fetching to respect the rate limit (and to prevent spam)

        await inter.send(__trusted_users, ephemeral=True)

    @checks.has_privileges(blacklisted=False)
    @commands.cooldown(1, 30, commands.BucketType.user)
    @commands.slash_command(
        name="ping", description="Prints latency and takes no arguments"
    )
    async def ping(self, inter: disnake.ApplicationCommandInteraction):
        """Ping the bot which returns its latency! This command does not take any arguments."""
        # TODO: round-trip latency, etc
        await inter.send(
            embed=SuccessEmbed(
                f"Pong! My latency is {round(self.bot.latency * 1000)}ms."
            ),
            ephemeral=True,
        )

    @checks.is_not_blacklisted()
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.slash_command(
        name="what_is_vote_threshold",
        description="Prints the vote threshold and takes no arguments",
    )
    async def what_is_vote_threshold(
            self, inter: disnake.ApplicationCommandInteraction
    ):
        """/what_is_vote_threshold
        Returns the vote threshold. Takes no arguments.
        There is a 5-second cooldown on this command."""
        await inter.send(
            embed=SuccessEmbed(f"The vote threshold is {self.bot.vote_threshold}."),
            ephemeral=True,
        )

    @checks.has_privileges(blacklisted=False)
    @commands.slash_command(
        name="generate_invite_link",
        description="Generates a invite link for this bot! Takes no arguments",
    )
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def generate_invite_link(self, inter: disnake.ApplicationCommandInteraction):
        """/generate_invite_link
        Generate an invite link for the bot. Takes no arguments"""
        await inter.send(
            embed=SuccessEmbed(
                disnake.utils.oauth_url(
                    client_id=self.bot.application_id,
                    permissions=disnake.Permissions(
                        send_messages=True,
                        read_messages=True,
                        embed_links=True,
                        use_slash_commands=True,
                        attach_files=True,
                    ),
                    scopes=["bot", "applications.commands"],
                )
            ),
            ephemeral=True,
        )

    @commands.slash_command(
        name="github_repo", description="Returns the link to the github repo"
    )
    @commands.cooldown(2, 120, commands.BucketType.user)
    async def github_repo(self, inter: disnake.ApplicationCommandInteraction):
        """/github_repo
        Gives you the link to the bot's GitHub repo.
        If you fork this, you must link the new source code link due to the GPL.
        There is a 2-minute cooldown on this command (after it has been executed 2 times)
        """
        await inter.send(
            embed=SuccessEmbed(
                f"[Repo Link:]({self.bot.constants.SOURCE_CODE_LINK})",
                successTitle="Here is the Github Repository Link.",
            )
        )

    @checks.trusted_users_only()
    @commands.cooldown(
        1, 50, commands.BucketType.user
    )  # Don't overload the bot (although trusted users will probably not)
    @commands.cooldown(
        15, 500, commands.BucketType.default
    )  # To prevent wars! If you want your own version, self host it :-)
    @commands.slash_command(
        name="set_vote_threshold",
        description="Sets the vote threshold",
        options=[
            disnake.Option(
                name="threshold",
                description="the threshold you want to change it to",
                type=disnake.OptionType.integer,
                required=True,
            )
        ],
    )
    async def set_vote_threshold(
            self, inter: disnake.ApplicationCommandInteraction, threshold: int
    ):
        """/set_vote_threshold [threshold: int]
        Set the vote threshold. Only trusted users may do this.
        There is a 50-second cooldown.
        This might cause a race condition"""
        # try:
        #    threshold = int(threshold)
        # except TypeError:  # Conversion failed!
        #    await inter.send(
        #        embed=ErrorEmbed(
        #            "Invalid threshold argument! (threshold must be an integer)"
        #        ),
        #        ephemeral=True,
        #    )
        #    return
        # Unnecessary because the type is an integer
        if threshold < 1:  # Threshold must be greater than 1!
            await inter.send(
                embed=ErrorEmbed("You can't set the threshold to smaller than 1."),
                ephemeral=True,
            )
            return
        vote_threshold = int(threshold)  # Probably unnecessary
        for problem in await self.bot.cache.get_global_problems():
            if problem.get_num_voters() >= vote_threshold:
                # If the number of the voters of the problem exceeds the vote threshold,
                # delete the problem.
                await self.cache.remove_problem(problem.id)
        await inter.send(
            embed=SuccessEmbed(
                f"The vote threshold has successfully been changed to {threshold}!"
            ),
            ephemeral=True,
        )
        return


    @commands.slash_command(
        name="submit_a_request",
        description="Submit a request. I will know!",
        options=[
            disnake.Option(
                name="offending_problem_guild_id",
                description="The guild id of the problem you are trying to remove.",
                type=disnake.OptionType.integer,
                required=False,
            ),
            disnake.Option(
                name="offending_problem_id",
                description="The problem id of the problem. Very important (so I know which problem to check)",
                type=disnake.OptionType.integer,
                required=False,
            ),
            disnake.Option(
                name="extra_info",
                description="A up to 5000 character description (about 2 pages) Use this wisely!",
                type=disnake.OptionType.string,
                required=False,
            ),
            disnake.Option(
                name="copyrighted_thing",
                description="The copyrighted thing that this problem is violating",
                type=disnake.OptionType.string,
                required=False,
            ),
            disnake.Option(
                name="type",
                description="Request type",
                required=False,
                type=disnake.OptionType.string,
            ),
        ],
    )
    async def submit_a_request(
            self,
            inter: disnake.ApplicationCommandInteraction,
            offending_problem_guild_id: int = None,
            offending_problem_id: int = None,
            extra_info: str = None,
            copyrighted_thing: str = Exception,
            type: str = "",
    ):
        """/submit_a_request [offending_problem_guild_id: int = None] [offending_problem_id: int = None]

        Submit a request! I will know! It uses a channel in my discord server and posts an embed.
        If you do not provide a guild id, it will be None.
        I will probably deprecate this and replace it with emailing me.
        This command has been deprecated."""
        if (
                extra_info is None
                and type == ""
                and copyrighted_thing is not Exception
                and offending_problem_guild_id is None
                and offending_problem_id is None
        ):
            await inter.send(embed=ErrorEmbed("You must specify some field."))
        if extra_info is None:
            await inter.send(embed=ErrorEmbed("Please provide extra information!"))
        assert len(extra_info) <= 5000
        try:
            channel = await self.bot.fetch_channel(
                901464948604039209
            )  # CHANGE THIS IF YOU HAVE A DIFFERENT REQUESTS CHANNEL! (the part after id)
            # TODO: make this an env var
        except (disnake.ext.commands.ChannelNotReadable, disnake.Forbidden):
            raise RuntimeError("The bot cannot send messages to the channel!")
        try:
            Problem = await self.bot.cache.get_problem(
                offending_problem_guild_id, offending_problem_id
            )
            problem_found = True
        except (TypeError, KeyError, problems_module.ProblemNotFound):
            # Problem not found
            problem_found = False
        embed = disnake.Embed(
            title=(
                f"A new {type} request has been received from {inter.author.name}#{inter.author.discriminator}!"
            ),
            description="",
        )

        if problem_found:
            embed.description = f"Problem_info:{str(problem)}"  # type: ignore
        embed.description += f"""Copyrighted thing: (if legal): {copyrighted_thing}
        Extra info: {extra_info}"""
        if problem_found:
            embed.set_footer(text=str(Problem) + asctime())
        else:
            embed.set_footer(text=str(asctime()))

        content = "A request has been submitted."
        for (
                owner_id
        ) in (
                self.bot.owner_ids
        ):  # Mentioning owners: may be removed (you can also remove it as well)
            content += f"<@{owner_id}>"
        content += f"<@{self.bot.owner_id}>"
        await channel.send(embed=embed, content=content)
        await inter.send("Your request has been submitted!")

    @checks.has_privileges(blacklisted=False)
    @commands.cooldown(1, 1, commands.BucketType.user)
    @commands.slash_command(
        name="documentation",
        description="Returns help!",
        options=[
            disnake.Option(
                name="documentation_type",
                description="What kind of help you want",
                choices=[
                    disnake.OptionChoice(
                        name="documentation_link", value="documentation_link"
                    ),
                    disnake.OptionChoice(name="command_help", value="command_help"),
                    disnake.OptionChoice(name="function_help", value="function_help"),
                    disnake.OptionChoice(name="privacy_policy", value="privacy_policy"),
                    disnake.OptionChoice(
                        name="terms_of_service", value="terms_of_service"
                    ),
                ],
                required=True,
            ),
            disnake.Option(
                name="help_obj",
                description="What you want help on",
                required=False,
                type=disnake.OptionType.string,
            ),
        ],
    )
    async def documentation(
            self,
            inter: disnake.ApplicationCommandInteraction,
            documentation_type: typing.Literal[
                "documentation_link",  # type: ignore
                "command_help",
                "function_help",
                "privacy_policy",
                "terms_of_service",
            ],
            help_obj: str = None,
    ) -> typing.Optional[disnake.Message]:
        """/documentation {documentation_type: str|documentation_link|command_help|function_help} {help_obj}

        Prints documentation :-). If the documentation is a command, it attempts to get its docstring.
        Otherwise, it gets the cached documentation.
        help_obj will be ignored if documentation_type is privacy_policy or documentation_link.
        Legend (for other documentation)
        /command_name: the command
        {argument_name: type |choice1|choice2|...} -
        A required argument with choices of the given type, and the available choices are choice1, choice 2, etc.
        {argument_name: type |choice1|choice2|... = default} -
        An optional argument that defaults to default if not specified.
        Arguments must be a choice specified (from choice 1 etc.) and must be of the type specified.
        [argument_name: type = default] -
        An argument with choices of the given type, and defaults to default if not specified. Strings are represented without quotation marks.
        (argument_name: type) -
        A required argument of the given type"""
        if help_obj is None and documentation_type in ["command_help", "function_help"]:
            return await inter.send(
                embed=ErrorEmbed(
                    "I can't help you with a command or function unless you tell me what you want help on!"
                )
            )
        if documentation_type == "documentation_link":
            await inter.send(
                embed=SuccessEmbed(
                    f"""<@{inter.author.id}> [Click here](https://github.com/rf20008/TheDiscordMathProblemBotRepo/tree/master/docs) for my documentation.
        """
                ),
                ephemeral=True,
            )
            return None
        if documentation_type == "command_help":
            try:
                command = self.bot.get_slash_command(help_obj)  # Get the command
                if command is None:  # command not found
                    return await inter.send(
                        embed=ErrorEmbed(
                            custom_title="I couldn't find your command!",
                            description=":x: Could not find the command specified. ",
                        )
                    )
                command_docstring = command.callback.__doc__
                if command_docstring is None:
                    return await inter.send(
                        "Oh no! This command does not have documentation! Please report this bug."
                    )
                return await inter.send(
                    embed=SuccessEmbed(description=str(command_docstring))
                )
            except AttributeError as exc:
                # My experiment failed
                raise Exception("uh oh...") from exc  # My experiment failed!
        elif documentation_type == "function_help":
            warnings.warn(DeprecationWarning("This has been deprecated"))
            documentation_loader = (
                the_documentation_file_loader.DocumentationFileLoader()
            )
            try:
                _documentation = documentation_loader.get_documentation(
                    {
                        "function_help": "docs/misc-non-commands-documentation.md",
                    }[documentation_type],
                    help_obj,
                )
            except the_documentation_file_loader.DocumentationNotFound as e:
                if isinstance(
                        e, the_documentation_file_loader.DocumentationFileNotFound
                ):
                    await inter.send(
                        embed=ErrorEmbed(
                            "Documentation file was not found. Please report this error!"
                        )
                    )
                    return None
                await inter.send(embed=ErrorEmbed(str(e)))
                return None
            await inter.send(_documentation)
        elif documentation_type == "privacy_policy":
            await inter.send(
                "The link to the privacy policy is [https://github.com/rf20008/TheDiscordMathProblemBotRepo/blob/beta/TERMS_AND_CONDITIONS.md](here)"
            )
            return
        elif documentation_type == "terms_of_service":
            # TODO: soft-code this in a config.json file
            await inter.send(
                "The link to the terms of service is here: [https://github.com/rf20008/TheDiscordMathProblemBotRepo/blob/beta/TERMS_AND_CONDITIONS.md](Terms of Service Link)"
            )
            return

            # with open("TERMS_AND_CONDITIONS.md") as file:
            #    await inter.send(
            #        embed=SuccessEmbed("".join([line for line in file]))
            #    )  # Concatenate the lines in the file + send them
        else:
            raise NotImplementedError(
                "This hasn't been implemented yet. Please contribute something!"
            )

    @checks.has_privileges(blacklisted=False)
    @checks.trusted_users_only()
    @checks.is_not_blacklisted()
    @commands.cooldown(1, 1, commands.BucketType.user)
    @commands.slash_command(
        name="blacklist",
        description="Blacklist someone from the bot!",
        options=[
            disnake.Option(
                name="user",
                description="The user to blacklist",
                type=disnake.OptionType.user,
                required=True,
            )
        ],
    )
    async def blacklist(
            self: "MiscCommandsCog",
            inter: disnake.ApplicationCommandInteraction,
            user: typing.Union[disnake.User, disnake.Member],
    ):
        """/blacklist [user: user]
        Blacklist someone from the bot. You must be a trusted user to do this!
        There is a 1-second cooldown."""
        user_data = await self.cache.get_user_data(
            user_id=user.id,
            default=problems_module.UserData(
                user_id=user.id, trusted=False, blacklisted=False
            ),
        )
        if not user_data.blacklisted:
            bot.log.debug("Can't blacklist user; user already blacklisted")
            return await inter.send("Can't blacklist user; user already blacklisted")
        else:
            user_data.blacklisted = True
            try:
                await self.cache.update_user_data(user_id=user.id, new=user_data)
            except problems_module.MathProblemsModuleException:
                await self.cache.add_user_data(user_id=user.id, new=user_data)
            self.bot.log.info(f"Successfully blacklisted the user with id {user.id}")
            await inter.send("Successfully blacklisted the user!")

            # TODO: what do I do after a user gets blacklisted? Do I delete their data?



    @commands.slash_command(
        description="This command gives you documentation."
    )
    async def documentation(
            self,
            inter: disnake.ApplicationCommandInteraction,
            documentation_type: typing.Literal[
                "documentation_link",  # type: ignore
                "command_help",
                "function_help",
                "privacy_policy",
                "terms_of_service",
            ],
            help_obj: str = None,
    ) -> typing.Optional[disnake.Message]:
        """/documentation {documentation_type: str|documentation_link|command_help|function_help} {help_obj}

        Prints documentation :-). If the documentation is a command, it attempts to get its docstring.
        Otherwise, it gets the cached documentation.
        help_obj will be ignored if documentation_type is privacy_policy or documentation_link.
        Legend (for other documentation)
        /command_name: the command
        {argument_name: type |choice1|choice2|...} -
        A required argument with choices of the given type, and the available choices are choice1, choice 2, etc.
        {argument_name: type |choice1|choice2|... = default} -
        An optional argument that defaults to default if not specified.
        Arguments must be a choice specified (from choice 1 etc.) and must be of the type specified.
        [argument_name: type = default] -
        An argument with choices of the given type, and defaults to default if not specified. Strings are represented without quotation marks.
        (argument_name: type) -
        A required argument of the given type
        You can use this command even if you are blacklisted!"""

        if help_obj is None and documentation_type in ["command_help", "function_help"]:
            return await inter.send(
                embed=ErrorEmbed(
                    "I can't help you with a command or function unless you tell me what you want help on!"
                )
            )
        if documentation_type == "documentation_link":
            await inter.send(
                embed=SuccessEmbed(
                    f"""<@{inter.author.id}> [Click here](https://github.com/rf20008/TheDiscordMathProblemBotRepo/tree/master/docs) for my documentation.
        """
                ),
                ephemeral=True,
            )
            return None
        if documentation_type == "command_help":
            try:
                command = self.bot.get_slash_command(help_obj)  # Get the command
                if command is None:  # command not found
                    return await inter.send(
                        embed=ErrorEmbed(
                            custom_title="I couldn't find your command!",
                            description=":x: Could not find the command specified. ",
                        )
                    )
                command_docstring = command.callback.__doc__
                if command_docstring is None:
                    return await inter.send(
                        "Oh no! This command does not have documentation! Please report this bug."
                    )
                return await inter.send(
                    embed=SuccessEmbed(description=str(command_docstring))
                )
            except AttributeError as exc:
                # My experiment failed
                raise Exception("uh oh...") from exc  # My experiment failed!
        elif documentation_type == "function_help":
            warnings.warn(DeprecationWarning("This has been deprecated"))
            documentation_loader = (
                the_documentation_file_loader.DocumentationFileLoader()
            )
            try:
                _documentation = documentation_loader.get_documentation(
                    {
                        "function_help": "docs/misc-non-commands-documentation.md",
                    }[documentation_type],
                    help_obj,
                )
            except the_documentation_file_loader.DocumentationNotFound as e:
                if isinstance(
                        e, the_documentation_file_loader.DocumentationFileNotFound
                ):
                    await inter.send(
                        embed=ErrorEmbed(
                            "Documentation file was not found. Please report this error!"
                        )
                    )
                    return None
                await inter.send(embed=ErrorEmbed(str(e)))
                return None
            await inter.send(_documentation)
        elif documentation_type == "privacy_policy":
            await inter.send(
                "The link to the privacy policy is [https://github.com/rf20008/TheDiscordMathProblemBotRepo/blob/beta/TERMS_AND_CONDITIONS.md](here)"
            )
            return
        elif documentation_type == "terms_of_service":
            # TODO: softcode this in a config.json file
            await inter.send(
                "The link to the terms of service is here: [https://github.com/rf20008/TheDiscordMathProblemBotRepo/blob/beta/TERMS_AND_CONDITIONS.md](Terms of Service Link)"
            )
            return

            # with open("TERMS_AND_CONDITIONS.md") as file:
            #    await inter.send(
            #        embed=SuccessEmbed("".join([line for line in file]))
            #    )  # Concatenate the lines in the file + send them
        else:
            raise NotImplementedError(
                "This hasn't been implemented yet!"
            )

    @checks.has_privileges(blacklisted=False)
    @checks.trusted_users_only()
    @checks.is_not_blacklisted()
    @commands.cooldown(1, 1, commands.BucketType.user)
    @commands.slash_command(
        name="blacklist",
        description="Blacklist someone from the bot!",
        options=[
            disnake.Option(
                name="user",
                description="The user to blacklist",
                type=disnake.OptionType.user,
                required=True,
            )
        ],
    )
    async def blacklist(
            self: "MiscCommandsCog",
            inter: disnake.ApplicationCommandInteraction,
            user: typing.Union[disnake.User, disnake.Member],
    ):
        """/blacklist [user: user]
        Blacklist someone from the bot. You must be a trusted user to do this!
        There is a 1-second cooldown."""
        user_data = await self.cache.get_user_data(
            user_id=user.id,
            default=problems_module.UserData(
                user_id=user.id, trusted=False, blacklisted=False
            ),
        )
        if not user_data.blacklisted:
            bot.log.debug("Can't blacklist user; user already blacklisted")
            return await inter.send("Can't blacklist user; user already blacklisted")
        else:
            user_data.blacklisted = True
            try:
                await self.cache.update_user_data(user_id=user.id, new=user_data)
            except problems_module.MathProblemsModuleException:
                await self.cache.add_user_data(user_id=user.id, new=user_data)
            self.bot.log.info(f"Successfully blacklisted the user with id {user.id}")
            await inter.send("Successfully blacklisted the user!")

            # TODO: what do I do after a user gets blacklisted? Do I delete their data?

    @checks.trusted_users_only()
    @checks.is_not_blacklisted()
    @commands.cooldown(1, 1, commands.BucketType.user)
    @commands.slash_command(
        name="unblacklist",
        description="Remove someone's blacklist",
        options=[
            disnake.Option(
                name="user",
                description="The user to un-blacklist",
                type=disnake.OptionType.user,
                required=True,
            )
        ],
    )
    async def unblacklist(
            self: "MiscCommandsCog",
            inter: disnake.ApplicationCommandInteraction,
            user: typing.Union[disnake.User, disnake.Member],
    ):
        """/unblacklist [user: user]
        Remove a user's bot blacklist. You must be a trusted user to do this!
        There is a 1-second cooldown."""
        user_data = await self.cache.get_user_data(
            user_id=user.id,
            default=problems_module.UserData(
                user_id=user.id, trusted=False, blacklisted=False
            ),
        )
        if not user_data.blacklisted:
            bot.log.debug("Can't un-blacklist user; user not blacklisted")
            return await inter.send("Can't un-blacklist user; user not blacklisted")
        else:
            user_data.blacklisted = False
            try:
                await self.cache.update_user_data(user_id=user.id, new=user_data)
            except problems_module.MathProblemsModuleException:
                await self.cache.add_user_data(user_id=user.id, new=user_data)
            self.bot.log.info(f"Successfully un-blacklisted the user with id {user.id}")
            await inter.send("Successfully un-blacklisted the user!")

            # TODO: what do I do after a user gets blacklisted? Do I delete their data?

    @checks.guild_owners_or_trusted_users_only()
    @checks.is_not_blacklisted()
    @checks.guild_not_blacklisted()
    @commands.slash_command(description="Request for your guild's data to be deleted")
    async def request_guild_data_delete(
            self, inter: disnake.ApplicationCommandInteraction
    ):
        """/request_guild_data_delete

        Requests the deletion of the data stored with this bot associated with the guild.
        Only guild owners can run this. There is also a confirmation view to confirm.
        You will have 2 minutes to click a button, or nothing will happen!"""
        try:
            assert inter.guild is not None
            assert (
                    await self.bot.is_trusted(inter.author)
                    or inter.author.id == inter.guild.owner_id
            )
        except AssertionError:
            await inter.send("You don't have permission!")
            raise
        assert isinstance(inter.channel, CAN_SEND_MESSAGES_TO)
        view = GuildDataDeletionView(
            inter=inter, timeout=GUILD_DATA_DELETION_TIMEOUT, bot=self.bot
        )
        await inter.send(view=view)
        msg = await inter.original_message()
        try:
            _ = await bot.wait_for(
                "button_click",
                check=lambda i: i.author.id == inter.author.id,
                timeout=120,
            )
        except asyncio.TimeoutError:
            view.stop()
            for item in view.children:
                if not isinstance(item, disnake.ui.Item):
                    raise RuntimeError()
                if hasattr(item, "disabled"):
                    if not getattr(item, "disabled", False):
                        item.disabled = True

            await msg.edit(
                content="You didn't respond in time, so the view has now been closed"
                        + msg.content,  # noqa: E501
                view=view,
            )
            return await inter.channel.send("You didn't submit in time!")
        return

    @commands.slash_command(
        description="Compute the number of factors of y in x! where x>y and x and y are integers"
    )
    async def compute_num_factors_in_factorial(self, inter: disnake.ApplicationCommandInteraction, x: int, y: int):
        """/compute_num_factors_in_factorial [x: int] [y:int]
        Compute the number of factors of y in x! where x>y and x and y are positive integers. y must be a prime number!
        The formula (the sum of floor(x,y^k) for k from 1 to infinity) is used) or expre
        I'm probably not going to implement parsing arithmetic so don't tell me about it.
        We already have calculators and a lot of calculators already exist (including some on Discord),so I'm not going to implement one here right now."""
        # TODO: implement a version that can compute this when y is not prime, and some other math commands (but not too many)
        if not x > y:
            await inter.send(embed=ErrorEmbed("x is not larger than y!"))
            return
        if x <= 0 or y <= 0:
            await inter.send(embed=ErrorEmbed("x or y are negative."))
            return
        if y > TEN_BILLION:
            await inter.send(embed=ErrorEmbed("y is too big!"))
            return

        if not miller_robin_primality_test(y):
            await inter.send(embed=ErrorEmbed("y is composite."))
            return
        Y = mpf(y)
        X = mpf(x)
        numFactors = mpf(0)
        k = mpf(0)
        while True:
            k += 1
            numNewFactorsOfY = floor(X / Y ** k)
            if numNewFactorsOfY == 0:
                # Everything after will be 0 so we can stop computing here.
                break
            else:
                numFactors += numNewFactorsOfY
        await inter.send(embed=SuccessEmbed(f"There are {numFactors} factors of {y} in {x}!."))
        return


def setup(bot):
    bot.add_cog(MiscCommandsCog(bot))


def teardown(bot):
    bot.remove_cog("MiscCommandsCog")
