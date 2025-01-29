from .BaseClient import BaseClient
from .Utils import bytes_to_int, format_temperature

# Client for Renogy LFP battery with built-in bluetooth / BT-2 module

FUNCTION = {
    3: "READ",
    6: "WRITE"
}

ALARMS = {
    0: "none",
    1: "below",
    2: "above",
    3: "other"
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
            {'register': 5035, 'words': 6, 'parser': self.parse_module_temp_info},
            {'register': 5042, 'words': 11, 'parser': self.parse_battery_info},
            {'register': 5100, 'words': 8, 'parser': self.parse_cell_alarms},
            {'register': 5106, 'words': 8, 'parser': self.parse_status},
            {'register': 5122, 'words': 8, 'parser': self.parse_device_info},
            {'register': 5223, 'words': 1, 'parser': self.parse_device_address},
            {'register': 5200, 'words': 21, 'parser': self.parse_device_configuration_1},
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
        data['cycles'] = bytes_to_int(bs, 15, 2)
        data['charge_limit_volts'] = bytes_to_int(bs, 17, 2, scale=0.1)
        data['discharge_limit_volts'] = bytes_to_int(bs, 19, 2, scale=0.1)
        data['charge_limit_amps'] = bytes_to_int(bs, 21, 2, scale=0.01)
        data['discharge_limit_amps'] = bytes_to_int(bs, 23, 2, scale=0.01, signed=True)
        self.data.update(data)

    def parse_device_info(self, bs):
        data = {}
        data['function'] = FUNCTION.get(bytes_to_int(bs, 1, 1))
        data['model'] = (bs[3:19]).decode('utf-8').rstrip('\x00')
        self.data.update(data)

    def parse_device_address(self, bs):
        data = {}
        data['device_id'] = bytes_to_int(bs, 3, 2)
        self.data.update(data)

    def parse_status(self, bs):
        data = {}
        data['function'] = FUNCTION.get(bytes_to_int(bs, 1, 1))
        i = bytes_to_int(bs, 3, 2)
        data['module_under_voltage_error'] = (i >> 15) & 1 
        data['charge_over_temp_error'] = (i >> 14) & 1 
        data['charge_under_temp_error'] = (i >> 13) & 1 
        data['discharge_over_temp_error'] = (i >> 12) & 1 
        data['discharge_under_temp_error'] = (i >> 11) & 1 
        data['discharge_over_current1_error'] = (i >> 10) & 1 
        data['charge_over_current1_error'] = (i >> 9) & 1 
        data['cell_over_voltage_error'] = (i >> 8) & 1 
        data['cell_under_voltage_error'] = (i >> 7) & 1 
        data['module_over_voltage_error'] = (i >> 6) & 1 
        data['discharge_over_current2_error'] = (i >> 5) & 1 
        data['charge_over_current2_error'] = (i >> 4) & 1 
        data['using_battery_module_power'] = (i >> 3) & 1 
        data['discharge_mosfet'] = (i >> 2) & 1 
        data['charge_mosfet'] = (i >> 1) & 1 
        data['short_circuit'] = i & 1
        
        i = bytes_to_int(bs, 5, 2)
        data['effective_charge_current'] = (i >> 15) & 1
        data['effective_discharge_current'] = (i >> 14) & 1
        data['heater_on'] = (i >> 13) & 1
        data['fully_charged'] = (i >> 11) & 1
        data['buzzer'] = (i >> 8) & 1
        data['discharge_high_temp_warn'] = (i >> 7) & 1
        data['discharge_low_temp_warn'] = (i >> 6) & 1
        data['charge_high_temp_warn'] = (i >> 5) & 1
        data['charge_low_temp_warn'] = (i >> 4) & 1
        data['module_high_voltage_warn'] = (i >> 3) & 1
        data['module_low_voltage_warn'] = (i >> 2) & 1
        data['cell_high_voltage_warn'] = (i >> 1) & 1
        data['cell_low_voltage_warn'] = i & 1
        
        i = bytes_to_int(bs, 7, 2)
        for j in range(0, self.data['cell_count']):
            data[f'cell_{j}_voltage_error'] = i & 1
            i = i >> 1

        i = bytes_to_int(bs, 9, 2)
        data['charge_enable'] = (i >> 7) & 1
        data['discharge_enable'] = (i >> 6) & 1
        data['charge_immediately'] = (i >> 5) & 1
        data['charge_immediately'] = (i >> 4) & 1
        data['request_full_charge'] = (i >> 3) & 1
        self.data.update(data)

    def parse_module_temp_info(self, bs):
        data = {}
        data['function' ] = FUNCTION.get(bytes_to_int(bs, 1, 1))
        data['bms_board_temp'] = bytes_to_int(bs, 3, 2, scale=0.1)
        data['environment_temperature_count'] = bytes_to_int(bs, 5, 2)
        for i in range(0, data['environment_temperature_count']):
            celcius = bytes_to_int(bs, 7 + i *2, 2, scale=0.1)
            data[f'environment_temperature_{i}'] = format_temperature(celcius, self.config['data']['temperature_unit'])

        data['heater_temperature_count'] = bytes_to_int(bs, 13, 2)
        for i in range(0, data['heater_temperature_count']):
            celcius =  bytes_to_int(bs, 15 + i *2, 2, scale=0.1)
            data[f'heater_temperature_{i}'] = format_temperature(celcius, self.config['data']['temperature_unit'])
        self.data.update(data)

    def parse_device_configuration_1(self, bs):
        data = {}
        data['function'] = FUNCTION.get(bytes_to_int(bs, 1, 1))
        data['config_cell_over_voltage_limit'] = bytes_to_int(bs, 3, 2, scale=0.1)
        data['config_cell_high_voltage_limit'] = bytes_to_int(bs, 5, 2, scale=0.1)
        data['config_cell_low_voltage_limit'] = bytes_to_int(bs, 7, 2, scale=0.1)
        data['config_cell_under_voltage_limit'] = bytes_to_int(bs, 9, 2, scale=0.1)
        data['config_charge_over_temp_limit'] = bytes_to_int(bs, 11, 2, scale=0.1)
        data['config_charge_high_temp_limit'] = bytes_to_int(bs, 13, 2, scale=0.1)
        data['config_charge_low_temp_limit'] = bytes_to_int(bs, 15, 2, scale=0.1)
        data['config_charge_under_temp_limit'] = bytes_to_int(bs, 17, 2, scale=0.1)
        data['config_charge_over2_current_limit'] = bytes_to_int(bs, 19, 2, scale=0.01)
        data['config_charge_over_current_limit'] = bytes_to_int(bs, 21, 2, scale=0.01)
        data['config_charge_high_current_limit'] = bytes_to_int(bs, 23, 2, scale=0.01)
        data['config_module_over_voltage_limit'] = bytes_to_int(bs, 25, 2, scale=0.1)
        data['config_module_high_voltage_limit'] = bytes_to_int(bs, 27, 2, scale=0.1)
        data['config_module_low_voltage_limit'] = bytes_to_int(bs, 29, 2, scale=0.1)
        data['config_module_under_voltage_limit'] = bytes_to_int(bs, 31, 2, scale=0.1)
        data['config_discharge_over_temp_limit'] = bytes_to_int(bs, 33, 2, scale=0.1)
        data['config_discharge_high_temp_limit'] = bytes_to_int(bs, 35, 2, scale=0.1)
        data['config_discharge_low_temp_limit'] = bytes_to_int(bs, 37, 2, scale=0.1, signed=True)
        data['config_discharge_under_temp_limit'] = bytes_to_int(bs, 39, 2, scale=0.1, signed=True)
        data['config_discharge_over2_current_limit'] = bytes_to_int(bs, 41, 2, scale=0.01, signed=True)
        data['config_discharge_over_current_limit'] = bytes_to_int(bs, 43, 2, scale=0.01, signed=True)
        data['config_discharge_high_current_limit'] = bytes_to_int(bs, 45, 2, scale=0.01, signed=True) 
        self.data.update(data)

    def parse_cell_alarms(self, bs):
        data = {}
        data['function'] = FUNCTION.get(bytes_to_int(bs, 1, 1)) 
        cell_voltage_alarms = bytes_to_int(bs, 3, 4)
        cell_temperature_alarms = bytes_to_int(bs, 7, 4)

        for i in range(0, self.data['cell_count']):
            data[f'cell_voltage_alarm_{i}'] = ALARMS[cell_voltage_alarms & 3]
            data[f'cell_temperature_alarm_{i}'] = ALARMS[cell_temperature_alarms & 3]
            cell_voltage_alarms = cell_voltage_alarms >> 2
            cell_temperature_alarms = cell_temperature_alarms >> 2

        self.data.update(data)
