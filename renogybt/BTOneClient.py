import os
from threading import Timer
import logging
import configparser
from .BLE import DeviceManager, Device
from .Utils import create_request_payload, parse_charge_controller_info, parse_set_load_response, bytes_to_int

DEVICE_ID = 255
POLL_INTERVAL = 30 # seconds
ALIAS_PREFIX = 'BT-TH'

NOTIFY_CHAR_UUID = "0000fff1-0000-1000-8000-00805f9b34fb"
WRITE_CHAR_UUID  = "0000ffd1-0000-1000-8000-00805f9b34fb"

READ_PARAMS = {
    'FUNCTION': 3,
    'REGISTER': 256,
    'WORDS': 34
}

WRITE_PARAMS_LOAD = {
    'FUNCTION': 6,
    'REGISTER': 266
}

class BTOneClient:
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
            for dev in self.manager.devices():
                if dev.alias() != None and dev.alias().startswith(ALIAS_PREFIX):
                    logging.debug(f"Possible device found! ======> {dev.alias()} > [{dev.mac_address}]")
            self.__stop_service()

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

    def set_load(self, value = 0):
        logging.info("setting load {}".format(value))
        request = create_request_payload(DEVICE_ID, WRITE_PARAMS_LOAD["FUNCTION"], WRITE_PARAMS_LOAD["REGISTER"], value)
        self.device.characteristic_write_value(request)

    def poll_params(self):
        self.__read_params()
        if self.timer is not None and self.timer.is_alive():
            self.timer.cancel()
        self.timer = Timer(self.config['device'].getint('poll_interval'), self.poll_params)
        self.timer.start()

    def __read_params(self):
        logging.info("reading params")
        request = create_request_payload(DEVICE_ID, READ_PARAMS["FUNCTION"], READ_PARAMS["REGISTER"], READ_PARAMS["WORDS"])
        self.device.characteristic_write_value(request)

    def __on_resolved(self):
        logging.info("resolved services")
        self.poll_params() if self.config['device'].getboolean('enable_polling') == True else self.__read_params()

    def __on_data_received(self, value):
        operation = bytes_to_int(value, 1, 1)

        if operation == 3:
            logging.info("on_data_received: response for read operation")
            self.data = parse_charge_controller_info(value)
            if self.on_data_callback is not None:
                self.on_data_callback(self, self.data)
        elif operation == 6:
            self.data = parse_set_load_response(value)
            logging.info("on_data_received: response for write operation")
            if self.on_data_callback is not None:
                self.on_data_callback(self, self.data)
        else:
            logging.warn("on_data_received: unknown operation={}".format(operation))

    def __on_error(self, connectFailed = False, error = None):
        logging.error(f"Exception occured: {error}")
        self.__stop_service() if connectFailed else self.disconnect()

    def __on_connect_fail(self, error):
        logging.error(f"Connection failed: {error}")
        self.__stop_service()

    def __stop_service(self):
        if self.timer is not None and self.timer.is_alive():
            self.timer.cancel()
        self.manager.stop()
        os._exit(os.EX_OK)
