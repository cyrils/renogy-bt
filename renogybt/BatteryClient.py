from .BaseClient import BaseClient
from .Utils import bytes_to_int, format_temperature

# Client for Renogy LFP battery with built-in bluetooth / BT-2 module

FUNCTION = {
    3: "READ",
    6: "WRITE"
}

class BatteryClient(BaseClient):
    def __init__(self, config, on_data_callback=None, on_error_callback=None):
        super().__init__(config)
        self.on_data_callback = on_data_callback
        self.on_error_callback = on_error_callback
        self.data = {}
        self.sections = [
            {'register': 5000, 'words': 17, 'parser': self.parse_cell_volt_info},
            {'register': 5017, 'words': 17, 'parser': self.parse_cell_temp_info},
            {'register': 5042, 'words': 6, 'parser': self.parse_battery_info},
            {'register': 5122, 'words': 8, 'parser': self.parse_device_info},
            {'register': 5223, 'words': 1, 'parser': self.parse_device_address}
        ]

    def parse_cell_volt_info(self, bs):
        data = {}
        data['function'] = FUNCTION.get(bytes_to_int(bs, 1, 1))
        data['cell_count'] = bytes_to_int(bs, 3, 2)
        for i in range(0, data['cell_count']):
            data[f'cell_voltage_{i}'] = bytes_to_int(bs, 5 + i*2, 2, scale = 0.1)
        self.data.update(data)

    def parse_cell_temp_info(self, bs):
        data = {}
        data['function'] = FUNCTION.get(bytes_to_int(bs, 1, 1))
        data['sensor_count'] = bytes_to_int(bs, 3, 2)
        for i in range(0, data['sensor_count']):
            celcius = bytes_to_int(bs, 5 + i*2, 2, scale = 0.1, signed = True)
            data[f'temperature_{i}'] = format_temperature(celcius, self.config['data']['temperature_unit'])
        self.data.update(data)

    def parse_battery_info(self, bs):
        data = {}
        data['function'] = FUNCTION.get(bytes_to_int(bs, 1, 1))
        data['current'] = bytes_to_int(bs, 3, 2, True, scale = 0.01)
        data['voltage'] = bytes_to_int(bs, 5, 2, scale = 0.1)
        data['remaining_charge'] = bytes_to_int(bs, 7, 4, scale = 0.001)
        data['capacity'] = bytes_to_int(bs, 11, 4, scale = 0.001)
        self.data.update(data)

    def parse_device_info(self, bs):
        data = {}
        data['function'] = FUNCTION.get(bytes_to_int(bs, 1, 1))
        data['model'] = (bs[3:17]).decode('utf-8')
        self.data.update(data)

    def parse_device_address(self, bs):
        data = {}
        data['device_id'] = bytes_to_int(bs, 3, 2)
        self.data.update(data)
