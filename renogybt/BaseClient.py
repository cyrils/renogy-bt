import os
from threading import Timer
import logging
import configparser
import libscrc
from .Utils import int_to_bytes
from .BLE import DeviceManager, Device

ALIAS_PREFIX = 'BT-TH'
NOTIFY_CHAR_UUID = "0000fff1-0000-1000-8000-00805f9b34fb"
WRITE_CHAR_UUID  = "0000ffd1-0000-1000-8000-00805f9b34fb"

class BaseClient:
    def __init__(self, config):
        self.config: configparser.ConfigParser = config
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

        self.device = Device(mac_address=self.config['device']['mac_addr'], manager=self.manager, on_resolved=self.__on_resolved, on_data=self.on_data_received, on_connect_fail=self.__on_connect_fail, notify_uuid=NOTIFY_CHAR_UUID, write_uuid=WRITE_CHAR_UUID)

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

    def __on_resolved(self):
        logging.info("resolved services")
        self.poll_params() if self.config['device'].getboolean('enable_polling') == True else self.read_params()

    def on_data_received(self, value):
        logging.info("on_data_received")
        # to be implemented by subclass

    def read_params(self):
        logging.info("reading params")
        # to be implemented by subclass

    def poll_params(self):
        self.read_params()
        if self.timer is not None and self.timer.is_alive():
            self.timer.cancel()
        self.timer = Timer(self.config['device'].getint('poll_interval'), self.poll_params)
        self.timer.start()

    def create_generic_read_request(self, device_id, function, regAddr, readWrd):                             
        data = None                                
        if regAddr and readWrd:
            data = []
            data.append(device_id)
            data.append(function)
            data.append(int_to_bytes(regAddr, 0))
            data.append(int_to_bytes(regAddr, 1))
            data.append(int_to_bytes(readWrd, 0))
            data.append(int_to_bytes(readWrd, 1))

            crc = libscrc.modbus(bytes(data))
            data.append(int_to_bytes(crc, 1))
            data.append(int_to_bytes(crc, 0))
            logging.debug("{} {} => {}".format("create_request_payload", regAddr, data))
        return data

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
