import logging
from .BaseClient import BaseClient
from .Utils import bytes_to_int

# Client for Renogy LFP battery RBT100LFP12-BT-XX series

DEVICE_ID = 48

FUNCTION = {
    3: "READ",
    6: "WRITE"
}

READ_PARAMS = {
    'FUNCTION': 3,
    'REGISTER': 5000,
    'WORDS': 48
}

class BatteryClient(BaseClient):
    def __init__(self, config, on_data_callback=None):
        super().__init__(config)
        self.on_data_callback = on_data_callback

    def read_params(self):
        logging.info("reading params")
        request = self.create_generic_read_request(DEVICE_ID, READ_PARAMS["FUNCTION"], READ_PARAMS["REGISTER"], READ_PARAMS["WORDS"])
        self.device.characteristic_write_value(request)

    def on_data_received(self, value):
        logging.info("on_data_received: response for read operation")
        self.data = self.parse_battery_info(value)
        if self.on_data_callback is not None:
            self.on_data_callback(self, self.data)

    def parse_battery_info(self, bs):
        data = {}
        data['function'] = FUNCTION.get(bytes_to_int(bs, 1, 1))
        data['cell_count'] = bytes_to_int(bs, 3, 2)
        data['sensor_count'] = bytes_to_int(bs, 37, 2)

        for i in range(0, data['cell_count']):
            data[f'cell_voltage_{i}'] = bytes_to_int(bs, 5 + i*2, 2) * 0.1

        for i in range(0, data['sensor_count']):
            data[f'temperature_{i}'] = bytes_to_int(bs, 39 + i*2, 2) * 0.1

        data['current'] = bytes_to_int(bs, 87, 2, True) * 0.01
        data['voltage'] = bytes_to_int(bs, 89, 2) * 0.1
        data['remaining_charge'] = bytes_to_int(bs, 91, 4) * 0.001
        data['capacity'] = bytes_to_int(bs, 95, 4) * 0.001

        return data
