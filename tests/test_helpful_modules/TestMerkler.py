import unittest
from hashlib import sha3_256
from helpful_modules.Merkler import FixedLengthMerkler, MerklerInvalidError

class TestFixedLengthMerkler(unittest.TestCase):

    def setUp(self):
        """Set up the Merkle tree with 7 entries."""
        self.data = [
            "Log entry 1",
            "Log entry 2",
            "Log entry 3",
            "Log entry 4",
            "Log entry 5",
            "Log entry 6",
            "Log entry 7"
        ]
        self.merkler = FixedLengthMerkler(size=7, contents=self.data)

        for i, entry in enumerate(self.data):
            self.merkler[i] = entry

    def test_root(self):
        """Test that the root hash of the tree is correct."""
        expecteds = ['_', '_', '_', '_', '_', '_', '_']
        for i in range(6, 0, -1):
            expecteds[i] = sha3_256(self.merkler.tree[2*i] + b'\x00' + self.merkler.tree[2*i+1]).digest()
            self.assertEqual(expecteds[i], self.merkler.tree[i])

        self.assertEqual(self.merkler.root, expecteds[1])

    def test_verify_whole_tree_valid(self):
        """Test verifying the entire tree with correct data."""
        try:
            self.merkler.verify_whole_tree(self.data)
            self.assertTrue(True)
        except MerklerInvalidError:
            self.fail("Merkle tree verification failed unexpectedly.")

    def test_verify_whole_tree_invalid(self):
        """Test verifying the entire tree with incorrect data."""
        invalid_data = self.data.copy()
        invalid_data[0] = "Corrupted entry"
        with self.assertRaises(MerklerInvalidError):
            self.merkler.verify_whole_tree(invalid_data)

    def test_verify_index_valid(self):
        """Test verifying a single index with correct data."""
        for i in range(7):
            try:
                self.assertTrue(self.merkler.verify_index(i, sha3_256(self.data[i].encode('utf-8')).digest()))
            except MerklerInvalidError:
                self.fail("Merkle index verification failed unexpectedly.")

    def test_verify_index_invalid(self):
        """Test verifying a single index with incorrect data."""
        with self.assertRaises(MerklerInvalidError):
            self.merkler.verify_index(2, sha3_256("Corrupted entry".encode('utf-8')).digest())

    def test_setitem(self):
        """Test setting an item in the tree and verifying its effect on the root."""
        self.merkler[4] = "Updated entry"
        self.data[4] = "Updated entry"
        expecteds = ['_', '_', '_', '_', '_', '_', '_']
        for i in range(6, 0, -1):
            expecteds[i] = sha3_256(self.merkler.tree[2 * i] + b'\x00' + self.merkler.tree[2 * i + 1]).digest()
            self.assertEqual(expecteds[i], self.merkler.tree[i])

        self.assertEqual(self.merkler.root, expecteds[1])

    def test_getitem(self):
        """Test getting an item from the tree."""
        for i in range(7):
            encodr = sha3_256(self.data[i].encode('utf-8')).digest()
            if self.merkler[i] != encodr:
                print(i, self.merkler[i].hex(), encodr.hex())
            self.assertEqual(self.merkler[i], encodr)

    def test_out_of_range_setitem(self):
        """Test setting an item out of range."""
        with self.assertRaises(IndexError):
            self.merkler[7] = b"Out of range entry"

    def test_out_of_range_getitem(self):
        """Test getting an item out of range."""
        with self.assertRaises(IndexError):
            self.merkler[7]

    def test_invalid_setitem_type(self):
        """Test setting an item with an invalid type."""
        with self.assertRaises(TypeError):
            self.merkler[0] = 1234  # Should be a string or bytes

    def test_invalid_getitem_type(self):
        """Test getting an item with an invalid type."""
        with self.assertRaises(TypeError):
            self.merkler["0"]  # Index must be an integer

    def test_verify_invalid_size(self):
        """Test verifying the tree with mismatched data sizes."""
        with self.assertRaises(ValueError):
            self.merkler.verify_whole_tree(self.data[:6])  # Too few entries

    def test_build_from_blocks(self):
        """Test building the tree from raw data blocks."""
        self.merkler.build_from_blocks(self.data)
        try:
            self.merkler.verify_whole_tree(self.data)
            self.assertTrue(True)
        except MerklerInvalidError:
            self.fail("Merkle tree verification failed unexpectedly after build.")

if __name__ == "__main__":
    unittest.main()
