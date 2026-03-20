"""You can distribute any version of the Software created and distributed *before* 23:17:55.00 July 28, 2024 GMT-4
under the GNU General Public License version 3 or at your option, any  later option.
But versions of the code created and/or distributed *on or after* that date must be distributed
under the GNU *Affero* General Public License, version 3, or, at your option, any later version.

The Discord Math Problem Bot Repo - Custom Bot

This program is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public License
as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
See the GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License along with this program.
If not, see <https://www.gnu.org/licenses/>.

Author: Samuel Guo (64931063+rf20008@users.noreply.github.com)"""

import asyncio
import inspect
import logging
import math
import random
import time
import typing
import warnings
from functools import partial, wraps
from types import FunctionType
import datetime

import disnake
import traceback
import sys
import os
from sys import stderr, stdout
from disnake.ext import commands, tasks

import helpful_modules
from helpful_modules import problems_module
from helpful_modules.base_on_error import base_on_error
from helpful_modules.constants_loader import BotConstants
from helpful_modules.problems_module import GuildData, AppealQuestion
from helpful_modules.problems_module import MathProblemCache, RedisCache
from helpful_modules.restart_the_bot import RestartTheBot
from helpful_modules.save_files import FileSaver
from helpful_modules.file_log import AuditLog

from ._error_logging import log_error
from .errors import (
    AppealViewChannelCantSeeException,
    AppealViewMessageNotFoundException,
    NotInSupportServerWarning,
)
from .FileDictionaryReader import AsyncFileDict
from .message_queue import MessageQueue
from .StatsTrack import CommandStats, CommandUsage, StreamWrapperStorer
from .threads_or_useful_funcs import modified_async_wrap

print(os.getpid())
WAIT = True
TIME_TO_WAIT = 25
ANNOUNCEMENTS_CHANNEL = 960725589260652588
TIMEOUT = 0.5
SUPPORT_SERVER_GUILD_ID = 873741593159540747
APPEALS_CHANNEL_ID = 944693665899630592


class TheDiscordMathProblemBot(disnake.ext.commands.Bot):
    is_closing: bool
    file_saver: FileSaver | None
    appeal_questions: dict[str, list[AppealQuestion]]
    tasks: list[str : disnake.ext.tasks.Loop]
    config_json: AsyncFileDict
    trusted_users: list[int] | None
    cache: MathProblemCache | RedisCache
    constants: BotConstants
    audit_log: AuditLog
    restart: RestartTheBot
    time_started: float
    total_stats: CommandStats | None
    queue: MessageQueue
    closing_things: list[typing.Callable]
    rate_limiters: list["RateLimiters"]

    def __init__(self, *args, **kwargs):
        self.is_closing = False
        self.file_saver = None
        self.appeal_questions = {}
        self.tasks = kwargs.pop("tasks")
        self.audit_log = kwargs.pop("audit_log")
        self.config_json = AsyncFileDict("config.json")
        self.storer = kwargs.pop("storer")
        self.trusted_users = kwargs.pop("trusted_users")
        cache = kwargs.pop("cache")
        self.cache = (
            cache
            if isinstance(cache, helpful_modules.problems_module.MathProblemCache)
            or isinstance(helpful_modules.problems_module.RedisCache)
            else False
        )
        if self.cache is False:
            raise TypeError("Not of type MathProblemCache")
        # print(self.cache)
        self.constants = (
            kwargs.pop("constants")
            if isinstance(kwargs.get("constants"), BotConstants)
            else False
        )
        if self.constants is False:
            raise TypeError("Constants is not a BotConstants object")
        super().__init__(*args, **kwargs)

        assert isinstance(self.tasks, dict)
        self.restart = RestartTheBot(self)  # TODO: fix the restartTheBot class
        for task in self.tasks.values():
            assert isinstance(task, disnake.ext.tasks.Loop)
            task.start()  # TODO: add being able to change it
        self.timeStarted = float("inf")
        self.total_stats = None
        self.this_session = None
        self.queue = MessageQueue()
        self.initialize_stats()
        # self.trusted_users = kwargs.get("trusted_users", None)
        # if not self.trusted_users and self.trusted_users != []:
        #    raise TypeError("trusted_users was not found")
        # self.denylisted_users = kwargs.get("denylisted_users", [])
        self.closing_things = []
        self.rate_limiters = []

    @property
    def support_server(self):
        guild = self.get_guild(SUPPORT_SERVER_GUILD_ID)
        if not guild:
            warnings.warn(
                "The bot is not in the support server",
                stacklevel=-1,
                category=NotInSupportServerWarning,
            )
        return guild

    def get_task(self, task_name):
        return self.tasks[task_name]

    def start_tasks(self):
        for task in self.tasks.values():
            task.start()

    @property
    def log(self):
        return logging.getLogger(__name__)

    @property
    def uptime(self):
        return time.time() - self.timeStarted  # TODO: more accurate time + timestamp

    async def on_ready(self):
        self.timeStarted = time.time()
        self.app_info = await self.application_info()
        if self.app_info.team:
            self.owner_ids = {member.id for member in self.app_info.team.members}
        else:
            self.owner_id = self.app_info.owner

        """Ran when the disnake library detects that the bot is ready"""
        app_info = await self.application_info()
        print("The bot is now ready!")
        print(f"I connected as {self.user.name}#{self.user.discriminator}.")
        print(
            f"My owner id is {self.owner_id if self.owner_id is not None else app_info.owner.id}!"
        )
        print(
            f"I am able to connect {self.session_start_limit.total} times before being prohibited today."
        )
        if self.owner_id is None and app_info.owner.id is not None:
            self.owner_id = app_info.owner.id

        print(f"My owner ids are {self.owner_ids}")
        try:
            await self.register_appeal_views()
        except BaseExceptionGroup as begroup:
            self.log.exception(
                "Exceptions happened while trying to register appeal views:", begroup
            )
            await log_error(begroup)
        except Exception as e:
            self.log.exception(
                "The following exception happened while trying to register appeal views:",
                e,
            )
            await log_error(e)

    async def owns_and_is_trusted(self, user: disnake.User):
        return await self.is_trusted(user) and await self.is_owner(user)

    def add_task(self, task):
        assert isinstance(task, disnake.ext.tasks.Loop)
        self.tasks.append(task)
        task.start()

    async def close(self):

        try:

            self.is_closing = True
            await self.audit_log.clear_buffer()
            await self.queue.stop(
                msg="Bot is closing",
                empty=True,
                act=True,
                timeout=TIMEOUT,
                limit=int(math.floor(TIME_TO_WAIT / TIMEOUT)),
                delete_undone_tasks=True,
            )
            await self.maybe_send_closing_message()
            if WAIT:
                await asyncio.sleep(TIME_TO_WAIT)
            await self.queue.empty(act=False)
            for cog_name in list(self.cogs):
                self.remove_cog(cog_name)
            for extension in list(self.extensions):
                self.unload_extension(extension)
            for task in self.tasks:
                task.stop()
            await asyncio.sleep(5)
            self.storer.close()
            await asyncio.gather(*self.closing_things)
        except Exception as e:
            print(f"An exception of {e} happened while the bot was trying to close.")
            self.log.exception(e)
            await log_error(e)
            await asyncio.sleep(3)
        except KeyboardInterrupt as err:
            print(f"An exception of {err} happened while the bot was trying to close.")
            self.log.exception(err)
            await log_error(err)
            await asyncio.sleep(3)
        finally:
            await super().close()
            self.is_closing = False

    async def maybe_send_closing_message(self):
        guild = self.support_server
        channel = guild.get_channel(ANNOUNCEMENTS_CHANNEL)
        await channel.send(
            f"This process will stop functioning in {TIME_TO_WAIT} seconds (if waiting is enabled)"
        )

    def add_closing_thing(self, thing: FunctionType) -> None:
        if asyncio.iscoroutinefunction(thing):
            self.closing_things.append(thing())

        elif inspect.isawaitable(thing):
            self.closing_things.append(thing)

        else:
            raise TypeError()

    async def is_trusted(
        self, user: typing.Union[disnake.User, disnake.Member]
    ) -> bool:
        return await self.is_trusted_by_user_id(user.id)

    async def is_denylisted_from_verification_code_system_by_user_id(
        self, user_id: int
    ) -> bool:
        data = await self.cache.get_user_data(
            user=user_id, default=problems_module.UserData.default(user_id)
        )
        return data.verification_code_denylist.is_denylisted()

    async def is_denylisted_from_verification_code_system(
        self, user: typing.Union[disnake.User, disnake.Member]
    ):
        return await self.is_denylisted_from_verification_code_system_by_user_id(
            user.id
        )

    async def is_trusted_by_user_id(self, user_id: int) -> bool:
        try:
            data = await self.cache.get_user_data(
                user_id=user_id,
                default=problems_module.UserData(
                    user_id=user_id, trusted=False, denylisted=False
                ),
            )
        except Exception as e:
            print(
                "An error occured while trying to find whether someone was trusted:",
                "".join(traceback.format_exception(e)),
            )
            self.log.exception(e)
            raise
        return data.trusted

    async def is_denylisted_by_user_id(self, user_id: int) -> bool:
        data = await self.cache.get_user_data(
            user_id=user_id,
            default=problems_module.UserData(
                user_id=user_id, trusted=False, denylisted=False
            ),
        )
        return data.is_denylisted()

    async def mods_can_view(self, channel: disnake.abc.Messageable):
        guild_data: problems_module.GuildData = await self.cache.get_guild_data(
            guild_id=channel.guild.id
        )
        for role_id in guild_data.mods_check.roles_allowed:
            role: disnake.Role = channel.guild.get_role(role_id)
            if channel.permissions_for(role).view_channel:
                return True
        return False

    async def is_user_denylisted(
        self, user: typing.Union[disnake.User, disnake.Member]
    ) -> bool:
        return await self.is_denylisted_by_guild_id(user.id)

    async def is_guild_denylisted(self, guild: disnake.Guild) -> bool:
        return await self.is_denylisted_by_guild_id(guild.id)

    async def is_denylisted_by_guild_id(self, guild_id: int) -> bool:
        data: GuildData = await self.cache.get_guild_data(
            guild_id=guild_id,
            default=GuildData.default(guild_id=guild_id),
        )
        return data.is_denylisted()

    async def notify_guild_on_guild_leave_because_guild_denylist(
        self, guild: disnake.Guild
    ) -> None:
        """
        Notify the guild about the bot leaving due to being denylisted. If suitable channels are available,
        send a notification message and then leave the guild. If no suitable channels are available, directly
        leave the guild without sending a notification.

        Args:
            guild (disnake.Guild): The guild from which the bot is leaving due to being denylisted.

        Raises:
            RuntimeError: If the guild is not actually denylisted.
        """
        guild_data = await self.cache.get_guild_data(
            guild_id=guild.id, default=GuildData.default(guild_id=guild.id)
        )
        if not guild_data.is_denylisted():
            raise RuntimeError("The guild isn't denylisted!")

        me: disnake.Member = guild.me

        # Function to check if a channel can be used for sending messages
        def can_send_messages(channel):
            return (
                isinstance(channel, disnake.abc.Messageable)
                and channel.permissions_for(me).send_messages
            )

        # Get all channels where the bot can send messages
        channels_that_we_could_send_to = list(filter(can_send_messages, guild.channels))

        if not channels_that_we_could_send_to:
            await guild.leave()
            return

        everyone_role = guild.get_role(guild.id)

        # Function to check if everyone can view the channel
        def everyone_can_view(channel):
            return channel.permissions_for(everyone_role).view_channel

        # Get channels visible to everyone
        channels_that_everyone_can_see = list(
            filter(everyone_can_view, channels_that_we_could_send_to)
        )

        if channels_that_everyone_can_see:
            channel_to_send_to = random.choice(channels_that_everyone_can_see)
        else:
            # Function to check if mods can view the channel

            # Get channels visible to moderators
            channels_that_mods_can_see = [
                channel
                for channel in channels_that_we_could_send_to
                if await self.mods_can_view(channel)
            ]

            if channels_that_mods_can_see:
                channel_to_send_to = random.choice(channels_that_mods_can_see)
            else:
                # If no suitable channels found, choose randomly from all channels
                channel_to_send_to = random.choice(channels_that_we_could_send_to)
        if guild_data.denylist_reason == float("inf"):
            until_str = "indefinitely"
        else:
            denylist_dt = disnake.utils.format_dt(guild_data, "R")
            if guild.denylist_expiry < time.time():
                until_str = f"in the past (since it expired {denylist_dt})"
            else:
                until_str = f"until {denylist_dt}"
        await channel_to_send_to.send(
            f"""I have left the guild because the guild is denylisted, under my terms and conditions.
            However, I'm available under the GPL. My source code is at {self.constants.SOURCE_CODE_LINK}, so you could self-host the bot if you wish.
            The reason this guild has been denylisted is {guild_data.denylist_reason} and lasts {until_str}
            """
        )
        await guild.leave()

    # async def on_application_command(self, inter: disnake.ApplicationCommandInteraction):
    #    await super().on_application_command(inter)
    #    if await self.is_guild_denylisted(inter.guild):
    #        await inter.send("This command has been executed in a b")
    #       await self.notify_guild_on_guild_leave_because_guild_denylist(inter.guild)

    def task(
        self,
    ) -> typing.Callable[
        [typing.Callable[[typing.Any], typing.Any], typing.Any],
        typing.Callable[[typing.Any], typing.Any],
    ]:
        """Add a task to my internal list of tasks + return it  (this is a decorator :-))"""

        def decorator(_self, func: FunctionType, *args, **kwargs):
            task: tasks.Loop(func=func, *args, **kwargs)
            _self.tasks.append(task)
            return func

        return decorator

    def closing_task(self):
        """Add a closing task to my internal list of closing tasks"""

        def decorator(_self, func: FunctionType):
            if isinstance(func, FunctionType):
                _self.closing_things.append(modified_async_wrap(func))
                return func
            elif inspect.isawaitable(func):
                _self.closing_things.append(func)
                return func
            raise TypeError("func is not awaitable!!")

        return decorator

    async def save_stats(self):
        await self.storer.writeStats(self.total_stats)

    def initialize_stats(self):
        self.total_stats = self.storer.return_stats()
        self.this_session = CommandStats(usages=[], unique_users=set(), total_cmds=0)

    async def is_owner(self, user: disnake.User) -> bool:
        """Helper function to determine whether user qualifies as an owner"""
        # print("Is owner: ", await self.is_owner(user))
        # print(await self.fetch_user(1259194910465331274))
        # print(self.owner_id)
        if self.owner_ids:
            return user.id in self.owner_ids
        elif self.owner_id:
            return user.id == self.owner_id
        else:
            try:
                app = await self.application_info()  # type: ignore
                if app.team:
                    self.owners = set(app.team.members)
                    self.owner_ids = ids = {m.id for m in app.team.members}
                    return user.id in ids
                else:
                    self.owner = app.owner
                    self.owner_id = owner_id = app.owner.id
                    return user.id == owner_id

            except disnake.HTTPException as he:
                await log_error(he)
                self.log.exception(
                    "An HTTP error happened while trying to know whether {user} owns this bot: ",
                    he,
                )
                raise
            except Exception as e:

                await log_error(e)
                self.log.exception(
                    "An error happened while trying to know whether {user} owns this bot: ",
                    e,
                )
                raise e

    async def register_appeal_views(self):
        """
        Fetches and registers appeal views from the appeals channel.

        This function iterates over all appeal view information stored in cache,
        attempts to fetch corresponding messages either from recent history or by
        fetching them directly if not found in history. It then adds the retrieved
        message views to the UI.

        Raises:
            BaseExceptionGroup: If any errors occur during the fetching or registration process.

        Notes:
            - Uses Discord API to fetch messages and handle exceptions like NotFound or Forbidden.
            - Logs errors encountered during message retrieval and view registration.
        """
        # Get the appeals channel
        appeals_channel = self.appeals_channel
        try:
            all_infos = self.cache.get_all_appeal_view_infos()
        except problems_module.AppealViewInfoNotFound:
            return  # there aren't any appeal view infos
        # Fetch recent message history and store in a dictionary for quick lookup
        history = {
            msg.id: msg for msg in await appeals_channel.history(limit=200).flatten()
        }

        # List to store any errors encountered
        errors = []

        # Iterate over all appeal view infos stored in cache

        try:
            async for appeal_view in all_infos:
                msg = None
                try:
                    # Check if the message ID exists in the fetched history
                    msg = history.get(appeal_view.message_id)

                    # If the message is not found in history, fetch it
                    if msg is None:
                        msg = await appeals_channel.fetch_message(
                            appeal_view.message_id
                        )

                # Handle exceptions if message is not found or access is forbidden
                except disnake.NotFound as nf:
                    # we'll try to delete this appeal
                    await self.cache.del_appeal_view_info(appeal_view.message_id)
                    continue

                except disnake.Forbidden as forb:
                    err = AppealViewChannelCantSeeException(
                        f"I can't see #appeals; I can't see the appeal with message {appeal_view.message_id}"
                    )
                    err.__cause__ = forb
                    errors.append(forb)

                # Catch any other unexpected exceptions
                except BaseException as be:
                    errors.append(be)

                # If message is still None, log an error
                if msg is None:
                    errors.append(
                        AppealViewMessageNotFoundException(
                            f"Appeal message for the appeal {appeal_view} is not found; maybe it's not in the appeals channel"
                        )
                    )
                view = disnake.ui.View.from_message(msg)
                view.user_id = appeal_view.user_id
                view.guild_id = appeal_view.guild_id
                view.message_id = appeal_view.message_id
                view.cache = self.cache
                view.pages = appeal_view.pages
                self.add_view(view, msg.id)
        except problems_module.AppealViewInfoNotFound as avinf:
            return  # there are no appeal view infos
            # Add the view from the message to the UI

        # Raise an exception if any errors occurred during the process
        if errors:
            raise BaseExceptionGroup("Appeal fetching failed!!!!", errors)

    @property
    def appeals_channel(self) -> disnake.abc.Messageable:
        return self.support_server.get_channel(APPEALS_CHANNEL_ID)

    async def on_guild_join(self, guild):
        """Ran when the bot joins a guild!"""
        if guild.id is None:  # Should never happen
            raise Exception("Uh oh!")  # This is probably causing the bot to do stuff

        if await self.is_guild_denylisted(guild):
            await self.notify_guild_on_guild_leave_because_guild_denylist(guild)
            if self.get_guild(guild.id) is not None:
                await self.get_guild(guild.id).leave()
            # await guild.leave()  # This will mess up stuff
            # print("Oh no")
            # raise RuntimeError(
            #     "Oh no..... there is a guild with id None... this will mess up the bot!")
            #  # Make sure that a guild with id _global doesn't mess up stuff

    async def on_guild_remove(self, guild):
        await self.cache.remove_all_by_guild_id(
            guild.id
        )  # Remove all guild-related stuff

    async def on_slash_command_error(self, inter, error):
        """Function called when a slash command errors, which will inevitably happen. All the functionality was moved to base_on_error :-)"""
        # print the traceback to the file
        if isinstance(error, KeyboardInterrupt):
            raise error
        try:
            dict_args = await base_on_error(inter, error)
        except Exception as e:
            print(traceback.format_exception(e))
            raise e

        # print(dict_args)
        try:
            await inter.send(**dict_args)
            return
        except BaseException as be:
            await log_error(be)
            # os._exit(1)
        try:
            if inter.response.is_done():
                await inter.followup.send(**dict_args)
            else:
                await inter.response.send_message(**dict_args)
        except AttributeError as err:
            print(error, err)
            await log_error(error, f"error_logs/{str(datetime.datetime.now())}")
            await inter.send(
                "An error occurred, and the error message couldn't be sent. However, it has been saved!"
            )

            raise ExceptionGroup(error, err)

    async def on_error(self, event, *args, **kwargs):
        print(f"Error in {event}... uh oh", file=stderr)
        error = sys.exc_info()
        # print the traceback to the file
        print(
            "\n".join(traceback.format_exception(*error)),
            file=stderr,
        )

        error_traceback_as_obj = "\n".join(traceback.format_exception(*error))
        # Log the error?
        await log_error(error[1])
        # We don't have an interaction/context, so I can't tell the user that an error happened
        print("Oh no! An exception occurred!", flush=True, file=stdout)

        print(error_traceback_as_obj, flush=True, file=stdout)

    async def on_connect(self):
        """Run when the bot connects"""

        print("The bot has connected to Discord successfully.")
        await asyncio.sleep(0.5)
        self.get_cog("HelpCog").update_cached_command_dict()
        await self.change_presence(
            status=disnake.Status.idle,
        )
        self.log.debug(
            "Deleting data from guilds the bot was kicked from while it was offline"
        )
        bot_guild_ids = set(guild.id for guild in self.guilds) # we make it a set because checking membership in a set is O(1)
        # The guild_ids of the guilds that the bot is in
        for guild_id in await self.cache.get_guilds():
            # Obtain all guilds the cache stores data (will need to be upgraded.)
            if guild_id not in bot_guild_ids:  # It's not in!
                if guild_id is None:  # Don't delete global problems
                    continue
                self.log.debug("The bot is deleting data from a guild it has left.")
                await self.cache.delete_all_by_guild_id(guild_id)  # Delete the data
