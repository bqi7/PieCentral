import unittest
import multiprocessing
from runtime.messaging import SharedMemoryBuffer


class TestSharedMemory(unittest.TestCase):
    def setUp(self):
        self.buf = SharedMemoryBuffer('test', 8)

    def tearDown(self):
        del self.buf

    def test_shared(self):
        def target(ready, buf):
            ready.wait()
            self.assertEqual(buf[0], 1)
            buf[0] = 2
        ready = multiprocessing.Event()
        child = multiprocessing.Process(target=target, args=(ready, self.buf))
        child.start()
        self.assertEqual(self.buf[0], 0)
        self.buf[0] = 1
        ready.set()
        child.join()
        self.assertEqual(self.buf[0], 2)

if __name__ == '__main__':
    unittest.main()
