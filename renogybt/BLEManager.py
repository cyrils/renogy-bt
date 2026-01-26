import asyncio
import logging
import sys
from bleak import BleakClient, BleakScanner, BLEDevice, BleakError

DISCOVERY_TIMEOUT = 5  # seconds for discovery
DISCOVERY_RETRY_DELAY = 3  # seconds between retries
CONNECT_RETRY_DELAY = 5  # seconds between connection retries
CONNECT_MAX_ATTEMPTS = 3
DISCOVERY_MAX_ATTEMPTS = 5


class BLEManager:
    def __init__(
        self,
        mac_address,
        alias,
        on_data,
        on_connect_fail,
        write_service_uuid,
        notify_char_uuid,
        write_char_uuid,
    ):
        self.mac_address = mac_address
        self.device_alias = alias
        self.data_callback = on_data
        self.connect_fail_callback = on_connect_fail
        self.write_service_uuid = write_service_uuid
        self.notify_char_uuid = notify_char_uuid
        self.write_char_uuid = write_char_uuid

        self.write_char_handle = None
        self.device: BLEDevice = None
        self.client: BleakClient = None
        self.discovered_devices = []

    # DISCOVERY WITH RETRY FOR BLUEZ IN-PROGRESS / NO ADAPTER / DBUS ERRORS

    async def discover(self):
        mac_address = self.mac_address.upper()
        attempt = 0

        while attempt < DISCOVERY_MAX_ATTEMPTS:
            try:
                logging.info("Starting discovery...")

                self.discovered_devices = await BleakScanner.discover(
                    timeout=DISCOVERY_TIMEOUT
                )

                logging.info("Devices found: %s", len(self.discovered_devices))

                # Search for target device
                for dev in self.discovered_devices:
                    if dev.address and (
                        dev.address.upper() == mac_address
                        or (dev.name and dev.name.strip() == self.device_alias)
                    ):
                        logging.info(f"Found matching device {dev.name} => {dev.address}")
                        self.device = dev

                        # Give BlueZ time to settle
                        await asyncio.sleep(1.5)
                        return

                logging.warning(f"Device not found: {self.device_alias} => {self.mac_address}")
                return

            except Exception as e:
                if any(err in str(e) for err in ["InProgress", "NoReply", "org.freedesktop.DBus"]):
                    logging.warning(
                        f"Bluetooth busy or DBus error, retrying discovery... ({attempt + 1}/{DISCOVERY_MAX_ATTEMPTS})"
                    )
                    attempt += 1
                    await asyncio.sleep(DISCOVERY_RETRY_DELAY)
                else:
                    logging.error(f"Bluetooth error during discovery: {e}")
                    return

        logging.error("Bluetooth discovery failed after multiple attempts")


    # CONNECT WITH RETRIES AND OLD BLEAK COMPATIBILITY

    async def connect(self):
        if not self.device:
            logging.error("No device connected!")
            return

        # Disconnect stale client if exists
        if self.client:
            try:
                if self.client.is_connected:
                    logging.info("Disconnecting stale BLE client")
                    await self.client.disconnect()
                    await asyncio.sleep(1)
            except Exception:
                pass

        # Use use_cached=False to avoid stale GATT connections
        self.client = BleakClient(self.device, timeout=15, use_cached=False)

        for attempt in range(CONNECT_MAX_ATTEMPTS):
            try:
                logging.info(f"Connecting (attempt {attempt + 1})...")
                await self.client.connect()

                logging.info(f"Client connection: {self.client.is_connected}")
                if not self.client.is_connected:
                    raise RuntimeError("Unable to connect")

                # Give services time to populate
                await asyncio.sleep(1.5)

                # Discover services and characteristics
                for service in self.client.services:
                    for characteristic in service.characteristics:
                        if characteristic.uuid == self.notify_char_uuid:
                            await self.client.start_notify(
                                characteristic, self.notification_callback
                            )
                            logging.info(f"Subscribed to notification {characteristic.uuid}")

                        if (
                            characteristic.uuid == self.write_char_uuid
                            and service.uuid == self.write_service_uuid
                        ):
                            self.write_char_handle = characteristic.handle
                            logging.info(
                                f"Found write characteristic {characteristic.uuid}, service {service.uuid}"
                            )

                if not self.write_char_handle:
                    raise RuntimeError("Write characteristic not found")

                logging.info("BLE connection established successfully")
                return  # SUCCESS

            except Exception as e:
                logging.warning(f"Connection attempt {attempt + 1} failed: {e}")
                await asyncio.sleep(CONNECT_RETRY_DELAY)

        logging.error("Error connecting to device after retries")
        self.connect_fail_callback(sys.exc_info())


    # NOTIFICATION CALLBACK

    async def notification_callback(self, characteristic, data: bytearray):
        logging.info("notification_callback")
        await self.data_callback(data)


    # WRITE

    async def characteristic_write_value(self, data):
        if not self.client or not self.client.is_connected:
            logging.error("Write attempted while not connected")
            return

        if not self.write_char_handle:
            logging.error("Write characteristic handle not set")
            return

        try:
            logging.info(f"Writing to {self.write_char_uuid}: {data}")
            await self.client.write_gatt_char(
                self.write_char_handle, bytearray(data), response=False
            )
            logging.info("Characteristic write succeeded")
            await asyncio.sleep(0.5)
        except Exception as e:
            logging.error(f"Characteristic write failed: {e}")


    # DISCONNECT

    async def disconnect(self):
        if self.client and self.client.is_connected:
            try:
                logging.info(f"Disconnecting device: {self.device.name} {self.device.address}")
                await self.client.disconnect()
                await asyncio.sleep(0.5)
            except Exception as e:
                logging.warning(f"Failed to disconnect BLE client: {e}")
