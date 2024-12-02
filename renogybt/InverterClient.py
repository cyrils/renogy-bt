from .BaseClient import BaseClient
from .Utils import bytes_to_int

FUNCTION = {
    3: "READ",
    6: "WRITE"
}

CHARGING_STATE = {
    0: 'deactivated',
    1: 'constant current',
    2: 'constant voltage',
    4: 'floating',
    6: 'battery activation',
    7: 'battery disconnecting'
}

class InverterClient(BaseClient):
    def __init__(self, config, on_data_callback=None, on_error_callback=None):
        super().__init__(config)
        self.on_data_callback = on_data_callback
        self.on_error_callback = on_error_callback
        self.data = {}
        self.sections = [
            {'register': 4000, 'words': 10, 'parser': self.parse_inverter_stats},
            {'register': 4109, 'words': 1, 'parser': self.parse_device_id},
            {'register': 4311, 'words': 8, 'parser': self.parse_inverter_model},
            {'register': 4327, 'words': 7, 'parser': self.parse_charging_info},
            {'register': 4408, 'words': 6, 'parser': self.parse_load_info}
        ]

    def parse_inverter_stats(self, bs):
        data = {}
        data['function'] = FUNCTION.get(bytes_to_int(bs, 1, 1))
        data['input_voltage'] = bytes_to_int(bs, 3, 2, scale=0.1)
        data['input_current'] = bytes_to_int(bs, 5, 2, scale=0.01)
        data['output_voltage'] = bytes_to_int(bs, 7, 2, scale=0.1)
        data['output_current'] = bytes_to_int(bs, 9, 2, scale=0.01)
        data['output_frequency'] = bytes_to_int(bs, 11, 2, scale=0.01)
        data['battery_voltage'] = bytes_to_int(bs, 13, 2, scale=0.1)
        data['temperature'] = bytes_to_int(bs, 15, 2, scale=0.1)
        data['input_frequency'] = bytes_to_int(bs, 21, 2, scale=0.01)
        self.data.update(data)

    def parse_device_id(self, bs):
        data = { 'device_id': bytes_to_int(bs, 3, 2) }
        self.data.update(data)

    def parse_inverter_model(self, bs):
        data = { 'model': (bs[3:19]).decode('utf-8').rstrip('\x00') }
        self.data.update(data)

    def parse_charging_info(self, bs):
        data = {}
        data['battery_percentage'] = bytes_to_int(bs, 3, 2)
        data['charging_current'] = bytes_to_int(bs, 5, 2, scale=0.1, signed=True)
        data['solar_voltage'] = bytes_to_int(bs, 7, 2, scale=0.1)
        data['solar_current'] = bytes_to_int(bs, 9, 2, scale=0.1)
        data['solar_power'] = bytes_to_int(bs, 11, 2)
        data['charging_status'] = CHARGING_STATE.get(bytes_to_int(bs, 13, 2))
        data['charging_power'] = bytes_to_int(bs, 15, 2)
        self.data.update(data)

    def parse_load_info(self, bs):
        data = {}
        data['load_curent'] = bytes_to_int(bs, 3, 2, scale=0.1)
        data['load_active_power'] = bytes_to_int(bs, 5, 2)
        data['load_apparent_power'] = bytes_to_int(bs, 7, 2)
        data['line_charging_current'] = bytes_to_int(bs, 11, 2, scale=0.1)
        data['load_percentage'] = bytes_to_int(bs, 13, 2)
        self.data.update(data)
