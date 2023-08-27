from .BaseClient import BaseClient
from .Utils import bytes_to_int

# Client for Renogy LFP battery with built-in bluetooth / BT-2 module

DEVICE_ID = 48

FUNCTION = {
    3: "READ",
    6: "WRITE"
}

class BatteryClient(BaseClient):
    def __init__(self, config, on_data_callback=None):
        super().__init__(config)
        self.on_data_callback = on_data_callback
        self.data = {}
        self.device_id = DEVICE_ID
        self.sections = [
            {'register': 5000, 'words': 17, 'parser': self.parse_cell_volt_info},
            {'register': 5017, 'words': 17, 'parser': self.parse_cell_temp_info},
            {'register': 5042, 'words': 6, 'parser': self.parse_battery_info},
            {'register': 5122, 'words': 8, 'parser': self.parse_device_info}
        ]

    def parse_cell_volt_info(self, bs):
        data = {}
        data['function'] = FUNCTION.get(bytes_to_int(bs, 1, 1))
        data['cell_count'] = bytes_to_int(bs, 3, 2)
        for i in range(0, data['cell_count']):
            data[f'cell_voltage_{i}'] = bytes_to_int(bs, 5 + i*2, 2) * 0.1
        self.data.update(data)

    def parse_cell_temp_info(self, bs):
        data = {}
        data['function'] = FUNCTION.get(bytes_to_int(bs, 1, 1))
        data['sensor_count'] = bytes_to_int(bs, 3, 2)
        for i in range(0, data['sensor_count']):
            data[f'temperature_{i}'] = bytes_to_int(bs, 5 + i*2, 2) * 0.1
        self.data.update(data)

    def parse_battery_info(self, bs):
        data = {}
        data['function'] = FUNCTION.get(bytes_to_int(bs, 1, 1))
        data['current'] = bytes_to_int(bs, 3, 2, True) * 0.01
        data['voltage'] = bytes_to_int(bs, 5, 2) * 0.1
        data['remaining_charge'] = bytes_to_int(bs, 7, 4) * 0.001
        data['capacity'] = bytes_to_int(bs, 11, 4) * 0.001
        self.data.update(data)

    def parse_device_info(self, bs):
        data = {}
        data['function'] = FUNCTION.get(bytes_to_int(bs, 1, 1))
        data['model'] = (bs[3:17]).decode('utf-8')
        self.data.update(data)
