import unittest
from helpful_modules.circular_deque import CircularDeque, CircularDequeIterator


class TestCircularDeque(unittest.TestCase):

    def test_init_and_len(self):
        dq = CircularDeque()
        self.assertEqual(len(dq), 0)
        self.assertTrue(dq.empty())

        dq2 = CircularDeque([1, 2, 3])
        self.assertEqual(len(dq2), 3)
        self.assertFalse(dq2.empty())
        self.assertEqual(list(dq2), [1, 2, 3])

    def test_append_and_pop_right(self):
        dq = CircularDeque()
        dq.append_right(10)
        dq.append_right(20)
        dq.append_right(30)
        self.assertEqual(len(dq), 3)
        self.assertEqual(dq.right, 30)

        self.assertEqual(dq.pop_right(), 30)
        self.assertEqual(dq.pop_right(), 20)
        self.assertEqual(len(dq), 1)
        self.assertEqual(dq.pop_right(), 10)
        self.assertTrue(dq.empty())

    def test_append_and_pop_left(self):
        dq = CircularDeque()
        dq.append_left(10)
        dq.append_left(20)
        dq.append_left(30)
        self.assertEqual(len(dq), 3)
        self.assertEqual(dq.left, 30)

        self.assertEqual(dq.pop_left(), 30)
        self.assertEqual(dq.pop_left(), 20)
        self.assertEqual(len(dq), 1)
        self.assertEqual(dq.pop_left(), 10)
        self.assertTrue(dq.empty())

    def test_mixed_appends_and_pops(self):
        dq = CircularDeque([1, 2])
        dq.append_right(3)
        dq.append_left(0)
        # Expected: [0, 1, 2, 3]
        self.assertEqual(list(dq), [0, 1, 2, 3])

        self.assertEqual(dq.pop_left(), 0)
        self.assertEqual(dq.pop_right(), 3)
        self.assertEqual(list(dq), [1, 2])

    def test_getitem_and_setitem(self):
        dq = CircularDeque([10, 20, 30, 40])
        self.assertEqual(dq[0], 10)
        self.assertEqual(dq[1], 20)
        self.assertEqual(dq[-1], 40)
        self.assertEqual(dq[-2], 30)

        # Test index out of range
        with self.assertRaises(IndexError):
            _ = dq[10]
        with self.assertRaises(IndexError):
            _ = dq[-5]

        # Test setitem
        dq[1] = 99
        self.assertEqual(dq[1], 99)

    def test_slicing(self):
        dq = CircularDeque([1, 2, 3, 4, 5])
        # Note: Depending on how slice is implemented in your getitem,
        # let's verify basic slice retrieval if supported by your implementation.
        # Your implementation loops over item.start, item.stop, item.step
        sub = dq[1:4:1]
        self.assertEqual(sub, [2, 3, 4])

    def test_extend_operations(self):
        dq = CircularDeque([1, 2])
        dq.extend_right([3, 4])
        self.assertEqual(list(dq), [1, 2, 3, 4])

        dq.extend_left([0, -1])
        # Depending on extend_left reversal logic, let's check final state
        self.assertIn(0, dq)
        self.assertIn(-1, dq)

    def test_search_and_math_methods(self):
        dq = CircularDeque([5, 2, 8, 2, 1])
        self.assertEqual(dq.count(2), 2)
        self.assertEqual(dq.index(8), 2)
        self.assertEqual(max(dq), 8)
        self.assertEqual(min(dq), 1)

    def test_removal_and_insertion(self):
        dq = CircularDeque([1, 2, 4])
        dq.insert(2, 3)  # Inserts 3 at index 2
        self.assertEqual(list(dq), [1, 2, 3, 4])

        dq.remove(3)
        self.assertEqual(list(dq), [1, 2, 4])

        del dq[0]
        self.assertEqual(list(dq), [2, 4])

    def test_comparisons_and_multiplication(self):
        dq1 = CircularDeque([1, 2, 3])
        dq2 = CircularDeque([1, 2, 3])
        dq3 = CircularDeque([1, 2, 4])

        self.assertEqual(dq1, dq2)
        self.assertNotEqual(dq1, dq3)
        self.assertTrue(dq1 < dq3)

        # Test multiplication
        dq_mul = dq1 * 2
        self.assertEqual(len(dq_mul), 6)
        self.assertEqual(list(dq_mul), [1, 2, 3, 1, 2, 3])

    def test_empty_deque_exceptions(self):
        dq = CircularDeque()
        with self.assertRaises(IndexError):
            _ = dq.left
        with self.assertRaises(IndexError):
            _ = dq.right
        with self.assertRaises(ValueError):
            dq.pop_left()
        with self.assertRaises(ValueError):
            dq.pop_right()
        with self.assertRaises(ValueError):
            max(dq)
        with self.assertRaises(ValueError):
            min(dq)


if __name__ == "__main__":
    unittest.main()