import logging
from .BaseClient import BaseClient
from .Utils import bytes_to_int, parse_temperature

# Read and parse BT-1 RS232 type bluetooth module connected to Renogy Rover/Wanderer/Adventurer
# series charge controllers. Also works with BT-2 RS485 module on Rover Elite, DC Charger etc.
# Does not support Communication Hub with multiple devices connected

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

LOAD_STATE = {
  0: 'off',
  1: 'on'
}

BATTERY_TYPE = {
    1: 'open',
    2: 'sealed',
    3: 'gel',
    4: 'lithium',
    5: 'custom'
}

class RoverClient(BaseClient):
    def __init__(self, config, on_data_callback=None, on_error_callback=None):
        super().__init__(config)
        self.on_data_callback = on_data_callback
        self.on_error_callback = on_error_callback
        self.data = {}
        self.sections = [
            {'register': 12, 'words': 8, 'parser': self.parse_device_info},
            {'register': 26, 'words': 1, 'parser': self.parse_device_address},
            {'register': 256, 'words': 34, 'parser': self.parse_chargin_info},
            {'register': 57348, 'words': 1, 'parser': self.parse_battery_type}
        ]
        self.set_load_params = {'function': 6, 'register': 266}

    async def on_data_received(self, response):
        operation = bytes_to_int(response, 1, 1)
        if operation == 6: # write operation
            self.parse_set_load_response(response)
            self.on_write_operation_complete()
            self.data = {}
        else:
            # read is handled in base class
            await super().on_data_received(response)

    def on_write_operation_complete(self):
        logging.info("on_write_operation_complete")
        if self.on_data_callback is not None:
            self.on_data_callback(self, self.data)

    def set_load(self, value = 0):
        logging.info("setting load {}".format(value))
        request = self.create_generic_read_request(self.device_id, self.set_load_params["function"], self.set_load_params["register"], value)
        self.bleManager.characteristic_write_value(request)

    def parse_device_info(self, bs):
        data = {}
        data['function'] = FUNCTION.get(bytes_to_int(bs, 1, 1))
        data['model'] = (bs[3:17]).decode('utf-8').strip()
        self.data.update(data)

    def parse_device_address(self, bs):
        data = {}
        data['device_id'] = bytes_to_int(bs, 4, 1)
        self.data.update(data)

    def parse_chargin_info(self, bs):
        data = {}

        temp_unit = self.config['data']['temperature_unit']

        data['device_info'] = {}

        data['device_info']['function']= {}
        data['device_info']['function']['value'] = FUNCTION.get(bytes_to_int(bs, 1, 1))
        data['device_info']['function']['device_class'] = ""
        data['device_info']['function']['unit_of_measurement'] = ""
        data['device_info']['function']['icon'] = "mdi:desktop-classic"

        data['device_info']['battery_percentage']= {}
        data['device_info']['battery_percentage']['value'] = bytes_to_int(bs, 3, 2)
        data['device_info']['battery_percentage']['device_class'] = "battery"
        data['device_info']['battery_percentage']['unit_of_measurement'] = "%"
        data['device_info']['battery_percentage']['icon'] = "mdi:battery-charging"

        data['device_info']['battery_voltage']= {}
        data['device_info']['battery_voltage']['value'] = bytes_to_int(bs, 5, 2, scale = 0.1)
        data['device_info']['battery_voltage']['device_class'] = "voltage"
        data['device_info']['battery_voltage']['unit_of_measurement'] = "V"
        data['device_info']['battery_voltage']['icon'] = "mdi:sine-wave"

        data['device_info']['battery_current']= {}
        data['device_info']['battery_current']['value'] = bytes_to_int(bs, 7, 2, scale = 0.01)
        data['device_info']['battery_current']['device_class'] = "current"
        data['device_info']['battery_current']['unit_of_measurement'] = "A"
        data['device_info']['battery_current']['icon'] = "mdi:current-ac"

        data['device_info']['battery_temperature']= {}
        data['device_info']['battery_temperature']['value'] = parse_temperature(bytes_to_int(bs, 10, 1), temp_unit)
        data['device_info']['battery_temperature']['device_class'] = "temperature"
        data['device_info']['battery_temperature']['unit_of_measurement'] = temp_unit
        data['device_info']['battery_temperature']['icon'] = "mdi:temperature-celsius"

        data['device_info']['controller_temperature']= {}
        data['device_info']['controller_temperature']['value'] = parse_temperature(bytes_to_int(bs, 9, 1), temp_unit)
        data['device_info']['controller_temperature']['device_class'] = "temperature"
        data['device_info']['controller_temperature']['unit_of_measurement'] = temp_unit
        data['device_info']['controller_temperature']['icon'] = "mdi:temperature-celsius"

        data['device_info']['load_status']= {}
        data['device_info']['load_status']['value'] = LOAD_STATE.get(bytes_to_int(bs, 67, 1) >> 7)
        data['device_info']['load_status']['device_class'] = ""
        data['device_info']['load_status']['unit_of_measurement'] = ""
        data['device_info']['load_status']['icon'] = "mdi:power-plug-battery-outline"

        data['device_info']['load_voltage']= {}
        data['device_info']['load_voltage']['value'] = bytes_to_int(bs, 11, 2, scale = 0.1)
        data['device_info']['load_voltage']['device_class'] = "voltage"
        data['device_info']['load_voltage']['unit_of_measurement'] = "V"
        data['device_info']['load_voltage']['icon'] = "mdi:sine-wave"

        data['device_info']['load_current']= {}
        data['device_info']['load_current']['value'] = bytes_to_int(bs, 13, 2, scale = 0.01)
        data['device_info']['load_current']['device_class'] = "current"
        data['device_info']['load_current']['unit_of_measurement'] = "A"
        data['device_info']['load_current']['icon'] = "mdi:current-ac"

        data['device_info']['load_power']= {}
        data['device_info']['load_power']['value'] = bytes_to_int(bs, 15, 2)
        data['device_info']['load_power']['device_class'] = "power"
        data['device_info']['load_power']['unit_of_measurement'] = "W"
        data['device_info']['load_power']['icon'] = "mdi:flash"

        data['device_info']['pv_voltage']= {}
        data['device_info']['pv_voltage']['value'] = bytes_to_int(bs, 17, 2, scale = 0.1) 
        data['device_info']['pv_voltage']['device_class'] = "voltage"
        data['device_info']['pv_voltage']['unit_of_measurement'] = "V"
        data['device_info']['pv_voltage']['icon'] = "mdi:sine-wave"

        data['device_info']['pv_current']= {}
        data['device_info']['pv_current']['value'] = bytes_to_int(bs, 19, 2, scale = 0.01)
        data['device_info']['pv_current']['device_class'] = "current"
        data['device_info']['pv_current']['unit_of_measurement'] = "A"
        data['device_info']['pv_current']['icon'] = "mdi:current-ac"

        data['device_info']['pv_power']= {}
        data['device_info']['pv_power']['value'] = bytes_to_int(bs, 21, 2)
        data['device_info']['pv_power']['device_class'] = "power"
        data['device_info']['pv_power']['unit_of_measurement'] = "W"
        data['device_info']['pv_power']['icon'] = "mdi:flash"

        data['device_info']['max_charging_power_today']= {}
        data['device_info']['max_charging_power_today']['value'] = bytes_to_int(bs, 33, 2)
        data['device_info']['max_charging_power_today']['device_class'] = "power"
        data['device_info']['max_charging_power_today']['unit_of_measurement'] = "W"
        data['device_info']['max_charging_power_today']['icon'] = "mdi:flash"

        data['device_info']['max_discharging_power_today']= {}
        data['device_info']['max_discharging_power_today']['value'] = bytes_to_int(bs, 35, 2)
        data['device_info']['max_discharging_power_today']['device_class'] = "power"
        data['device_info']['max_discharging_power_today']['unit_of_measurement'] = "W"
        data['device_info']['max_discharging_power_today']['icon'] = "mdi:flash"

        data['device_info']['charging_amp_hours_today']= {}
        data['device_info']['charging_amp_hours_today']['value'] = bytes_to_int(bs, 37, 2)
        data['device_info']['charging_amp_hours_today']['device_class'] = "current"
        data['device_info']['charging_amp_hours_today']['unit_of_measurement'] = "A"
        data['device_info']['charging_amp_hours_today']['icon'] = "mdi:current-ac"

        data['device_info']['discharging_amp_hours_today']= {}
        data['device_info']['discharging_amp_hours_today']['value'] = bytes_to_int(bs, 39, 2)
        data['device_info']['discharging_amp_hours_today']['device_class'] = "current"
        data['device_info']['discharging_amp_hours_today']['unit_of_measurement'] = "A"
        data['device_info']['discharging_amp_hours_today']['icon'] = "mdi:current-ac"

        data['device_info']['power_generation_today']= {}
        data['device_info']['power_generation_today']['value'] = bytes_to_int(bs, 41, 2)
        data['device_info']['power_generation_today']['device_class'] = "power"
        data['device_info']['power_generation_today']['unit_of_measurement'] = "W"
        data['device_info']['power_generation_today']['icon'] = "mdi:flash"

        data['device_info']['power_consumption_today']= {}
        data['device_info']['power_consumption_today']['value'] = bytes_to_int(bs, 43, 2)
        data['device_info']['power_consumption_today']['device_class'] = "power"
        data['device_info']['power_consumption_today']['unit_of_measurement'] = "W"
        data['device_info']['power_consumption_today']['icon'] = "mdi:flash"

        data['device_info']['power_generation_total']= {}
        data['device_info']['power_generation_total']['value'] = bytes_to_int(bs, 59, 4)
        data['device_info']['power_generation_total']['device_class'] = "power"
        data['device_info']['power_generation_total']['unit_of_measurement'] = "W"
        data['device_info']['power_generation_total']['icon'] = "mdi:flash"

        data['device_info']['charging_status']= {}
        data['device_info']['charging_status']['value'] = CHARGING_STATE.get(bytes_to_int(bs, 68, 1))
        data['device_info']['charging_status']['device_class'] = ""
        data['device_info']['charging_status']['unit_of_measurement'] = ""
        data['device_info']['charging_status']['icon'] = "mdi:connection"

        self.data.update(data)

    def parse_battery_type(self, bs):
        data = {}
        data['function'] = FUNCTION.get(bytes_to_int(bs, 1, 1))
        data['battery_type'] = BATTERY_TYPE.get(bytes_to_int(bs, 3, 2))
        self.data.update(data)

    def parse_set_load_response(self, bs):
        data = {}
        data['function'] = FUNCTION.get(bytes_to_int(bs, 1, 1))
        data['load_status'] = bytes_to_int(bs, 5, 1)
        self.data.update(data)
