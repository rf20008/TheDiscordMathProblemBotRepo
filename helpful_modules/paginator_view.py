"""
This file is part of The Discord Math Problem Bot Repo

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

Author: Samuel Guo (64931063+rf20008@users.noreply.github.com)
"""
import asyncio

import disnake
from .my_modals import MyModal
from .custom_embeds import ErrorEmbed
import os
from .checks import always_succeeding_check_unwrapped
from typing import List

class PaginatorView(disnake.ui.View):
    user_id: int
    page_num: int
    pages: list[str]

    def __init__(self, user_id: int, pages: list[str], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_id = user_id
        self.pages = pages
        self.page_num = 0

    @classmethod
    def paginate(cls, user_id: int, text: str, max_page_length: int = 1500, **kwargs) -> 'PaginatorView':
        pages = cls.break_into_pages(text, max_page_length)
        return cls(user_id, pages, **kwargs)

    @staticmethod
    def break_into_pages(text: str, max_page_length: int = 1500, *, breaking_chars: str = " .!?-,:;-\n\t") -> List[str]:
        """
        Breaks a long text into smaller pages suitable for pagination.

        Args:
            text (str): The input text to be paginated.
            max_page_length (int, optional): The maximum length of each page. Defaults to 1500.
            breaking_chars (str, optional): Characters used for breaking the text into tokens. Defaults to " .!?\\n".

        Returns:
            list[str]: A list of pages, each containing a portion of the input text.
        """
        if not isinstance(text, str):
            raise TypeError("Expected 'text' to be a string.")
        if not isinstance(max_page_length, int):
            raise TypeError("Expected 'max_page_length' to be an integer.")
        if not isinstance(breaking_chars, str):
            raise TypeError("Expected 'breaking_chars' to be a string.")

        pages = []
        breaking_chars = set(breaking_chars)
        tokens = []
        cur_token = []

        # Tokenize the text based on breaking characters
        for char in text:
            cur_token.append(char)
            if char in breaking_chars:
                tokens.append("".join(cur_token))
                cur_token.clear()
        if cur_token:
            tokens.append("".join(cur_token))
        del cur_token

        cur_page = []
        cur_length = 0

        # Iterate through tokens to create pages
        for token_idx in range(len(tokens)):
            cur_token = tokens[token_idx]
            # If the current token exceeds the max page length, split it into smaller chunks
            if len(cur_token) > max_page_length:
                if cur_page:
                    # Add the old page we were working on first
                    pages.append("".join(cur_page))
                    cur_page.clear()
                    cur_length = 0

                for i in range(0, len(cur_token), max_page_length):
                    pages.append(cur_token[i:i + max_page_length])  # let's debug this (a token might not snugly fit)
            else:
                # If adding the current token exceeds the max page length, start a new page
                if cur_length + len(cur_token) > max_page_length:
                    pages.append("".join(cur_page))
                    cur_page.clear()
                    cur_length = 0

                # Add the token to the current page and update the page length
                cur_page.append(cur_token)
                cur_length += len(cur_token)

        # Append the remaining tokens to the last page
        if cur_page:
            pages.append("".join(cur_page))

        return pages

    async def interaction_check(self, interaction: disnake.Interaction) -> bool:
        return interaction.author.id == self.user_id

    @disnake.ui.button(emoji="⬅")
    async def prev_page_button(
        self: "PaginatorView", button: disnake.ui.Button, inter: disnake.MessageInteraction
    ) -> None:
        await inter.response.defer()
        if inter.author.id != self.user_id:
            await inter.send(
                "You can not interact with this because it is not yours", ephemeral=True
            )
            return
        self.page_num -= 1
        self.page_num %= len(self.pages)
        # Of course, we need to show this to the user
        await inter.edit_original_response(view=self, embed=self.create_embed())

    @disnake.ui.button(emoji="➡️")
    async def next_page_button(
            self: "PaginatorView", _: disnake.ui.Button, inter: disnake.MessageInteraction
    ) -> None:
        await inter.response.defer()
        if inter.author.id != self.user_id:
            await inter.send(
                "You can not interact with this because it is not yours", ephemeral=True
            )
            return
        self.page_num += 1
        self.page_num %= len(self.pages)
        await inter.edit_original_response(view=self, embed=self.create_embed())

    async def on_timeout(self):
        for item in self.items:
            item.disabled = True

    def create_embed(self):
        return disnake.Embed(
            title=f"Page {self.page_num+1} of {len(self.pages)}:",
            description=self.pages[self.page_num],
            color=disnake.Color.from_rgb(50, 50, 255),
        )

    @disnake.ui.button(label="Go to Page", style=disnake.ButtonStyle.green)
    async def go_to_page_button(
        self, button: disnake.ui.Button, inter: disnake.MessageInteraction
    ) -> disnake.ui.Modal:
        if inter.author.id != self.user_id:
            await inter.send(
                "You can not interact with this because it is not yours", ephemeral=True
            )
            return None
        component = disnake.ui.TextInput(
            label="What page do you want to go to?",
            value=None,
            max_length=1000,
            custom_id="page_num_ui_modal" + os.urandom(20).hex(),
        )
        page_num_custom_id = component.custom_id
        async def on_timeout(_: disnake.ui.Modal):
            await inter.send(
                embed=ErrorEmbed(
                    "You didn't respond to the modal in time! You only have **15** seconds to respond."
                ),
                ephemeral=True,
            )
            raise asyncio.TimeoutError

        async def callback(
            modal: disnake.ui.Modal, modal_inter: disnake.ModalInteraction
        ):
            page_num = modal_inter.text_values.get(page_num_custom_id, None)
            if page_num is None:
                await modal_inter.send(
                    embed=ErrorEmbed("You did not enter anything"), ephemeral=True
                )
                return
            try:
                page_num = int(page_num)
            except ValueError:
                await modal_inter.send(
                    embed=ErrorEmbed("You did not send an integer page number"),
                    ephemeral=True,
                )
                return
            if page_num < 1 or page_num >= len(self.pages):
                await modal_inter.send(
                    embed=ErrorEmbed(
                        f"Your page number is out of bounds. There are only {len(self.pages)} pages"
                    ),
                    ephemeral=True,
                )
                return
            # yay! we can now go to that page
            self.page_num = (
                page_num - 1
            )  # remember, lists are 0-indexed, but they will enter 1-indexed pages
            await modal_inter.edit_original_message(
                embed=self.create_embed(), view=self
            )

        modal: disnake.ui.Modal = MyModal(
            title="What page do you want to go to?",
            components=[component],
            timeout=15.0,
            on_timeout=on_timeout,
            callback=callback,
            check = always_succeeding_check_unwrapped
        )
        try:
            await inter.response.send_modal(modal)
            return modal # this helps me test because without this i can't test
        except asyncio.TimeoutError:
            await inter.followup.send(
                embed=ErrorEmbed(
                    "You didn't send an answer fast enough. You only have **15 seconds**. Please try again."
                )
            )
