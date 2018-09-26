import unittest

from webcrawling.back_heap import BackHeap


class BackHeapTests(unittest.TestCase):
    SampleHost = 'test.com'

    def test_push(self):
        heap = BackHeap()
        self.assertTrue(heap.push_host(self.SampleHost))

    def test_double_push(self):
        heap = BackHeap()
        self.assertTrue(heap.push_host(self.SampleHost))
        self.assertFalse(heap.push_host(self.SampleHost))

    def test_pop_push(self):
        heap = BackHeap()
        self.assertTrue(heap.push_host(self.SampleHost, delay=False))
        self.assertEqual(heap.pop_host(), (0, self.SampleHost))
        self.assertTrue(heap.push_host(self.SampleHost))

    def test_pop_empty(self):
        heap = BackHeap()
        self.assertIsNone(heap.pop_host())
