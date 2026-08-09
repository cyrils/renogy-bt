# Based on the register map by john-in-france
# Repository: https://github.com/john-in-france/renogy-riv-ble-bridge
# Original Discussion: https://github.com/cyrils/renogy-bt/discussions/136

from .BaseClient import BaseClient
from .Utils import bytes_to_int, format_temperature

FUNCTION = {
    3: "READ",
    6: "WRITE"
}

OPERATING_MODE = {
    4: "line/charging",
    5: "inverting/battery"
}

class HFInverterClient(BaseClient):
    def __init__(self, config, on_data_callback=None, on_error_callback=None):
        super().__init__(config)
        self.on_data_callback = on_data_callback
        self.on_error_callback = on_error_callback
        self.data = {}
        self.sections = [
            {'register': 4000, 'words': 7, 'parser': self.parse_stats},
            {'register': 4109, 'words': 1, 'parser': self.parse_device_id},
            {'register': 4301, 'words': 1, 'parser': self.parse_ac_input_present},
            {'register': 4311, 'words': 8, 'parser': self.parse_inverter_model},
            {'register': 4328, 'words': 6, 'parser': self.parse_charging_info},
            {'register': 4405, 'words': 18, 'parser': self.parse_operating_info}
        ]

    def parse_stats(self, bs):
        data = {}
        data['function'] = FUNCTION.get(bytes_to_int(bs, 1, 1))
        data['ac_input_voltage'] = bytes_to_int(bs, 3, 2, scale=0.1)
        data['ac_input_frequency'] = bytes_to_int(bs, 5, 2, scale=0.1)
        data['ac_voltage_setting'] = bytes_to_int(bs, 7, 2, scale=0.1)
        data['battery_discharge_current'] = bytes_to_int(bs, 9, 2, scale=0.1)
        
        temp_unit = self.config['data']['temperature_unit']
        data['battery_temperature'] = format_temperature(bytes_to_int(bs, 13, 2, scale=0.1), temp_unit)
        data['internal_temperature'] = format_temperature(bytes_to_int(bs, 15, 2, scale=0.1), temp_unit)
        self.data.update(data)

    def parse_device_id(self, bs):
        data = { 'device_id': bytes_to_int(bs, 3, 2) }
        self.data.update(data)

    def parse_ac_input_present(self, bs):
        data = { 'ac_input_present': bytes_to_int(bs, 3, 2) }
        self.data.update(data)

    def parse_inverter_model(self, bs):
        data = { 'model': (bs[3:19]).decode('utf-8').rstrip('\x00').strip() }
        self.data.update(data)

    def parse_charging_info(self, bs):
        data = {}
        data['battery_current'] = bytes_to_int(bs, 3, 2, scale=0.1, signed=True)
        data['charging_active'] = bytes_to_int(bs, 11, 2)
        data['charging_power_amps'] = bytes_to_int(bs, 13, 2, scale=0.1)
        self.data.update(data)

    def parse_operating_info(self, bs):
        data = {}
        operating_mode = bytes_to_int(bs, 3, 2)
        data['operating_mode_raw'] = operating_mode
        data['operating_mode'] = OPERATING_MODE.get(operating_mode)
        data['charging_current'] = bytes_to_int(bs, 17, 2, scale=0.1)
        data['max_charging_current_setting'] = bytes_to_int(bs, 37, 2, scale=0.1)
        self.data.update(data)
