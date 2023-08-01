import os
import logging
import configparser
from .BLE import DeviceManager, Device
from .Utils import create_battery_read_payload, parse_battery_info

DEVICE_ID = 48 # or 247 ?

NOTIFY_CHAR_UUID = "0000fff1-0000-1000-8000-00805f9b34fb"
WRITE_CHAR_UUID  = "0000ffd1-0000-1000-8000-00805f9b34fb"

READ_PARAMS = {
    'FUNCTION': 3,
    'REGISTER': 5000,
    'WORDS': 46
}

class BatteryClient:
    def __init__(self, config, on_data_callback=None):
        self.config: configparser.ConfigParser = config
        self.on_data_callback = on_data_callback
        self.manager = None
        self.device = None
        self.timer = None
        self.data = {}

    def connect(self):
        self.manager = DeviceManager(adapter_name=self.config['device']['adapter'], mac_address=self.config['device']['mac_addr'], alias=self.config['device']['alias'])
        self.manager.discover()

        if not self.manager.device_found:
            logging.error(f"Device not found: {self.config['device']['alias']} => {self.config['device']['mac_addr']}, please check the details provided.")

        self.device = Device(mac_address=self.config['device']['mac_addr'], manager=self.manager, on_resolved=self.__on_resolved, on_data=self.__on_data_received, on_connect_fail=self.__on_connect_fail, notify_uuid=NOTIFY_CHAR_UUID, write_uuid=WRITE_CHAR_UUID)

        try:
            self.device.connect()
            self.manager.run()
        except Exception as e:
            self.__on_error(True, e)
        except KeyboardInterrupt:
            self.__on_error(False, "KeyboardInterrupt")

    def disconnect(self):
        self.device.disconnect()
        self.__stop_service()

    def read_params(self):
        logging.info("reading params")
        request = create_battery_read_payload(DEVICE_ID, READ_PARAMS["FUNCTION"], READ_PARAMS["REGISTER"], READ_PARAMS["WORDS"])
        self.device.characteristic_write_value(request)

    def __on_resolved(self):
        logging.info("resolved services")
        self.read_params()

    def __on_data_received(self, value):
        logging.info("on_data_received: response for read operation", value.hex())
        self.data = parse_battery_info(value)
        if self.on_data_callback is not None:
            self.on_data_callback(self, self.data)

    def __on_error(self, connectFailed = False, error = None):
        logging.error(f"Exception occured: {error}")
        self.__stop_service() if connectFailed else self.disconnect()

    def __on_connect_fail(self, error):
        logging.error(f"Connection failed: {error}")
        self.__stop_service()

    def __stop_service(self):
        self.manager.stop()
        os._exit(os.EX_OK)
