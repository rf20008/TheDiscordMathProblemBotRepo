import disnake
from disnake.ui import Modal
import os
from .threads_or_useful_funcs import base_on_error
class MyModal(Modal):
    """A wrapper around disnake.Modal that allows passing in a custom callback :_)"""
    def __init__(self, *args, **kwargs):

        async def default_callback(modal_inter):
            raise NotImplementedError
        
        self._callback = kwargs.pop('callback', default_callback)
        async def _check(s, inter):
            return True
        kwargs['custom_id'] = kwargs['custom_id'] if 'custom_id' in kwargs.keys() else os.urandom(20).hex()
        self._check = kwargs.pop('check', _check)
        self._on_error = kwargs.pop('on_error', MyModal.on_error)
        self._inter: disnake.ApplicationCommandInteraction = kwargs.pop('inter', None)
        
        super().__init__(*args, **kwargs)

        

    async def callback(self, inter: disnake.ModalInteraction):
        if await self._check(inter):
            await self._callback(inter)
    async def on_error(self, error, inter):
        await inter.send(**(await base_on_error(inter, error)))


    async def on_timeout(self):
        await self._inter.send("You didn't submit the modal fast enough!")
        return
