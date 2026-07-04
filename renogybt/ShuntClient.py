import asyncio
import logging
import time
from .BaseClient import BaseClient
from .Utils import bytes_to_int, format_temperature

logger = logging.getLogger(__name__)
SHUNT_READ_SUCCESS = 87


class ShuntClient(BaseClient):
    def __init__(self, config, on_data_callback=None, on_error_callback=None):
        super().__init__(config)

        self.G_NOTIFY_CHAR_UUID = "0000c411-0000-1000-8000-00805f9b34fb"
        self.G_WRITE_SERVICE_UUID = ""
        self.G_WRITE_CHAR_UUID = ""
        self.G_READ_TIMEOUT = 30

        self.throttle_timer_len = self.config['data'].getint('poll_interval')
        self.throttle_timer = time.perf_counter() - self.throttle_timer_len - 1
        self.on_data_callback = on_data_callback
        self.on_error_callback = on_error_callback
        self.data = {}
        self.sections = [
            {'register': 256, 'words': 110, 'parser': self.parse_shunt_info}
        ]
        self.set_load_params = {'function': 6, 'register': 266}

    async def on_data_received(self, response):
        logger.info("ShuntClient.on_data_received")
        operation = bytes_to_int(response, 1, 1)

        if not self.is_running or (time.perf_counter() - self.throttle_timer) <= self.throttle_timer_len:
            return

        self.throttle_timer = time.perf_counter()

        if operation == SHUNT_READ_SUCCESS:
            if (self.section_index < len(self.sections) and
                self.sections[self.section_index]['parser'] is not None and
                self.sections[self.section_index]['words'] == len(response)):
                self.data = self.sections[self.section_index]['parser'](response)
                self.on_read_operation_complete()
                if self.discovery_timeout and not self.discovery_timeout.cancelled():
                    self.discovery_timeout.cancel()
            else:
                logger.warning("Unexpected shunt payload: %s", response.hex())
        else:
            logger.info("Ignoring shunt notification with operation=%s", operation)

    def set_load(self, value=0):
        request = self.create_generic_read_request(self.device_id, self.set_load_params["function"], self.set_load_params["register"], value)
        asyncio.create_task(self.ble_manager.characteristic_write_value(request))

    def parse_shunt_info(self, bs):
        data = {}
        temp_unit = self.config['data']['temperature_unit']
        data['main_battery_percent'] = bytes_to_int(bs, 34, 2, scale=0.1)
        data['main_battery_voltage'] = bytes_to_int(bs, 25, 3, scale=0.001)
        data['starter_battery_voltage'] = bytes_to_int(bs, 30, 2, scale=0.001)
        data['charge_amps'] = bytes_to_int(bs, 21, 3, scale=0.001, signed=True)
        data['charge_watts'] = round((data['main_battery_voltage'] * data['charge_amps']), 2)
        data['battery_temperature'] = format_temperature(bytes_to_int(bs, 66, 2, scale=0.1), temp_unit)
        logger.debug("Shunt payload: %s", bs.hex())
        return data
