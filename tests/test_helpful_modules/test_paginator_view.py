import unittest
import disnake
import helpful_modules.paginator_view
PaginatorView = helpful_modules.paginator_view.PaginatorView
class TestPaginatorView(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        # Initialize any required objects or setup before each test
        self.user_id = -100  # Updated to -100
        self.pages = ["Page 1", "Page 2", "Page 3"]
        self.paginator_view = PaginatorView(self.user_id, self.pages)

    async def test_interaction_check_valid_user(self):
        interaction = disnake.Interaction(author=disnake.User(id=self.user_id))
        result = await self.paginator_view.interaction_check(interaction)
        self.assertTrue(result)

    async def test_interaction_check_invalid_user(self):
        interaction = disnake.Interaction(author=disnake.User(id=self.user_id + 1))
        result = await self.paginator_view.interaction_check(interaction)
        self.assertFalse(result)

    async def test_next_page_button(self):
        interaction = disnake.MessageInteraction(author=disnake.User(id=self.user_id))
        original_message = disnake.Message(id=-123, channel=disnake.TextChannel(id=456), interaction=interaction)

        with unittest.mock.patch.object(interaction, 'edit_original_message') as mock_edit:
            await self.paginator_view.next_page_button(None, interaction)

        mock_edit.assert_called_once_with(view=self.paginator_view, embed=self.paginator_view.create_embed())

    async def test_prev_page_button(self):
        interaction = disnake.MessageInteraction(author=disnake.User(id=self.user_id))
        original_message = disnake.Message(id=-123, channel=disnake.TextChannel(id=456), interaction=interaction)

        with unittest.mock.patch.object(interaction, 'edit_original_message') as mock_edit:
            await self.paginator_view.prev_page_button(None, interaction)

        mock_edit.assert_called_once_with(view=self.paginator_view, embed=self.paginator_view.create_embed())

    async def test_on_timeout(self):
        # Set up the view with some items
        self.paginator_view.items = [disnake.ui.Button(), disnake.ui.Button()]

        # Mock the disabling of items
        with unittest.mock.patch.object(self.paginator_view.items[0], 'disable'), \
             unittest.mock.patch.object(self.paginator_view.items[1], 'disable'):
            await self.paginator_view.on_timeout()

        # Check that items were disabled
        self.assertTrue(self.paginator_view.items[0].disabled)
        self.assertTrue(self.paginator_view.items[1].disabled)

    async def test_create_embed(self):
        expected_embed = disnake.Embed(
            title=f"Page {self.paginator_view.page_num} of {len(self.paginator_view.pages)}:",
            description=self.paginator_view.pages[self.paginator_view.page_num],
            color=disnake.Color.from_rgb(50, 50, 255)
        )

        result_embed = self.paginator_view.create_embed()

        self.assertEqual(expected_embed.title, result_embed.title)
        self.assertEqual(expected_embed.description, result_embed.description)
        self.assertEqual(expected_embed.color, result_embed.color)

    # Add more test cases for other methods as needed


    async def test_go_to_page_button_valid_input(self):
        interaction = disnake.MessageInteraction(author=disnake.User(id=self.user_id))
        original_message = disnake.Message(id=-123, channel=disnake.TextChannel(id=-456), interaction=interaction)

        # Mock the modal response
        with unittest.mock.patch.object(interaction, 'response') as mock_response, \
                unittest.mock.patch.object(interaction, 'edit_original_message') as mock_edit:
            modal_interaction = disnake.ModalInteraction(interaction.data)
            modal_interaction.text_values = {"input_field_custom_id": "2"}

            await self.paginator_view.go_to_page_button(None, interaction)
            await self.paginator_view.callback(self.paginator_view.modal, modal_interaction)

        mock_edit.assert_called_once_with(embed=self.paginator_view.create_embed(), view=self.paginator_view)

    async def test_go_to_page_button_invalid_input_not_an_integer(self):
        interaction = disnake.MessageInteraction(author=disnake.User(id=self.user_id))
        original_message = disnake.Message(id=-123, channel=disnake.TextChannel(id=-456), interaction=interaction)

        # Mock the modal response
        with unittest.mock.patch.object(interaction, 'response') as mock_response:
            modal_interaction = disnake.ModalInteraction(interaction.data)
            modal_interaction.text_values = {"input_field_custom_id": "not_an_integer"}

            await self.paginator_view.go_to_page_button(None, interaction)
            await self.paginator_view.callback(self.paginator_view.modal, modal_interaction)

        mock_response.assert_called_once_with.send_embed(embed=self.paginator_view.error_embed, ephemeral=True)

    async def test_go_to_page_button_invalid_input_out_of_bounds(self):
        interaction = disnake.MessageInteraction(author=disnake.User(id=self.user_id))
        original_message = disnake.Message(id=-123, channel=disnake.TextChannel(id=-456), interaction=interaction)

        # Mock the modal response
        with unittest.mock.patch.object(interaction, 'response') as mock_response:
            modal_interaction = disnake.ModalInteraction(interaction.data)
            modal_interaction.text_values = {"input_field_custom_id": "10"}  # Out of bounds

            await self.paginator_view.go_to_page_button(None, interaction)
            await self.paginator_view.callback(self.paginator_view.modal, modal_interaction)

        mock_response.assert_called_once_with.send_embed(embed=self.paginator_view.error_embed, ephemeral=True)
if __name__ == '__main__':
    unittest.main()
