import unittest
import unittest.mock
from helpful_modules import my_modals
import disnake
import typing

class TestMyModals(unittest.IsolatedAsyncioTestCase):
    async def test_default_init(self):
        modal_2 = my_modals.MyModal(
            timeout=180,
            title="What code do you want to run?",
            custom_id="314159",
            inter=unittest.mock.AsyncMock(spec=disnake.ApplicationCommandInteraction),
            components=[],
        )
        self.assertRaises(
            NotImplementedError,
            modal_2.callback,
            unittest.mock.AsyncMock(spec=disnake.ApplicationCommandInteraction)
        )



    async def test_custom_callback_called_on_interaction(self):
        # Arrange
        async def custom_callback(modal, inter, *args):
            return args

        modal = my_modals.MyModal(
            timeout=180,
            title="What code do you want to run?",
            custom_id="314159",
            inter=unittest.mock.AsyncMock(spec=disnake.ApplicationCommandInteraction),
            components=[],
            callback=custom_callback,
            extra_args=["arg1", "arg2"]
        )
        interaction = unittest.mock.AsyncMock(spec=disnake.ApplicationCommandInteraction)

        # Act
        result = await modal.callback(interaction)

        # Assert
        self.assertEqual(result, ("arg1", "arg2"))

    async def test_on_error_called_with_correct_arguments(self):
        # Arrange
        modal = my_modals.MyModal(
            timeout=180,
            title="What code do you want to run?",
            custom_id="314159",
            inter=unittest.mock.AsyncMock(spec=disnake.ApplicationCommandInteraction),
            components=[],
            on_error=my_modals.MyModal.on_error
        )
        interaction = unittest.mock.AsyncMock(spec=disnake.ApplicationCommandInteraction)
        error = Exception("Test Exception")

        # Act
        await modal.on_error(error, interaction)

        # Assert
        interaction.send.assert_awaited_once_with(
            content="An error occurred while processing your request. The error has been logged.",
            ephemeral=True
        )

    async def test_modal_timeout_sends_correct_message(self):
        # Arrange
        modal = my_modals.MyModal(
            timeout=180,
            title="What code do you want to run?",
            custom_id="314159",
            inter=unittest.mock.AsyncMock(spec=disnake.ApplicationCommandInteraction),
            components=[]
        )
        interaction = unittest.mock.AsyncMock(spec=disnake.ApplicationCommandInteraction)

        # Act
        await modal.on_timeout()

        # Assert
        interaction.send.assert_awaited_once_with("You didn't submit the modal fast enough!", ephemeral=True)

    if __name__ == "__main__":
        unittest.main()
