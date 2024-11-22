import logging
from .BaseClient import BaseClient
from .Utils import bytes_to_int

FUNCTION = {
    3: "READ",
    6: "WRITE"
}

CHARGING_STATE = {
    0: 'deactivated',
    1: 'activated',
    2: 'mppt',
    3: 'equalizing',
    4: 'boost',
    5: 'floating',
    6: 'current limiting'
}

BATTERY_TYPE = {
    1: 'open',
    2: 'sealed',
    3: 'gel',
    4: 'lithium',
    5: 'custom'
}

class InverterClient(BaseClient):
    def __init__(self, config, on_data_callback=None, on_error_callback=None):
        super().__init__(config)
        self.on_data_callback = on_data_callback
        self.on_error_callback = on_error_callback
        self.data = { 'function': 'READ' }
        self.sections = [
            {'register': 4000, 'words': 8, 'parser': self.parse_inverter_stats},
            {'register': 4311, 'words': 8, 'parser': self.parse_inverter_model},
            {'register': 4329, 'words': 5, 'parser': self.parse_solar_charging},
            {'register': 4410, 'words': 4, 'parser': self.parse_battery_info}
        ]

    def parse_inverter_stats(self, bs):
        data = {}
        data['function'] = FUNCTION.get(bytes_to_int(bs, 1, 1))
        data['input_voltage'] = bytes_to_int(bs, 3, 2, scale=0.1)
        data['input_current'] = bytes_to_int(bs, 5, 2, scale=0.01)
        data['output_voltage'] = bytes_to_int(bs, 7, 2, scale=0.1)
        data['output_current'] = bytes_to_int(bs, 9, 2, scale=0.01)
        data['frequency'] = bytes_to_int(bs, 11, 2, scale=0.01)
        data['battery_voltage'] = bytes_to_int(bs, 13, 2, scale=0.1)
        data['temperature'] = bytes_to_int(bs, 15, 2, scale=0.1)
        self.data.update(data)

    def parse_inverter_model(self, bs):
        data = {}
        data['model'] = (bs[3:15]).decode('utf-8')
        self.data.update(data)

    def parse_solar_charging(self, bs):
        data = {}
        data['solar_voltage'] = bytes_to_int(bs, 3, 2, scale=0.1)
        data['solar_current'] = bytes_to_int(bs, 5, 2, scale=0.1)
        data['solar_power'] = bytes_to_int(bs, 7, 2)
        data['charging_status'] = CHARGING_STATE.get(bytes_to_int(bs, 9, 2))
        data['charging_power'] = bytes_to_int(bs, 11, 2)
        self.data.update(data)

    def parse_battery_info(self, bs):
        data = {}
        data['load_power'] = bytes_to_int(bs, 3, 2)
        data['charging_current'] = bytes_to_int(bs, 7, 2, scale=0.01)
        self.data.update(data)
