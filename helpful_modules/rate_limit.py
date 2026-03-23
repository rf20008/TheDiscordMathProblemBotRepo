import disnake
import time
from dataclasses import dataclass
import typing
import copy
import traceback
import disnake.ext.commands
import sortedcontainers
from sortedcontainers import SortedList
from disnake.ext.commands import InvokableApplicationCommand

from .circular_deque import CircularDeque
from .problems_module import UserData, DenylistType
#from .custom_bot import TheDiscordMathProblemBot
from .threads_or_useful_funcs import first_true, last_true

ONE_SECOND = 1
ONE_MINUTE = 60
ONE_HOUR = 60 * ONE_MINUTE
ONE_DAY = 24 * ONE_HOUR
ONE_WEEK = 7 * ONE_DAY

GLOBAL_LIMIT_PER_MIN = 1000

usage_deque: CircularDeque = CircularDeque([])


def get_command_name(inter: disnake.ApplicationCommandInteraction):
    return (
        inter.application_command.qualified_name
        if hasattr(inter.application_command, "qualified_name")
        and isinstance(inter.application_command, InvokableApplicationCommand)
        else "Unknown command"
    )


async def autoban(
    user: disnake.User,
    bot: "TheDiscordMathProblemBot",
    duration: float = 30.0,
    reason: str = "You've been temporarily denylisted for using the bot too much recently. ",
):
    user_info: UserData = await bot.cache.get_user_data(user.id, default=None)
    bot.audit_log.add_log_entry(
        f"Autoban of {user.id} by {bot} for {duration} seconds because {reason}"
    )
    bot.dispatch("autoban_ratelimit_exceeded", user, duration, reason)
    if user_info.is_denylisted():
        return
    user_info.denylist(
        reason=reason,
        duration=duration,
        denylist_type=DenylistType.GENERAL_USER_DENYLIST,
        denylisting_moderator=str(bot.user.name),
    )
    await bot.cache.set_user_data(user.id, user_info)


def num_at_least_x(L: sortedcontainers.SortedList, x: float) -> int:
    return len(L) - L.bisect_left(x)


@dataclass
class RateLimit:
    unit: str  # human-readable name of unit
    limit: int  # maximum number of requests allowed in `per` seconds
    per: float  # duration of ratelimit (in seconds)

    def valid(self):
        return self.limit > 0 and self.per > 0


DEFAULT_GLOBAL_LIMIT = RateLimit(
    unit="minute", limit=GLOBAL_LIMIT_PER_MIN, per=ONE_MINUTE
)
DEFAULT_RATE_LIMITS = [
    RateLimit(unit="day", limit=1440, per=ONE_DAY),
    RateLimit(unit="hour", limit=250, per=ONE_HOUR),
    RateLimit(unit="minute", limit=15, per=ONE_MINUTE),
    RateLimit(unit="second", limit=5, per=ONE_SECOND),
]


class RateLimiter:  # todo: more rate limits
    global_deque: SortedList
    user_deque: dict[int, SortedList]

    def __init__(
        self,
        bot: "TheDiscordMathProblemBot",
        *,
        global_limit: RateLimit | None = None,
        user_limits: list[RateLimit] | None = None,
        does_user_bypass: typing.Callable[[int], bool] | None = None,
    ):
        from .custom_bot import TheDiscordMathProblemBot # avoid circular import
        if not isinstance(bot, TheDiscordMathProblemBot):
            raise TypeError("Bot must be of type TheDiscordMathProblemBot.")
        self.bot = bot
        if user_limits is None:
            user_limits = copy.deepcopy(DEFAULT_RATE_LIMITS)
        if global_limit is None:
            global_limit = copy.deepcopy(DEFAULT_GLOBAL_LIMIT)
        if not isinstance(user_limits, list) and not all(
            isinstance(limit, RateLimit) for limit in user_limits
        ):
            raise TypeError(
                "User limits must be of type list or tuple. Also, all its elements must be of type RateLimit."
            )
        if not all(limit.valid() for limit in user_limits):
            raise ValueError("User limits must all be valid.")
        self.user_limits = user_limits
        self.longest_limit = RateLimit(unit="none", limit=1 << 64 - 1, per=1e-300)
        for limit in user_limits:
            if limit.per > self.longest_limit.per:
                self.longest_limit = limit

        if not isinstance(global_limit, RateLimit) or not global_limit.valid():
            raise TypeError("Global limit must be valid a RateLimit.")
        self.global_limit = global_limit
        # if not isinstance(day_limit, int) or day_limit < 0:
        #    raise TypeError("Day limit must be positive and an integer.")
        # self.day_limit = day_limit
        # if not isinstance(hour_limit, int) or hour_limit < 0:
        #    raise TypeError("Hour limit must be positive and an integer.")
        # self.hour_limit = hour_limit
        # if not isinstance(minute_limit, int) or minute_limit < 0:
        #    raise TypeError("Minute limit must be positive and an integer.")
        # self.minute_limit = minute_limit
        # if not isinstance(seconds_limit, int) or seconds_limit < 0:
        #    raise TypeError("Second limit must be positive and an integer.")
        # self.seconds_limit = seconds_limit
        if does_user_bypass is not None and not callable(does_user_bypass):
            raise TypeError("does_user_bypass must be callable.")
        self.does_user_bypass = does_user_bypass
        self.global_deque = SortedList()
        self.user_deques = {}

    def get_list_for(self, user_id: int) -> SortedList:
        if user_id in self.user_deques:
            return self.user_deques[user_id]
        self.user_deques[user_id] = SortedList()
        return self.user_deques[user_id]

    async def will_bypass(self, user_id: int) -> bool:
        if self.does_user_bypass is None:
            return False  # nobody bypasses if there is no bypass-function
        return await self.maybe_await(self.does_user_bypass, user_id)

    async def maybe_await(self, func, *args, **kwargs):
        result = func(*args, **kwargs)
        if hasattr(result, "__await__"):
            return await result
        return result

    async def __call__(self, inter) -> str:
        """Return whether inter causes the user to be denylisted. If False, means"""
        from .custom_bot import TheDiscordMathProblemBot # avoid circular import
        author_id = inter.author.id
        cur_time = time.time()
        if await self.will_bypass(author_id):
            return ""
        if not isinstance(inter.bot, TheDiscordMathProblemBot):
            await inter.send("The bot ran into an error.")
            raise TypeError()
        command_name = get_command_name(inter)
        inter.bot.audit_log.add_log_entry(
            "Someone used a command! We are checking the rate limit",
            extra_info={
                "user": inter.author.id,
                "user_mention": inter.author.mention,
                "guild_id": inter.guild_id,
                "guild_name": inter.guild.name if inter.guild else "Not in a guild",
                "channel": inter.channel.id,
                "command_name": command_name,
                "arguments": inter.options,
            },
        )
        self.global_deque.add(cur_time)
        while (
            len(self.global_deque) > 0
            and self.global_deque[0] < cur_time - self.global_limit.per
        ):
            self.global_deque.pop(0)

        if len(self.global_deque) > self.global_limit.limit:
            return "The bot is currently experiencing a high volume of commands. Please try again later."
        user_deque = self.get_list_for(inter.author.id)
        user_deque.add(cur_time)

        while len(user_deque) > 0 and user_deque[0] < cur_time - self.longest_limit.per:
            user_deque.pop(0)
        self.user_deques[inter.author.id] = user_deque
        if len(user_deque) > self.longest_limit.limit:
            await autoban(
                user=inter.author,
                bot=inter.bot,
                duration=float(ONE_DAY),
                reason=(
                    f"You have been automatically denylisted for using the bot {self.longest_limit.limit} times in a {self.longest_limit.unit}. "
                    "This denylist is appealable, and we hope that your appeal will be reviewed, but beware: \n\n"
                    "Warning 1: It is **NOT** guaranteed that your appeal will be even read. We hope that we can read your appeal,"
                    "but I am a busy high school student and I do not have the time to read every appeal. \n"
                    "Warning 2: I do not check my appeal box often. It may be faster to informally appeal in my DMs.\n"
                    "Warning 3: If you exceed 1440 requests within a 24-hour period, you will be autobanned. \n\n"
                    "Your past usage (before the appeal) will still be counted when re-evaluating your rate limit status. "
                    "Even if your appeal is approved, the autoban will be automatically reimposed if you continue to exceed the limit."
                ),
            )

            return "You have been denylisted for using the bot too many times today. Please try again later. This denylist is appealable, but you will be automatically denylisted again if you appeal."
        for limit in self.user_limits:
            times_last_per = num_at_least_x(user_deque, cur_time - limit.per)
            if times_last_per >= limit.limit:
                return f"You've used the bot too many times in the last {limit.unit}. Please try again later."
        return ""


#global_rate_limiter = RateLimiter()
#appeal_rate_limiter = RateLimiter()
global_rate_limiter = None
appeal_rate_limiter = None

class RateLimitedException(disnake.ext.commands.CheckFailure):
    """Raised when someone tries to run a command, but they're rate limited"""

    pass


def rate_limit_check():
    async def predicate(inter: disnake.ApplicationCommandInteraction):
        from .custom_bot import TheDiscordMathProblemBot
        if not isinstance(inter.bot, TheDiscordMathProblemBot):
            await inter.send("The bot ran into an error.")
            raise TypeError()

        cur_time = time.time()
        command_name = (
            inter.application_command.qualified_name
            if hasattr(inter.application_command, "qualified_name")
            and isinstance(inter.application_command, InvokableApplicationCommand)
            else "Unknown command"
        )
        try:
            # log the checking rate limit
            inter.bot.audit_log.add_log_entry(
                "Someone used a command! We are checking the rate limit",
                extra_info={
                    "user": inter.author.id,
                    "user_mention": inter.author.mention,
                    "guild_id": inter.guild_id,
                    "guild_name": inter.guild.name if inter.guild else "No Name",
                    "channel": inter.channel.id,
                    "command_name": command_name,
                    "arguments": inter.options,
                },
            )
        except KeyboardInterrupt:
            exit()
        except Exception as e:
            await inter.send(
                f"The bot ran into an error.\n{'\n'.join(traceback.format_exception(e))}"
            )
            raise e
        if "appeal" not in command_name:
            global_rate_limited_msg = await inter.bot.global_rate_limiter(inter)
            if global_rate_limited_msg:
                raise RateLimitedException(str(global_rate_limited_msg))  # type: ignore
        else:
            appeal_rate_limited_msg = await inter.bot.appeal_rate_limiter(inter)
            if appeal_rate_limited_msg:
                raise RateLimitedException(appeal_rate_limited_msg)  # type: ignore
        return True

    return predicate
