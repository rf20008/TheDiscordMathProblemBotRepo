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
        if isinstance(v, str):
            v = v.encode('utf-8')
        if not isinstance(v, bytes):
            raise TypeError(f"`v` must be str or bytes, not type {v.__class__.__name__}")
        return hashlib.sha3_256(v).digest()
    def __init__(self, size: int, contents: list[str | bytes] | None):
        if not isinstance(size, int):
            raise TypeError("Size must be a non-negative integer")

        if size <= 0:
            raise ValueError("Size must be a positive integer")
        self.size = size
        self.tree = [b"" for _ in range(4*self.size)]
        if contents is not None:
            if not isinstance(contents, list):
                raise TypeError("Contents are not a list")
            if len(contents) != self.size:
                raise TypeError("Contents are not the right length")
            contents_hashes = [None for _ in range(self.size)]
            for i in range(self.size):
                if isinstance(contents[i], bytes):
                    contents_hashes[i] = contents[i]
                elif isinstance(contents[i], str):
                    contents_hashes[i] = self.sha3_hash(contents[i])
                else:
                    raise TypeError(f"Contents index#{i} is not a str nor bytes")

            self._build_from_hashes(sindex=0, sleft=0, sright=self.size-1, data_hashes=contents_hashes)

    @property
    def root(self):
        return self.tree[1]
    def __setitem__(self, index, value: str):
        if not isinstance(index, int):
            raise TypeError("index must be an int")
        if index<0 or index>=self.size:
            raise IndexError("FixedLengthMerkler index out of range")
        if not isinstance(value, str):
            raise TypeError("value must be a str")
        self.update(index=1, left=0, right=self.size, pos=index, new_val = value.encode("utf-8"))
    def update(self, *, index: int, left: int, right: int, pos: int, new_val: bytes):
        if left==right:
            self.tree[index] = self.sha3_hash(new_val)
            return
        mid = (left+right)//2
        if (pos <= mid):
            self.update(index=index*2, left=left, right=mid, pos=pos, new_val=new_val)
        else:
            self.update(index=index * 2 + 1, left=mid + 1, right=right, pos=pos, new_val=new_val)
        self.tree[index] = self.sha3_hash(self.tree[index*2] + b'\x00' + self.tree[index*2 + 1])
        return

    def get_idx_logn(self, *, index: int, left: int, right: int, pos: int) -> bytes:
        #print(index, left, right, pos, self.tree[index].hex())
        if left==right:
            return index
        mid = (left+right)//2
        if pos<=mid:
            return self.get_idx_logn(index=index*2, left=left, right=mid, pos=pos)
        return self.get_idx_logn(index=index*2+1, left=mid+1, right=right, pos=pos)


    def __getitem__(self, index: int):
        if not isinstance(index, int):
            raise TypeError("idx must be an int")
        if index<0 or index>=self.size:
            raise IndexError("FixedLengthMerkler index out of range")
        return self.tree[self.get_idx_logn(index=1, left=0, right=self.size-1, pos = index)]
    def __getstate__(self):
        """Prepare object for pickling."""
        return {'leaves': self.leaves, 'size': self.size}

    def __setstate__(self, state):
        """Restore object from pickled state."""
        self.leaves = state['leaves']
        self.size = state['size']
    def verify_whole_tree(self, data_blocks: list[str]):
        if len(data_blocks) != self.size:
            raise ValueError("Mismatch between data block size and merkle tree size")
        return self._verify_whole_tree(index=1, left=0, right=self.size-1, data_blocks=data_blocks)
    def _verify_whole_tree(self, *, index: int, left: int, right: int, data_blocks: list[str]):
        if len(data_blocks) != self.size:
            raise ValueError("Mismatch between data block size and merkle tree size")

        if left==right:
            expected_hash = self.sha3_hash(data_blocks[left])
            if expected_hash != self.tree[index]:
                raise MerklerInvalidError(f"Merkler failed at index {index} (pos={left}). Expected hash: {expected_hash}. Found: {self.tree[index]}")
            return True
        mid = (left+right)//2

        self._verify_whole_tree(index=index*2, left=left, right=mid, data_blocks=data_blocks)
        self._verify_whole_tree(index=index*2+1, left=mid+1, right=right, data_blocks=data_blocks)
        expected_hash = self.sha3_hash(self.tree[index*2] + b'\x00' + self.tree[index*2 + 1])
        if expected_hash != self.tree[index]:
            raise MerklerInvalidError(
                f"Merkler failed at index {index} (pos={left}). Expected hash: {expected_hash}. Found: {self.tree[index]}")
        return True
    def _verify_index(self, *, sindex: int, left: int, right: int, index_to_verify: int, should_be: bytes):
        if left==right:
            expected_hash = self.sha3_hash(should_be)
            if expected_hash != self.tree[sindex]:
                raise MerklerInvalidError(
                    f"Merkler failed at index {sindex} (pos={left}). "
                    f"Expected hash: {expected_hash.hex()}. Found: {self.tree[sindex].hex()}"
                )
            return True
        mid = (left+right)//2
        if (index_to_verify <= mid):
            self._verify_index(sindex = sindex*2, left=left, right=mid, index_to_verify=index_to_verify, should_be=should_be)
        else:
            self._verify_index(sindex=sindex*2+1, left=mid+1, right=right, index_to_verify=index_to_verify, should_be=should_be)
        expected_hash = self.sha3_hash(self.tree[sindex * 2] + b'\x00' + self.tree[sindex * 2 + 1])
        if expected_hash != self.tree[sindex]:
            raise MerklerInvalidError(
                f"Merkler failed at index {sindex} (pos={left}). Expected hash: {expected_hash}. Found: {self.tree[sindex]}")
        return True
    def verify_index(self, index: int, should_be: bytes):
        return self._verify_index(sindex=1, left=0, right=self.size-1, index_to_verify=index, should_be=should_be)
    def build_from_blocks(self, data_blocks: list[bytes]):
        if len(data_blocks) != self.size:
            raise ValueError("data blocks are not the same size as the merkler")
        data_hashes = [self.sha3_hash(data_blocks[i]) for i in range(len(data_blocks))]
        self._build_from_hashes(sindex=1, sleft=0, sright = self.size - 1, data_hashes=data_hashes)
    def _build_from_hashes(self, *, sindex: int, sleft: int, sright: int, data_hashes: list[bytes]):
        if sleft == sright:
            self.tree[sindex] = data_hashes[sleft]
            return
        mid = (sleft+sright)//2
        self._build_from_hashes(sindex=sindex*2, sleft=sleft, sright=mid, data_hashes=data_hashes)
        self._build_from_hashes(sindex=sindex*2+1, sleft=mid+1, sright=sright, data_hashes=data_hashes)
        self.tree[sindex] = self.sha3_hash(self.tree[sindex*2] + b'\x00' + self.tree[sindex*2 + 1])
        return
    def to_dict(self):
        return {
            "size": self.size,
            "tree": [item.hex() if item else None for item in self.tree]
        }
    @classmethod
    def from_dict(cls, data):
        merkler = cls(data['size'])
        merkler.tree = [bytes.fromhex(item) if item else None for item in data['tree']]
        return merkler
    def __repr__(self):
        return str(self.to_dict())