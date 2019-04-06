import unittest
import multiprocessing
from runtime.buffer import SharedMemoryBuffer, SharedLock


class TestSharedMemory(unittest.TestCase):
    def setUp(self):
        self.buf = SharedMemoryBuffer('test', 8)

    def tearDown(self):
        del self.buf

    def test_shared(self):
        def target(ready):
            ready.wait()
            buf = SharedMemoryBuffer('test', 8)
            self.assertEqual(buf[0], 1)
            buf[0] = buf.peers
        ready = multiprocessing.Event()
        child = multiprocessing.Process(target=target, args=(ready, ))
        child.start()
        self.assertEqual(self.buf[0], 0)
        self.buf[0] = 1
        ready.set()
        child.join()
        self.assertEqual(self.buf[0], 2)
        self.assertEqual(self.buf.peers, 1)


class TestSharedLock(unittest.TestCase):
    def setUp(self):
        self.lock = SharedLock('test-lock')

    def tearDown(self):
        del self.lock

    def test_lock(self):
        def target(sync_ctr, unsync_ctr, n):
            lock = SharedLock('test-lock')
            for _ in range(n):
                unsync_ctr.value += 1
            for _ in range(n):
                with lock:
                    sync_ctr.value += 1
        sync_ctr = multiprocessing.Value('i', lock=False)
        unsync_ctr = multiprocessing.Value('i', lock=False)
        child_count, n = 4, 8000
        children = [multiprocessing.Process(target=target, args=(sync_ctr, unsync_ctr, n))
                    for _ in range(child_count)]
        for child in children:
            child.start()
        for child in children:
            child.join()
        self.assertEqual(sync_ctr.value, child_count*n)
        self.assertLess(unsync_ctr.value, child_count*n)



if __name__ == '__main__':
    unittest.main()
