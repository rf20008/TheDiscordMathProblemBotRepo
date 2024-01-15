from random import randint

from disnake import Color, Embed


def generate_random_color():
    return Color.from_rgb(r=randint(0, 255), g=randint(0, 255), b=randint(0, 255))

class SimpleEmbed(Embed):
    def __init__(
        self,
        title="",
        description="",
        color: Color | None = None,
        footer=None,
    ):
        if color is None:
            color = generate_random_color()
        super().__init__(title=title, description=description, color=color)
        self.set_footer(text=footer)


class ErrorEmbed(SimpleEmbed):
    def __init__(
        self,
        description="",
        color=Color.red(),
        custom_title="Error",
        footer=None,
    ):
        super().__init__(title=custom_title, description=description, color=color)
        self.set_footer(text=footer)


class SuccessEmbed(SimpleEmbed):
    def __init__(
        self,
        description="",
        color=Color.green(),
        successTitle="Success!",
        footer=None,
    ):
        super().__init__(title=successTitle, description=description, color=color)
        self.set_footer(text=footer)
