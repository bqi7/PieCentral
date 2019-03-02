import unittest
import threading
import multiprocessing
from runtime.statemanager import SharedStore
import pytest
import time


class TestSharedStore(unittest.TestCase):
    def create_net(self, count, target, args=None, kwargs=None):
        args, kwargs = args or (), kwargs or {}
        ready, error = multiprocessing.Barrier(count), multiprocessing.Event()
        children = [multiprocessing.Process(target=target, args=(whoami, ready, error) + args,
                                            kwargs=kwargs) for whoami in range(count)]
        return children, ready, error

    def set_and_wait(self, store, whoami, ready, error, count, delay=1):
        store.ready.wait()
        ready.wait()
        store[whoami] = whoami
        ready.wait()
        time.sleep(delay)  # Wait for command streams to stabilize
        for peer in range(count):
            if peer not in store:
                error.set()
                return

    def test_net_set(self):
        def target(whoami, ready, error, count):
            with SharedStore() as store:
                self.set_and_wait(store, whoami, ready, error, count)
        count = 10
        children, ready, error = self.create_net(count, target, args=(count, ))
        for child in children:
            child.start()
        for child in children:
            child.join()
        self.assertFalse(error.is_set())

    def test_net_del(self):
        def target(whoami, ready, error, count):
            with SharedStore() as store:
                self.set_and_wait(store, whoami, ready, error, count)
                if error.is_set():
                    return
                del store[whoami]
                ready.wait()
                time.sleep(1)
                for peer in range(count):
                    if peer in store:
                        error.set()
                        return
        count = 10
        children, ready, error = self.create_net(count, target, args=(count, ))
        for child in children:
            child.start()
        for child in children:
            child.join()
        self.assertFalse(error.is_set())
