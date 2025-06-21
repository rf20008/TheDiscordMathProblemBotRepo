import disnake
import time
import typing
import traceback
import disnake.ext.commands
from disnake.ext.commands import InvokableApplicationCommand

from .circular_deque import CircularDeque
from .problems_module import UserData, DenylistType
from .custom_bot import TheDiscordMathProblemBot
from .threads_or_useful_funcs import first_true, last_true
ONE_MINUTE = 60
ONE_HOUR = 60 * ONE_MINUTE
ONE_DAY = 24 * ONE_HOUR
ONE_WEEK = 7 * ONE_DAY
DAY_LIMIT = 1440
HOUR_LIMIT = 250
MINUTE_LIMIT = 15
SECOND_LIMIT = 5
LIMITS = {
    "day": 1440,
    "minute": 15,
    "hour": 250,
    "second": 5,
}
GLOBAL_LIMIT_PER_MIN = 1000

usage_deque: CircularDeque = CircularDeque([])
DEQUES: dict[int, CircularDeque] = {}
def get_command_name(inter: disnake.ApplicationCommandInteraction):
    return inter.application_command.qualified_name if hasattr(inter.application_command, "qualified_name") and isinstance(inter.application_command, InvokableApplicationCommand) else "Unknown command"
async def autoban(user: disnake.User, bot: TheDiscordMathProblemBot, duration: float = 30.0, reason: str = "You've been temporarily denylisted for using the bot too much recently. "):
    user_info: UserData = await bot.cache.get_user_data(user.id, default = None)
    bot.audit_log.add_log_entry(f"Autoban of {user.id} by {bot} for {duration} seconds because {reason}")
    if user_info.is_denylisted():
        return
    user_info.denylist(
        reason=reason,
        duration=duration,
        denylist_type=DenylistType.GENERAL_USER_DENYLIST,
        denylisting_moderator=str(bot.user.name),
    )
    await bot.cache.set_user_data(user.id, user_info)


@dataclasses.dataclass
class RateLimit:
    unit: str
    limit: int
    per: int


class RateLimiter: # todo: more rate limits
    def __init__(
            self,
            bot: TheDiscordMathProblemBot,
            *,

            global_limit: int = GLOBAL_LIMIT_PER_MIN,
            day_limit: int = DAY_LIMIT,
            hour_limit: int = HOUR_LIMIT,
            minute_limit: int = MINUTE_LIMIT,
            seconds_limit: int = SECOND_LIMIT,
            does_user_bypass: typing.Callable[[int], bool] | None = None
    ):
        if not isinstance(bot, TheDiscordMathProblemBot):
            raise TypeError("Bot must be of type TheDiscordMathProblemBot.")
        self.bot = bot
        if not isinstance(global_limit, int) or global_limit < 0:
            raise TypeError("Global limit must be positive and an integer.")
        self.global_limit = global_limit
        if not isinstance(day_limit, int) or day_limit < 0:
            raise TypeError("Day limit must be positive and an integer.")
        self.day_limit = day_limit
        if not isinstance(hour_limit, int) or hour_limit < 0:
            raise TypeError("Hour limit must be positive and an integer.")
        self.hour_limit = hour_limit
        if not isinstance(minute_limit, int) or minute_limit < 0:
            raise TypeError("Minute limit must be positive and an integer.")
        self.minute_limit = minute_limit
        if not isinstance(seconds_limit, int) or seconds_limit < 0:
            raise TypeError("Second limit must be positive and an integer.")
        self.seconds_limit = seconds_limit
        if does_user_bypass is None:
            does_user_bypass = lambda user: False # nobody bypasses by default if
        if not callable(does_user_bypass):
            raise TypeError("does_user_bypass must be callable.")
        self.does_user_bypass = does_user_bypass
        self.global_deque = CircularDeque([])
        self.user_deques = CircularDeque([])

    async def maybe_await(self, func, *args, **kwargs):
        result = func(*args, **kwargs)
        if hasattr(result, '__await__'):
            return await result
        return result
    async def __call__(self, inter):
        """Return whether inter causes the user to be denylisted. If False, means """
        author_id = inter.author.id
        cur_time = time.time()
        if await self.does_user_bypass(author_id):
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
                "guild_name": inter.guild.name if inter.guild else "No Name",
                "channel": inter.channel.id,
                "command_name": command_name,
                "arguments": inter.options
            }
        )
        self.global_deque.append(cur_time)
        while not self.global_deque.empty() and self.global_deque.left < cur_time - ONE_MINUTE:
            self.global_deque.popleft()
        if author_id not in self.user_deques:
            self.user_deques[author_id] = CircularDeque([cur_time])
        else:
            self.user_deques[author_id].append_right(cur_time)

        if len(self.global_deque) > GLOBAL_LIMIT_PER_MIN:
            return "The bot is currently experiencing a high volume of commands. Please try again later."
        if len(self.user_deques[inter.author.id]) > self.day_limit:
            await autoban(
                user=inter.author,
                bot=inter.bot,
                duration = float(ONE_DAY),
                reason = (
                    f"You have been automatically denylisted for using the bot {LIMITS['day']} times in a day. "
                    "This denylist is appealable, and we hope that your appeal will be reviewed, but beware: \n\n"
                    "Warning 1: It is **NOT** guaranteed that your appeal will be even read. We hope that we can read your appeal,"
                    "but I am a busy high school student and I do not have the time to read every appeal. \n"
                    "Warning 2: I do not check my appeal box often. It may be faster to informally appeal in my DMs.\n"
                    "Warning 3: If you exceed 1440 requests within a 24-hour period, you will be autobanned. \n\n"
                    "Your past usage (before the appeal) will still be counted when re-evaluating your rate limit status. "
                    "Even if your appeal is approved, the autoban will be automatically reimposed if you continue to exceed the limit."
                )
            )

            return ("You have been denylisted for using the bot too many times today. Please try again later. "
                   "This denylist is appealable, but you will be automatically denylisted again if you appeal.")
        for unit, duration in (("second", 1), ("minute", ONE_MINUTE), ("hour", ONE_HOUR), ("day", ONE_DAY)):
            times_last_unit = len(DEQUES[inter.author.id]) - last_true(0, len(DEQUES[inter.author.id]), lambda idx: DEQUES[inter.author.id][idx]  <= cur_time - duration)
            if times_last_unit > LIMITS[unit]:
                return f"You've used the bot too many times in the last {unit}. Please try again later."
        return ""


global_rate_limiter = RateLimiter()
appeal_rate_limiter = RateLimiter()
class RateLimitedException(disnake.ext.commands.CheckFailure):
    """Raised when someone tries to run a command but they're rate limit"""
    pass
def rate_limit_check():
    async def predicate(inter: disnake.ApplicationCommandInteraction):
        if not isinstance(inter.bot, TheDiscordMathProblemBot):
            await inter.send("The bot ran into an error.")
            raise TypeError()

        cur_time = time.time()
        BEFORE = cur_time - ONE_DAY
        command_name = inter.application_command.qualified_name if hasattr(inter.application_command, "qualified_name") and isinstance(inter.application_command, InvokableApplicationCommand) else "Unknown command"
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
                    "arguments": inter.options
                }
            )
        except KeyboardInterrupt:
            exit()
        except Exception as e:
            await inter.send(f"THe bot ran into an error.\n{'\n'.join(traceback.format_exception(e))}")
            raise e
        if "appeal" not in command_name:
            global_rate_limited = global_rate_limiter(inter)
            if global_rate_limited:
                raise RateLimitedException(global_rate_limited)
        else:
            appeal_rate_limited = appeal_rate_limiter(inter)
            if appeal_rate_limited:
                raise RateLimitedException(appeal_rate_limited)
        return True
    return predicate