import unittest
from unittest.mock import MagicMock, AsyncMock
import configparser
import asyncio
from renogybt.RoverClient import RoverClient
from renogybt.BLEManager import BLEManager


def make_client():
    cfg = configparser.ConfigParser()
    cfg.read_dict({
        "device": {"device_id": "255", "alias": "BT-TH-TEST", "mac_addr": "AA:BB:CC:DD:EE:FF"},
        "data": {"poll_interval": "60", "enable_polling": "false"},
    })
    return RoverClient(cfg)


def make_manager(disconnect_error):
    manager = BLEManager("AA:BB:CC:DD:EE:FF", "BT-TH-TEST", None, None, None, None, None, None)
    manager.device = MagicMock()
    manager.client = MagicMock()
    manager.client.is_connected = True
    manager.client.disconnect = AsyncMock(side_effect=disconnect_error)
    return manager


class TestDisconnect(unittest.IsolatedAsyncioTestCase):
    async def test_ble_manager_disconnect_ignores_eof_error(self):
        manager = make_manager(EOFError())
        await manager.disconnect()
        manager.client.disconnect.assert_awaited_once()

    async def test_disconnect_twice_does_not_raise(self):
        client = make_client()
        client.loop = asyncio.get_running_loop()
        client.future = client.loop.create_future()
        client.ble_manager = make_manager(None)

        await client.disconnect()
        await client.disconnect()
        self.assertEqual(client.future.result(), 'DONE')


class TestStartStop(unittest.TestCase):
    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        asyncio.set_event_loop(None)
        self.loop.close()

    def test_start_returns_when_disconnect_raises_eof_error(self):
        client = make_client()

        async def connect():
            # connected, then stopped after a read, as in a normal run
            client.ble_manager = make_manager(EOFError())
            client.loop.call_later(0.1, client.stop)

        client.connect = connect
        # stops the loop if start() is still waiting on its future
        self.loop.call_later(3, self.loop.stop)
        client.start()

        self.assertTrue(client.future.done(), "start() hung waiting on its future")
        self.assertEqual(client.future.result(), 'DONE')


if __name__ == '__main__':
    unittest.main()
