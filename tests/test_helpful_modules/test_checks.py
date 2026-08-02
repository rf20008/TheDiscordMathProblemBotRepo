"""
You can distribute any version of the Software created and distributed *before* 23:17:55.00 July 28, 2024 GMT-4
under the GNU General Public License version 3 or at your option, any  later option.
But versions of the code created and/or distributed *on or after* that date must be distributed
under the GNU *Affero* General Public License, version 3, or, at your option, any later version.

This file is part of TheDiscordMathProblemBotRepo

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

Author: Samuel Guo (64931063+rf20008@users.noreply.github.com)
"""

import pytest
from disnake.ext import commands

from helpful_modules.checks import *


class FakeInter:
    def __init__(self):
        self.author = type("U", (), {"id": 1, "mention": "@u"})()
        self.guild = type("G", (), {"owner_id": 1})()
        self.guild_id = 123
        self.data = type("D", (), {"name": "cmd"})()
        self.application_command = type("C", (), {"qualified_name": "cmd"})()
        self.filled_options = {}
        self.bot = None


def test_custom_check_passes():
    @custom_check(function=lambda inter: True)
    @commands.command()
    async def dummy(inter):
        return "ok"

    # Simulate invocation
    inter = FakeInter()
    assert dummy.checks[0](inter) is True


def test_custom_check_fails_with_exception():
    class MyError(Exception):
        pass

    @custom_check(
        function=lambda inter: False,
        exceptionToRaiseIfFailed=MyError("failed"),
    )
    @commands.command()
    async def dummy(inter):
        return "ok"

    inter = FakeInter()

    with pytest.raises(MyError):
        dummy.checks[0](inter)


def test_custom_check_receives_interaction():
    captured = {}

    def check_fn(inter):
        captured["value"] = inter.value
        return True

    @custom_check(function=check_fn)
    @commands.command()
    async def dummy(inter):
        return "ok"

    inter = type("FakeInter", (), {"value": 999})

    result = dummy.checks[0](inter)

    assert result is True
    assert captured["value"] == 999


@pytest.mark.asyncio
async def test_trusted_pass(monkeypatch):
    class Bot:
        async def is_trusted(self, user):
            return True

    inter = type("I", (), {"bot": Bot(), "author": type("U", (), {})()})()

    @trusted_users_only()
    @commands.command()
    async def cmd(inter):
        pass

    assert await cmd.checks[0](inter) is True


@pytest.mark.asyncio
async def test_trusted_fail(monkeypatch):
    class Bot:
        async def is_trusted(self, user):
            return False

    inter = type(
        "I", (), {"bot": Bot(), "author": type("U", (), {"mention": "@u"})()}
    )()

    @trusted_users_only()
    @commands.command()
    async def cmd(inter):
        pass

    with pytest.raises(NotTrustedUser):
        await cmd.checks[0](inter)


class FakeUserData:
    def __init__(self, deny=False):
        self._deny = deny
        self.denylist_reason = "spam"
        self.denylist_expiry = 9999999999

    def is_denylisted(self):
        return self._deny


@pytest.mark.asyncio
async def test_denylist_fail():
    class Cache:
        async def get_user_data(self, *a, **k):
            return FakeUserData(True)

    class Bot:
        cache = Cache()

        async def is_trusted(self, u):
            return False

    inter = type(
        "I", (), {"bot": Bot(), "author": type("U", (), {"id": 1, "mention": "@u"})()}
    )()

    @is_not_denylisted()
    @commands.command()
    async def cmd(inter):
        pass

    with pytest.raises(DenylistedException):
        await cmd.checks[0](inter)


@pytest.mark.asyncio
async def test_guild_denylisted_blocks():
    sent = {}

    class Bot:
        async def is_guild_denylisted(self, guild):
            return True

        async def notify_guild_on_guild_leave_because_guild_denylist(self, guild):
            sent["left"] = True

    class Guild:
        id = 1

    inter = type(
        "I",
        (),
        {
            "bot": Bot(),
            "guild": Guild(),
            "send": lambda *a, **k: sent.update({"msg": True}),
        },
    )()

    @guild_not_denylisted()
    @commands.command()
    async def cmd(inter):
        pass

    result = await cmd.checks[0](inter)

    assert result is False


@pytest.mark.asyncio
async def test_huge_number_rejected():
    inter = type(
        "I", (), {"filled_options": {"x": "999999999999999999999999999999999"}}
    )()

    @no_insanely_huge_numbers_check(max_num=10**10)
    @commands.command()
    async def cmd(inter):
        pass

    assert await cmd.checks[0](inter) is False


@pytest.mark.asyncio
async def test_audit_log_called():
    calls = {}

    class Audit:
        def add_to_log(self, **kwargs):
            calls["called"] = True

    class Bot:
        audit_log = Audit()

    inter = type(
        "I",
        (),
        {
            "bot": Bot(),
            "application_command": type("C", (), {"qualified_name": "x"})(),
            "guild_id": 1,
            "author": type("U", (), {"id": 1})(),
        },
    )()

    @audit_command_usage_check()
    @commands.command()
    async def cmd(inter):
        pass

    await cmd.checks[0](inter)

    assert calls["called"] is True


def run_all_tests():
    raise SystemExit(pytest.main([]))


if __name__ == "__main__":
    run_all_tests()
