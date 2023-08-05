import logging
from .BaseClient import BaseClient
from .Utils import bytes_to_int, parse_temperature

# Read and parse BT-1 RS232 type bluetooth module connected to Renogy Rover/Wanderer/Adventurer
# series charge controllers. Also works with BT-2 RS485 module on Rover Elite, DC Charger etc.
# Does not support Communication Hub with multiple devices connected

DEVICE_ID = 255

READ_PARAMS = {
    'FUNCTION': 3,
    'REGISTER': 256,
    'WORDS': 34
}

WRITE_PARAMS_LOAD = {
    'FUNCTION': 6,
    'REGISTER': 266
}

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

class BTModuleClient(BaseClient):
    def __init__(self, config, on_data_callback=None):
        super().__init__(config)
        self.on_data_callback = on_data_callback

    def read_params(self):
        logging.info("reading params")
        request = self.create_generic_read_request(DEVICE_ID, READ_PARAMS["FUNCTION"], READ_PARAMS["REGISTER"], READ_PARAMS["WORDS"])
        self.device.characteristic_write_value(request)

    def on_data_received(self, value):
        operation = bytes_to_int(value, 1, 1)

        if operation == 3:
            logging.info("on_data_received: response for read operation")
            self.data = self.parse_charge_controller_info(value)
            if self.on_data_callback is not None:
                self.on_data_callback(self, self.data)
        elif operation == 6:
            logging.info("on_data_received: response for write operation")
            self.data = self.parse_set_load_response(value)
            if self.on_data_callback is not None:
                self.on_data_callback(self, self.data)
        else:
            logging.warn("on_data_received: unknown operation={}".format(operation))

    def set_load(self, value = 0):
        logging.info("setting load {}".format(value))
        request = self.create_generic_read_request(DEVICE_ID, WRITE_PARAMS_LOAD["FUNCTION"], WRITE_PARAMS_LOAD["REGISTER"], value)
        self.device.characteristic_write_value(request)

    def parse_charge_controller_info(self, bs):
        data = {}
        data['function'] = FUNCTION[bytes_to_int(bs, 1, 1)]
        data['battery_percentage'] = bytes_to_int(bs, 3, 2)
        data['battery_voltage'] = bytes_to_int(bs, 5, 2) * 0.1
        data['battery_current'] = bytes_to_int(bs, 7, 2) * 0.01
        data['battery_temperature'] = parse_temperature(bytes_to_int(bs, 10, 1))
        data['controller_temperature'] = parse_temperature(bytes_to_int(bs, 9, 1))
        data['load_status'] = LOAD_STATE[bytes_to_int(bs, 67, 1) >> 7]
        data['load_voltage'] = bytes_to_int(bs, 11, 2) * 0.1
        data['load_current'] = bytes_to_int(bs, 13, 2) * 0.01
        data['load_power'] = bytes_to_int(bs, 15, 2)
        data['pv_voltage'] = bytes_to_int(bs, 17, 2) * 0.1
        data['pv_current'] = bytes_to_int(bs, 19, 2) * 0.01
        data['pv_power'] = bytes_to_int(bs, 21, 2)
        data['max_charging_power_today'] = bytes_to_int(bs, 33, 2)
        data['max_discharging_power_today'] = bytes_to_int(bs, 35, 2)
        data['charging_amp_hours_today'] = bytes_to_int(bs, 37, 2)
        data['discharging_amp_hours_today'] = bytes_to_int(bs, 39, 2)
        data['power_generation_today'] = bytes_to_int(bs, 41, 2)
        data['power_consumption_today'] = bytes_to_int(bs, 43, 2)
        data['power_generation_total'] = bytes_to_int(bs, 59, 4)
        data['charging_status'] = CHARGING_STATE[bytes_to_int(bs, 68, 1)]
        return data

    def parse_set_load_response(self, bs):
        data = {}
        data['function'] = FUNCTION[bytes_to_int(bs, 1, 1)]
        data['load_status'] = bytes_to_int(bs, 5, 1)
        return data