import asyncio
import json
import aiofiles

__all__ = ("AsyncFileDict",)


class AsyncFileDict:
    """A class for asynchronously managing JSON data stored in a file."""

    def __init__(self, filename, overwrite=False):
        """
        Initialize the AsyncFileDict.

        Parameters:
        - filename (str): The name of the file to read or write JSON data.
        - overwrite (bool): If True, overwrite the file if it exists.

        """
        self.filename = filename
        self.dict = {}
        if overwrite:
            asyncio.run(self.update_my_file())

    async def update_my_file(self):
        """
        Asynchronously update the file with the internal dictionary.

        Returns:
        - None

        """
        async with aiofiles.open(self.filename, "w") as file:
            await file.write(str(json.dumps(self.dict)))

    async def read_from_file(self) -> dict:
        """
        Asynchronously read JSON data from the file into the internal dictionary.

        Returns:
        - dict: The internal dictionary.

        """
        async with aiofiles.open(self.filename, "r") as file:
            stuff = await file.read(-1)
            self.dict = json.loads(stuff)
        return self.dict

    async def get_key(self, key):
        """
        Asynchronously get the value associated with the given key.

        Parameters:
        - key: The key to retrieve.

        Returns:
        - The value associated with the key.

        """
        return (await self.read_from_file())[key]

    async def set_key(self, key, val):
        """
        Asynchronously set a key-value pair and update the file.

        Parameters:
        - key: The key to set.
        - val: The value to associate with the key.

        Returns:
        - None

        """
        self.dict[key] = val
        await self.update_my_file()

    async def del_key(self, key):
        """
        Asynchronously delete a key-value pair and update the file.

        Parameters:
        - key: The key to delete.

        Returns:
        - None

        """
        del self.dict[key]
        await self.update_my_file()

    def __iter__(self):
        """
        Return an iterator for the keys in the internal dictionary.

        Returns:
        - Iterator for keys.

        """
        return self.dict.__iter__()

    def keys(self):
        """
        Return a view of the keys in the internal dictionary.

        Returns:
        - View of keys.

        """
        return self.dict.keys()

    def values(self):
        """
        Return a view of the values in the internal dictionary.

        Returns:
        - View of values.

        """
        return self.dict.items()

    def items(self):
        """
        Return a view of the key-value pairs in the internal dictionary.

        Returns:
        - View of key-value pairs.

        """
        return self.dict.items()
