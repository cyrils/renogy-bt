import logging
from .BaseClient import BaseClient
from .Utils import bytes_to_int, parse_temperature

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
    6: 'current limiting',
    8: 'alternator direct'
}

BATTERY_TYPE = {
    1: 'open',
    2: 'sealed',
    3: 'gel',
    4: 'lithium',
    5: 'custom'
}

class DCChargerClient(BaseClient):
    def __init__(self, config, on_data_callback=None, on_error_callback=None):
        super().__init__(config)
        self.on_data_callback = on_data_callback
        self.on_error_callback = on_error_callback
        self.data = {}
        self.sections = [
            {'register': 12, 'words': 8, 'parser': self.parse_device_info},
            {'register': 26, 'words': 1, 'parser': self.parse_device_address},
            {'register': 256, 'words': 30, 'parser': self.parse_charging_info},
            {'register': 288, 'words': 3, 'parser': self.parse_state},
            {'register': 57348, 'words': 1, 'parser': self.parse_battery_type}
        ]

    def parse_device_info(self, bs):
        data = {}
        data['function'] = FUNCTION.get(bytes_to_int(bs, 1, 1))
        data['model'] = (bs[3:19]).decode('utf-8').strip()
        self.data.update(data)

    def parse_device_address(self, bs):
        data = {}
        data['device_id'] = bytes_to_int(bs, 4, 1)
        self.data.update(data)

    def parse_charging_info(self, bs):
        data = {}
        temp_unit = self.config['data']['temperature_unit']
        data['function'] = FUNCTION.get(bytes_to_int(bs, 1, 1))
        data['battery_percentage'] = bytes_to_int(bs, 3, 2)
        data['battery_voltage'] = bytes_to_int(bs, 5, 2, scale = 0.1)
        data['combined_charge_current'] = bytes_to_int(bs, 7, 2, scale = 0.01)
        data['controller_temperature'] = parse_temperature(bytes_to_int(bs, 9, 1), temp_unit)
        data['battery_temperature'] = parse_temperature(bytes_to_int(bs, 10, 1), temp_unit)
        data['alternator_voltage'] = bytes_to_int(bs, 11, 2, scale = 0.1)
        data['alternator_current'] = bytes_to_int(bs, 13, 2, scale = 0.01)
        data['alternator_power'] = bytes_to_int(bs, 15, 2)
        data['pv_voltage'] = bytes_to_int(bs, 17, 2, scale = 0.1) 
        data['pv_current'] = bytes_to_int(bs, 19, 2, scale = 0.01)
        data['pv_power'] = bytes_to_int(bs, 21, 2)
        data['battery_min_voltage_today'] = bytes_to_int(bs, 25, 2, scale=0.1)
        data['battery_max_voltage_today'] = bytes_to_int(bs, 27, 2, scale=0.1)
        data['battery_max_current_today'] = bytes_to_int(bs, 29, 2, scale=0.01)
        data['max_charging_power_today'] = bytes_to_int(bs, 33, 2)
        data['charging_amp_hours_today'] = bytes_to_int(bs, 37, 2)
        data['power_generation_today'] = bytes_to_int(bs, 41, 2)
        data['total_working_days'] = bytes_to_int(bs, 45, 2)
        data['count_battery_overdischarged'] = bytes_to_int(bs, 47, 2)
        data['count_battery_fully_charged'] = bytes_to_int(bs, 49, 2)
        data['battery_ah_total_accumulated'] = bytes_to_int(bs, 51, 4)
        data['power_generation_total'] = bytes_to_int(bs, 59, 4)
        self.data.update(data)

    def parse_state(self, bs):
        data = {}
        alarms = {}
        data['charging_status'] = CHARGING_STATE.get(bytes_to_int(bs, 2, 1))
        
        byte = bytes_to_int(bs, 4, 1)
        alarms['low_temp_shutdown'] = (byte >> 11) & 1
        alarms['bms_overcharge_protection'] = (byte >> 10) & 1
        alarms['starter_reverse_polarity'] = (byte >> 9) & 1
        alarms['alternator_over_voltage'] = (byte >> 8) & 1
        alarms['alternator_over_current'] = (byte >> 4) & 1
        alarms['controller_over_temp_2'] = (byte >> 3) & 1

        byte = bytes_to_int(bs, 6, 1)
        alarms['solar_reverse_polarity'] = (byte >> 12) & 1
        alarms['solar_over_voltage'] = (byte >> 9) & 1
        alarms['solar_over_current'] = (byte >> 7) & 1
        alarms['battery_over_temperature'] = (byte >> 6) & 1
        alarms['controller_over_temp'] = (byte >> 5) & 1
        alarms['battery_low_voltage'] = (byte >> 2) &  1
        alarms['battery_over_voltage'] = (byte >> 1) &  1
        alarms['battery_over_discharge'] = byte &  1

        key = next((key for key, value in alarms.items() if value > 0), None)
        if (key != None): data['error'] = key

        self.data.update(data)

    def parse_battery_type(self, bs):
        data = {}
        data['function'] = FUNCTION.get(bytes_to_int(bs, 1, 1))
        data['battery_type'] = BATTERY_TYPE.get(bytes_to_int(bs, 3, 2))
        self.data.update(data)
