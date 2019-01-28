import unittest
import threading
import multiprocessing
from runtime.statemanager import SharedStoreClient, SharedStoreServer
import pytest


class TestSharedStore(unittest.TestCase):
    def setUp(self):
        self.name = 'test-store'
        self.server = SharedStoreServer(self.name)
        self.server.start()

    def tearDown(self):
        self.server.stop()

    def check_set_watch(self, sender, receiver, key, value):
        async def recv(store, recv_key):
            self.assertEqual(key, recv_key)
            self.assertEqual(store[key], value)
            done.set()
        done = threading.Event()
        receiver.watch(key, recv)
        sender[key] = value
        done.wait()

    def check_del_watch(self, sender, receiver, key):
        async def set_recv(store, recv_key):
            del store[recv_key]
        async def del_recv(store, recv_key):
            self.assertNotIn(store, recv_key)
            done.set()
        done = threading.Event()
        receiver.watch(key, set_recv)
        sender.watch(key, del_recv)
        sender[key] = None
        done.wait()

    def test_client_set_watch(self):
        with SharedStoreClient(self.name) as client:
            self.check_set_watch(client, self.server, 'key', 1)

    def test_server_set_watch(self):
        with SharedStoreClient(self.name) as client:
            self.check_set_watch(self.server, client, 'key', 1)

    def test_client_del_watch(self):
        # with SharedStoreClient(self.name) as client:
        #     self.check_del_watch(client, self.server, 'key')
        pass

    def test_server_del_watch(self):
        # with SharedStoreClient(self.name) as client:
        #     self.check_del_watch(self.server, client, 'key')
        pass

    def test_server_restart(self):
        self.assertEqual(threading.active_count(), 2)
        self.server.stop()
        self.assertEqual(threading.active_count(), 1)
        self.server.start()
        self.assertEqual(threading.active_count(), 2)

    @pytest.mark.perf
    def test_set_throughput(self):
        pass  # TODO
