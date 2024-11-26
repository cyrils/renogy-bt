import asyncio
import configparser
import logging
import traceback
from .BLEManager import BLEManager
from .Utils import bytes_to_int, crc16_modbus, int_to_bytes

# Base class that works with all Renogy family devices
# Should be extended by each client with its own parsers and section definitions
# Section example: {'register': 5000, 'words': 8, 'parser': self.parser_func}

ALIAS_PREFIXES = ['BT-TH', 'RNGRBP', 'BTRIC']
NOTIFY_CHAR_UUID = "0000fff1-0000-1000-8000-00805f9b34fb"
WRITE_CHAR_UUID  = "0000ffd1-0000-1000-8000-00805f9b34fb"
READ_TIMEOUT = 15 # (seconds)
READ_SUCCESS = 3
READ_ERROR = 131

class BaseClient:
    def __init__(self, config):
        self.config: configparser.ConfigParser = config
        self.ble_manager = None
        self.device = None
        self.poll_timer = None
        self.read_timeout = None
        self.data = {}
        self.device_id = self.config['device'].getint('device_id')
        self.sections = []
        self.section_index = 0
        self.loop = None
        logging.info(f"Init {self.__class__.__name__}: {self.config['device']['alias']} => {self.config['device']['mac_addr']}")

    def start(self):
        try:
            self.loop = asyncio.get_event_loop()
            self.loop.create_task(self.connect())
            self.future = self.loop.create_future()
            self.loop.run_until_complete(self.future)
        except Exception as e:
            self.__on_error(e)
        except KeyboardInterrupt:
            self.__on_error("KeyboardInterrupt")

    async def connect(self):
        self.ble_manager = BLEManager(mac_address=self.config['device']['mac_addr'], alias=self.config['device']['alias'], on_data=self.on_data_received, on_connect_fail=self.__on_connect_fail, notify_uuid=NOTIFY_CHAR_UUID, write_uuid=WRITE_CHAR_UUID)
        await self.ble_manager.discover()

        if not self.ble_manager.device:
            logging.error(f"Device not found: {self.config['device']['alias']} => {self.config['device']['mac_addr']}, please check the details provided.")
            for dev in self.ble_manager.discovered_devices:
                if dev.name != None and dev.name.startswith(tuple(ALIAS_PREFIXES)):
                    logging.info(f"Possible device found! ====> {dev.name} > [{dev.address}]")
            self.stop()
        else:
            await self.ble_manager.connect()
            if self.ble_manager.client and self.ble_manager.client.is_connected: await self.read_section()

    async def disconnect(self):
        await self.ble_manager.disconnect()
        self.future.set_result('DONE')

    async def on_data_received(self, response):
        if self.read_timeout and not self.read_timeout.cancelled(): self.read_timeout.cancel()
        operation = bytes_to_int(response, 1, 1)

        if operation == READ_SUCCESS or operation == READ_ERROR:
            if (operation == READ_SUCCESS and
                self.section_index < len(self.sections) and
                self.sections[self.section_index]['parser'] != None and
                self.sections[self.section_index]['words'] * 2 + 5 == len(response)):
                # call the parser and update data
                logging.info(f"on_data_received: read operation success")
                self.__safe_parser(self.sections[self.section_index]['parser'], response)
            else:
                logging.info(f"on_data_received: read operation failed: {response.hex()}")

            if self.section_index >= len(self.sections) - 1: # last section, read complete
                self.section_index = 0
                self.on_read_operation_complete()
                self.data = {}
                await self.check_polling()
            else:
                self.section_index += 1
                await asyncio.sleep(0.5)
                await self.read_section()
        else:
            logging.warning("on_data_received: unknown operation={}".format(operation))

    def on_read_operation_complete(self):
        logging.info("on_read_operation_complete")
        self.data['__device'] = self.config['device']['alias']
        self.data['__client'] = self.__class__.__name__
        self.__safe_callback(self.on_data_callback, self.data)

    def on_read_timeout(self):
        logging.error("on_read_timeout => Timed out! Please check your device_id!")
        self.stop()

    async def check_polling(self):
        if self.config['data'].getboolean('enable_polling'): 
            await asyncio.sleep(self.config['data'].getint('poll_interval'))
            await self.read_section()

    async def read_section(self):
        index = self.section_index
        if self.device_id == None or len(self.sections) == 0:
            return logging.error("BaseClient cannot be used directly")

        self.read_timeout = self.loop.call_later(READ_TIMEOUT, self.on_read_timeout)
        request = self.create_generic_read_request(self.device_id, 3, self.sections[index]['register'], self.sections[index]['words']) 
        await self.ble_manager.characteristic_write_value(request)

    def create_generic_read_request(self, device_id, function, regAddr, readWrd):                             
        data = None                                
        if regAddr != None and readWrd != None:
            data = []
            data.append(device_id)
            data.append(function)
            data.append(int_to_bytes(regAddr, 0))
            data.append(int_to_bytes(regAddr, 1))
            data.append(int_to_bytes(readWrd, 0))
            data.append(int_to_bytes(readWrd, 1))

            crc = crc16_modbus(bytes(data))
            data.append(crc[0])
            data.append(crc[1])
            logging.debug("{} {} => {}".format("create_request_payload", regAddr, data))
        return data

    def __on_error(self, error = None):
        logging.error(f"Exception occured: {error}")
        self.__safe_callback(self.on_error_callback, error)
        self.stop()

    def __on_connect_fail(self, error):
        logging.error(f"Connection failed: {error}")
        self.__safe_callback(self.on_error_callback, error)
        self.stop()

    def stop(self):
        if self.read_timeout and not self.read_timeout.cancelled(): self.read_timeout.cancel()
        self.loop.create_task(self.disconnect())

    def __safe_callback(self, calback, param):
        if calback is not None:
            try:
                calback(self, param)
            except Exception as e:
                logging.error(f"__safe_callback => exception in callback! {e}")
                traceback.print_exc()

    def __safe_parser(self, parser, param):
        if parser is not None:
            try:
                parser(param)
            except Exception as e:
                logging.error(f"exception in parser! {e}")
                traceback.print_exc()
