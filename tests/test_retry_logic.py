import unittest
from unittest.mock import MagicMock, AsyncMock, patch
import configparser
import asyncio
from renogybt.ShuntClient import ShuntClient
from renogybt.BLEManager import BLEManager

# Custom sleep mock to yield control on sleep(0) but skip actual delays
original_sleep = asyncio.sleep

async def mock_sleep(delay, *args, **kwargs):
    if delay == 0:
        await original_sleep(0)
    else:
        # Return immediately for any retry/connect delays
        pass

class TestRetryLogic(unittest.IsolatedAsyncioTestCase):
    async def test_retry_on_connect_fail_up_to_three_times(self):
        cfg = configparser.ConfigParser()
        cfg.read_dict({
            "device": {"device_id": "255", "alias": "BT-TH-TEST", "mac_addr": "AA:BB:CC:DD:EE:FF"},
            "data": {"poll_interval": "60", "enable_polling": "false"},
        })
        client = ShuntClient(cfg)
        client.loop = asyncio.get_running_loop()
        client.future = client.loop.create_future()

        mock_ble_manager = MagicMock(spec=BLEManager)
        mock_ble_manager.discover = AsyncMock()
        mock_ble_manager.connect = AsyncMock()
        mock_ble_manager.device = MagicMock()
        mock_ble_manager.client = MagicMock()
        mock_ble_manager.client.is_connected = False

        # When connect() is called, trigger the fail callback
        def side_effect_connect():
            client._BaseClient__on_connect_fail(Exception("Mock Connection Error"))
        mock_ble_manager.connect.side_effect = side_effect_connect

        with patch('renogybt.BaseClient.BLEManager', return_value=mock_ble_manager):
            with patch('asyncio.sleep', side_effect=mock_sleep) as mock_sleep_spy:
                await client.connect()
                
                # Allow scheduled retry tasks to run
                for _ in range(10):
                    await asyncio.sleep(0)

                self.assertEqual(client._retry_count, 3)
                # Verify sleep was called with exponential delays (2s, 4s, 8s)
                called_delays = [call[0][0] for call in mock_sleep_spy.call_args_list if call[0][0] > 0]
                self.assertEqual(called_delays, [2, 4, 8])

    async def test_retry_on_unexpected_disconnect(self):
        cfg = configparser.ConfigParser()
        cfg.read_dict({
            "device": {"device_id": "255", "alias": "BT-TH-TEST", "mac_addr": "AA:BB:CC:DD:EE:FF"},
            "data": {"poll_interval": "60", "enable_polling": "false"},
        })
        client = ShuntClient(cfg)
        client.loop = asyncio.get_running_loop()
        client.future = client.loop.create_future()

        mock_ble_manager = MagicMock(spec=BLEManager)
        mock_ble_manager.discover = AsyncMock()
        mock_ble_manager.connect = AsyncMock()
        mock_ble_manager.device = MagicMock()
        mock_ble_manager.client = MagicMock()
        mock_ble_manager.client.is_connected = True

        with patch('renogybt.BaseClient.BLEManager', return_value=mock_ble_manager):
            with patch('asyncio.sleep', side_effect=mock_sleep) as mock_sleep_spy:
                await client.connect()
                self.assertEqual(client._retry_count, 0)

                # Trigger unexpected disconnect
                client._BaseClient__on_disconnect()

                # Run the scheduled retry task
                for _ in range(5):
                    await asyncio.sleep(0)

                self.assertEqual(client._retry_count, 0)
                mock_sleep_spy.assert_any_call(2)

    async def test_retry_on_connect_fail_custom_max_retry(self):
        cfg = configparser.ConfigParser()
        cfg.read_dict({
            "device": {"device_id": "255", "alias": "BT-TH-TEST", "mac_addr": "AA:BB:CC:DD:EE:FF", "max_retry": "5"},
            "data": {"poll_interval": "60", "enable_polling": "false"},
        })
        client = ShuntClient(cfg)
        client.loop = asyncio.get_running_loop()
        client.future = client.loop.create_future()

        self.assertEqual(client.max_retry, 5)

        mock_ble_manager = MagicMock(spec=BLEManager)
        mock_ble_manager.discover = AsyncMock()
        mock_ble_manager.connect = AsyncMock()
        mock_ble_manager.device = MagicMock()
        mock_ble_manager.client = MagicMock()
        mock_ble_manager.client.is_connected = False

        def side_effect_connect():
            client._BaseClient__on_connect_fail(Exception("Mock Connection Error"))
        mock_ble_manager.connect.side_effect = side_effect_connect

        with patch('renogybt.BaseClient.BLEManager', return_value=mock_ble_manager):
            with patch('asyncio.sleep', side_effect=mock_sleep) as mock_sleep_spy:
                await client.connect()
                
                # Allow scheduled retry tasks to run
                for _ in range(15):
                    await asyncio.sleep(0)

                self.assertEqual(client._retry_count, 5)
                called_delays = [call[0][0] for call in mock_sleep_spy.call_args_list if call[0][0] > 0]
                self.assertEqual(called_delays, [2, 4, 8, 16, 32])
