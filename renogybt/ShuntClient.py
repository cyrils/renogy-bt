import logging
import time
from .BaseClient import BaseClient
from .Utils import bytes_to_int, format_temperature

logger = logging.getLogger(__name__)
SHUNT_READ_SUCCESS = 87

# Shunt Client is purely notification-driven
# rather than the controller-style Modbus read request flow.

class ShuntClient(BaseClient):
    def __init__(self, config, on_data_callback=None, on_error_callback=None):
        super().__init__(config)

        self.NOTIFY_CHAR_UUID = "0000c411-0000-1000-8000-00805f9b34fb"
        self.WRITE_SERVICE_UUID = ""
        self.WRITE_CHAR_UUID = ""

        self.on_data_callback = on_data_callback
        self.on_error_callback = on_error_callback
        self.data = {}
        self.throttle_timer_len = self.config['data'].getint('poll_interval')
        self.throttle_timer = time.perf_counter() - self.throttle_timer_len - 1

    async def on_data_received(self, response):
        logger.debug("ShuntClient.on_data_received")
        operation = bytes_to_int(response, 1, 1)

        if (time.perf_counter() - self.throttle_timer) <= self.throttle_timer_len:
            return

        self.throttle_timer = time.perf_counter()

        if operation != SHUNT_READ_SUCCESS:
            logger.debug("Ignoring shunt notification with operation=%s", operation)
            return

        self.data = self.parse_shunt_info(response)
        self.on_read_operation_complete()

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
