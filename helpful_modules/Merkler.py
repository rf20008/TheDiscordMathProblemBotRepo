import hashlib

from .FileDictionaryReader import AsyncFileDict


class MerklerInvalidError(Exception):
    """An exception raised when the merkle tree is invalid"""

    pass


class FixedLengthMerkler:
    tree: list[bytes]
    size: int
    __slots__ = ("size", "tree")

    @staticmethod
    def sha3_hash(v: str | bytes):
        """
        Compute the SHA3-256 hash of the given input.

        Args:
            v (str | bytes): The input to hash. Can be a string or bytes.

        Returns:
            bytes: The resulting SHA3-256 hash.

        Raises:
            TypeError: If `v` is not a string or bytes.
        """
        if isinstance(v, str):
            v = v.encode("utf-8")
        if not isinstance(v, bytes):
            raise TypeError(
                f"`v` must be str or bytes, not type {v.__class__.__name__}"
            )
        return hashlib.sha3_256(v).digest()

    def __init__(self, size: int, contents: list[str | bytes] | None):
        """
        Initializes the FixedLengthMerkler object with a given size and optional contents.

        Args:
            size (int): The number of leaves in the Merkle tree.
            contents (list[str | bytes] | None): A list of data blocks to initialize the tree.

        Raises:
            TypeError: If size is not an integer or contents is not a list.
            ValueError: If size is less than or equal to 0 or contents has incorrect length.
        """
        if not isinstance(size, int):
            raise TypeError("Size must be a non-negative integer")

        if size <= 0:
            raise ValueError("Size must be a positive integer")
        self.size = size
        self.tree = [b"" for _ in range(4 * self.size)]
        if contents is not None:
            if not isinstance(contents, list):
                raise TypeError("Contents are not a list")
            if len(contents) != self.size:
                raise TypeError("Contents are not the right length")
            contents_hashes = [b"" for _ in range(self.size)]
            for i in range(self.size):
                if isinstance(contents[i], bytes):
                    contents_hashes[i] = contents[i]
                elif isinstance(contents[i], str):
                    contents_hashes[i] = self.sha3_hash(contents[i])
                else:
                    raise TypeError(f"Contents index#{i} is not a str nor bytes")

            self._build_from_hashes(
                sindex=1, sleft=0, sright=self.size - 1, data_hashes=contents_hashes
            )
            # print(self)
            # print(self.tree[1], self.tree[2], self.tree[4], self.tree[8])
            self.verify_whole_tree(contents_hashes)

    @property
    def root(self):
        """
        Returns the root hash of the Merkle tree.

        Returns:
            bytes: The root hash.
        """
        return self.tree[1]

    def __setitem__(self, index, value: str):
        """
        Updates the value at the given index in the Merkle tree.

        Args:
            index (int): The index of the leaf to update.
            value (str): The new value to store at the leaf.

        Raises:
            TypeError: If index is not an integer or value is not a string.
            IndexError: If index is out of range.
        """
        if not isinstance(index, int):
            raise TypeError("index must be an int")
        if index < 0 or index >= self.size:
            raise IndexError("FixedLengthMerkler index out of range")
        if not isinstance(value, str):
            raise TypeError("value must be a str")
        self.update(
            index=1, left=0, right=self.size, pos=index, new_val=value.encode("utf-8")
        )

    def update(self, *, index: int, left: int, right: int, pos: int, new_val: bytes):
        """
        Recursively updates a value in the Merkle tree and recalculates the hashes up the tree.

        Args:
            index (int): The current node index.
            left (int): The left boundary of the range.
            right (int): The right boundary of the range.
            pos (int): The position of the leaf to update.
            new_val (bytes): The new value to hash and update in the tree.
        """
        if left == right:
            self.tree[index] = self.sha3_hash(new_val)
            return
        mid = (left + right) // 2
        if pos <= mid:
            self.update(index=index * 2, left=left, right=mid, pos=pos, new_val=new_val)
        else:
            self.update(
                index=index * 2 + 1, left=mid + 1, right=right, pos=pos, new_val=new_val
            )
        self.tree[index] = self.sha3_hash(
            self.tree[index * 2] + b"\x00" + self.tree[index * 2 + 1]
        )
        return

    def get_idx_logn(self, pos: int) -> int:
        """
        Finds the index of a leaf at a given position using logarithmic time complexity.

        Args:
            pos (int): The position of the leaf.

        Returns:
            int: The index of the leaf in the tree.
        """
        return self._get_idx_logn(index=1, left=0, right=self.size - 1, pos=pos)

    def _get_idx_logn(self, *, index: int, left: int, right: int, pos: int) -> int:
        """
        Helper function for logarithmic index lookup in the tree.

        Args:
            index (int): The current node index.
            left (int): The left boundary of the range.
            right (int): The right boundary of the range.
            pos (int): The position of the leaf to look up.

        Returns:
            int: The index of the leaf.
        """
        # print(index, left, right, pos, self.tree[index].hex())
        if left == right:
            return index
        mid = (left + right) // 2
        if pos <= mid:
            return self._get_idx_logn(index=index * 2, left=left, right=mid, pos=pos)
        return self._get_idx_logn(
            index=index * 2 + 1, left=mid + 1, right=right, pos=pos
        )

    def __getitem__(self, index: int):
        """
        Retrieves the value at the given index in the Merkle tree.

        Args:
            index (int): The index of the leaf to retrieve.

        Returns:
            bytes: The hash at the specified leaf position.

        Raises:
            TypeError: If index is not an integer.
            IndexError: If index is out of range.
        """
        if not isinstance(index, int):
            raise TypeError("idx must be an int")
        if index < 0 or index >= self.size:
            raise IndexError("FixedLengthMerkler index out of range")
        return self.tree[
            self._get_idx_logn(index=1, left=0, right=self.size - 1, pos=index)
        ]

    def __getstate__(self):
        """
        Prepares the object for pickling.

        Returns:
            dict: A dictionary with the object's state.
        """
        return {"tree": self.tree, "size": self.size}

    def __setstate__(self, state):
        """Restore object from pickled state."""
        self.tree = state["tree"]
        self.size = state["size"]

    def verify_whole_tree(self, data_blocks: list[str]):
        """
        Verifies the integrity of the entire Merkle tree.

        Args:
            data_blocks (list[str]): A list of data blocks to verify against the tree.

        Returns:
            bool: True if the tree is valid, otherwise raises an error.

        Raises:
            ValueError: If the number of data blocks does not match the size of the Merkle tree.
        """
        if len(data_blocks) != self.size:
            raise ValueError("Mismatch between data block size and merkle tree size")
        return self._verify_whole_tree(
            index=1, left=0, right=self.size - 1, data_blocks=data_blocks
        )

    def _verify_whole_tree(
        self, *, index: int, left: int, right: int, data_blocks: list[str | bytes]
    ):
        """
        Recursively verifies the entire Merkle tree against a list of data blocks.

        Args:
            index (int): The current node index.
            left (int): The left boundary of the range.
            right (int): The right boundary of the range.
            data_blocks (list[str | bytes]): A list of data blocks to verify.

        Returns:
            bool: True if the tree is valid, otherwise raises an error.

        Raises:
            MerklerInvalidError: If the hash at any node does not match the expected hash.
        """
        if len(data_blocks) != self.size:
            raise ValueError("Mismatch between data block size and merkle tree size")

        if left == right:
            if isinstance(data_blocks[left], str):
                expected_hash = self.sha3_hash(data_blocks[left])
            else:
                expected_hash = data_blocks[left]
            if expected_hash != self.tree[index]:
                raise MerklerInvalidError(
                    f"Merkler failed at index {index} (pos={left}). Expected hash: {expected_hash}. Found: {self.tree[index]}"
                )
            return True
        mid = (left + right) // 2

        self._verify_whole_tree(
            index=index * 2, left=left, right=mid, data_blocks=data_blocks
        )
        self._verify_whole_tree(
            index=index * 2 + 1, left=mid + 1, right=right, data_blocks=data_blocks
        )
        expected_hash = self.sha3_hash(
            self.tree[index * 2] + b"\x00" + self.tree[index * 2 + 1]
        )
        if expected_hash != self.tree[index]:
            raise MerklerInvalidError(
                f"Merkler failed at index {index} (pos={left}). Expected hash: {expected_hash}. Found: {self.tree[index]}"
            )
        return True

    def _verify_index(
        self,
        *,
        sindex: int,
        left: int,
        right: int,
        index_to_verify: int,
        should_be_hash: bytes,
    ):
        """
        Verifies the integrity of a specific leaf in the Merkle tree.

        Args:
            sindex (int): The current node index.
            left (int): The left boundary of the range.
            right (int): The right boundary of the range.
            index_to_verify (int): The index of the leaf to verify.
            should_be_hash (bytes): The expected hash value of the leaf.

        Returns:
            bool: True if the leaf is valid, otherwise raises an error.

        Raises:
            MerklerInvalidError: If the hash at the leaf does not match the expected hash.
        """
        if left == right:

            if should_be_hash != self.tree[sindex]:
                raise MerklerInvalidError(
                    f"Merkler failed at index {sindex} (pos={left}). "
                    f"Expected hash: {should_be_hash.hex()}. Found: {self.tree[sindex].hex()}"
                )
            return True
        mid = (left + right) // 2
        if index_to_verify <= mid:
            self._verify_index(
                sindex=sindex * 2,
                left=left,
                right=mid,
                index_to_verify=index_to_verify,
                should_be_hash=should_be_hash,
            )
        else:
            self._verify_index(
                sindex=sindex * 2 + 1,
                left=mid + 1,
                right=right,
                index_to_verify=index_to_verify,
                should_be_hash=should_be_hash,
            )
        expected_hash = self.sha3_hash(
            self.tree[sindex * 2] + b"\x00" + self.tree[sindex * 2 + 1]
        )
        if expected_hash != self.tree[sindex]:
            raise MerklerInvalidError(
                f"Merkler failed at index {sindex} (pos={left}). Expected hash: {expected_hash}. Found: {self.tree[sindex]}"
            )
        return True

    def verify_index(self, index: int, should_be: bytes | str):
        """
        Verifies whether the hash at a specified index matches the expected hash.

        Args:
            index (int): The index of the node to verify.
            should_be (bytes | str): The expected hash at the specified index. If a string is provided, it will be hashed using SHA3.

        Returns:
            bool: True if the hash at the specified index matches the expected hash, otherwise False.

        Raises:
            MerklerInvalidError: If any hash mismatch occurs while traversing the Merkle tree.
        """
        if isinstance(should_be, str):
            should_be = self.sha3_hash(should_be)
        return self._verify_index(
            sindex=1,
            left=0,
            right=self.size - 1,
            index_to_verify=index,
            should_be_hash=should_be,
        )

    def build_from_blocks(self, data_blocks: list[bytes]):
        """
        Builds a Merkle tree from a list of data blocks, hashing each block to form the leaves.

        Args:
            data_blocks (list[bytes]): A list of data blocks to construct the Merkle tree.

        Raises:
            ValueError: If the number of data blocks does not match the size of the Merkle tree.

        Notes:
            This method uses SHA3 hashing for each data block and calls a private method to build the tree recursively.
        """
        if len(data_blocks) != self.size:
            raise ValueError("data blocks are not the same size as the merkler")
        data_hashes = [self.sha3_hash(data_blocks[i]) for i in range(len(data_blocks))]
        self._build_from_hashes(
            sindex=1, sleft=0, sright=self.size - 1, data_hashes=data_hashes
        )

    def _build_from_hashes(
        self, *, sindex: int, sleft: int, sright: int, data_hashes: list[bytes]
    ):
        """
        Recursively builds a Merkle tree from a list of data hashes.

        Args:
            sindex (int): The current node index.
            sleft (int): The left boundary of the range.
            sright (int): The right boundary of the range.
            data_hashes (list[bytes]): A list of data hashes to build the tree.

        Raises:
            MerklerInvalidError: If the hash at any node does not match the expected hash.
        """
        if sleft == sright:
            self.tree[sindex] = data_hashes[sleft]
            return
        mid = (sleft + sright) // 2
        self._build_from_hashes(
            sindex=sindex * 2, sleft=sleft, sright=mid, data_hashes=data_hashes
        )
        self._build_from_hashes(
            sindex=sindex * 2 + 1, sleft=mid + 1, sright=sright, data_hashes=data_hashes
        )
        self.tree[sindex] = self.sha3_hash(
            self.tree[sindex * 2] + b"\x00" + self.tree[sindex * 2 + 1]
        )
        return

    def to_dict(self):
        return {
            "size": self.size,
            "tree": [item.hex() if item else None for item in self.tree],
        }

    @classmethod
    def from_dict(cls, data):
        merkler = cls(data["size"])
        merkler.tree = [bytes.fromhex(item) if item else None for item in data["tree"]]
        return merkler

    def __repr__(self):
        return str(self.to_dict())

    def get_leaves(self):
        return self._get_leaves(index=1, left=0, right=self.size - 1)

    def _get_leaves(self, index: int, left: int, right: int):
        if left == right:
            return [self.tree[index]]
        mid = (left + right) // 2
        left_leaves = self._get_leaves(index=index * 2, left=left, right=mid)
        right_leaves = self._get_leaves(index * 2 + 1, mid + 1, right)
        return left_leaves + right_leaves


class DynamicLengthMerkler(FixedLengthMerkler):
    cur_size: int
    DEFAULT: str = ""

    def __init__(self, initial_size=16, contents: list[bytes] | None = None):
        if contents is None:
            contents = [self.DEFAULT for _ in range(initial_size)]
        if len(contents) < initial_size:
            raise ValueError("Contents too small")
        super().__init__(size=initial_size, contents=contents)
        self.cur_size = initial_size

    def resize(self, new_size: int):
        new_tree = [b"" for _ in range(4 * new_size)]
        old_leaves = self.get_leaves()

        def build_tree(index: int, left: int, right: int):
            nonlocal new_tree
            if left == right:
                if left < self.size:
                    self.tree[index] = old_leaves[left]
                else:
                    self.tree[index] = self.sha3_hash(self.DEFAULT)
                return
            mid = (left + right) // 2
            build_tree(index * 2, left, mid)
            build_tree(index * 2 + 1, mid + 1, right)
            new_tree[index] = self.sha3_hash(
                new_tree[index * 2] + b"\x00" + new_tree[index * 2 + 1]
            )

        build_tree(1, 0, new_size)
        self.tree = new_tree
        self.size = new_size

    @staticmethod
    def sha3_hash(obj: bytes | str):
        if isinstance(obj, str):
            v = v.encode("utf-8")
        if not isinstance(obj, bytes):
            raise TypeError(
                f"`v` must be str or bytes, not type {obj.__class__.__name__}"
            )
        return hashlib.sha3_256(obj).digest()

    def append(self, thing):
        if self.cur_size >= self.size:
            self.resize(self.size * 2 + 1)

        self[self.cur_size] = thing
        self.cur_size += 1
