import os
from threading import Timer
import logging
import configparser
import libscrc
from .Utils import bytes_to_int, int_to_bytes
from .BLE import DeviceManager, Device

# Base class that works with all Renogy family devices
# Should be extended by each client with its own parsers and section definitions
# Section example: {'register': 5000, 'words': 8, 'parser': self.parser_func}
# Two sections cannot have same word length (important)

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
        self.device_id = None
        self.sections = []
        logging.info(f"Init {self.__class__.__name__}: {self.config['device']['alias']} => {self.config['device']['mac_addr']}")

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
        self.poll_data() if self.config['device'].getboolean('enable_polling') == True else self.read_section()

    def on_data_received(self, response):
        operation = bytes_to_int(response, 1, 1)
        if operation == 3: # read operation
            logging.info("on_data_received: response for read operation")
            index, section = self.find_section_by_response(response)
            parsed_data = section['parser'](response) if section['parser'] != None else {}
            self.data.update(parsed_data)
            if index >= len(self.sections) - 1: # last section
                self.on_read_operation_complete()
                self.data = {}
            else:
                self.read_section(index + 1)
        else:
            logging.warn("on_data_received: unknown operation={}".format(operation))

    def on_read_operation_complete(self):
        logging.info("on_read_operation_complete")
        if self.on_data_callback is not None:
            self.on_data_callback(self, self.data)

    def poll_data(self):
        self.read_section()
        if self.timer is not None and self.timer.is_alive():
            self.timer.cancel()
        self.timer = Timer(self.config['device'].getint('poll_interval'), self.poll_data)
        self.timer.start()

    def read_section(self, index = 0):
        if self.device_id == None or len(self.sections) == 0:
            return logging.error("base client cannot be used directly")
        request = self.create_generic_read_request(self.device_id, 3, self.sections[index]['register'], self.sections[index]['words']) 
        self.device.characteristic_write_value(request)

    def find_section_by_response(self, response):
        length = len(response)
        for index, param in enumerate(self.sections):
            if param['words'] * 2 + 5 == length:
                return index, param
        return None

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
