import unittest
from unittest.mock import MagicMock, AsyncMock, patch
from renogybt.BLEManager import BLEManager


def make_manager(mac_address="AA:BB:CC:DD:EE:FF", alias="BT-TH-TEST"):
    return BLEManager(mac_address, alias, None, None, None, None, None, None)


def make_device(address, name):
    device = MagicMock()
    device.address = address
    device.name = name
    return device


class TestDiscover(unittest.IsolatedAsyncioTestCase):
    async def test_found_by_address_skips_scan(self):
        manager = make_manager("aa:bb:cc:dd:ee:ff")
        device = make_device("AA:BB:CC:DD:EE:FF", "BT-TH-TEST")
        with patch('renogybt.BLEManager.BleakScanner') as scanner:
            scanner.find_device_by_address = AsyncMock(return_value=device)
            scanner.discover = AsyncMock()
            await manager.discover()

        scanner.find_device_by_address.assert_awaited_once()
        self.assertEqual(scanner.find_device_by_address.call_args[0][0], "AA:BB:CC:DD:EE:FF")
        scanner.discover.assert_not_awaited()
        self.assertIs(manager.device, device)

    async def test_not_found_by_address_falls_back_to_scan(self):
        manager = make_manager("AA:BB:CC:DD:EE:FF", "BT-TH-TEST")
        device = make_device("11:22:33:44:55:66", "BT-TH-TEST")
        with patch('renogybt.BLEManager.BleakScanner') as scanner:
            scanner.find_device_by_address = AsyncMock(return_value=None)
            scanner.discover = AsyncMock(return_value=[device])
            await manager.discover()

        scanner.discover.assert_awaited_once()
        self.assertIs(manager.device, device)

    async def test_lookup_error_falls_back_to_scan(self):
        manager = make_manager()
        device = make_device("AA:BB:CC:DD:EE:FF", "BT-TH-TEST")
        with patch('renogybt.BLEManager.BleakScanner') as scanner:
            scanner.find_device_by_address = AsyncMock(side_effect=Exception("adapter busy"))
            scanner.discover = AsyncMock(return_value=[device])
            await manager.discover()

        self.assertIs(manager.device, device)

    async def test_no_address_scans_by_alias(self):
        manager = make_manager("", "BT-TH-TEST")
        device = make_device("AA:BB:CC:DD:EE:FF", "BT-TH-TEST")
        with patch('renogybt.BLEManager.BleakScanner') as scanner:
            scanner.find_device_by_address = AsyncMock()
            scanner.discover = AsyncMock(return_value=[device])
            await manager.discover()

        scanner.find_device_by_address.assert_not_awaited()
        self.assertIs(manager.device, device)


if __name__ == '__main__':
    unittest.main()
