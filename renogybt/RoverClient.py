import asyncio
import logging
from .BaseClient import BaseClient
from .Utils import bytes_to_int, parse_temperature

# Read and parse BT-1/BT-2 type bluetooth modules connected to Renogy Rover/Wanderer/Adventurer    

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
        self.data = {
         #   'function': 'READ',
            'daily_power_generation Wh': [],
            'daily_charge Ah': [],
            'daily_max_power W': []
        }
        self.sections = [
            {'register': 12, 'words': 8, 'parser': self.parse_device_info},
            {'register': 26, 'words': 1, 'parser': self.parse_device_address},
            {'register': 256, 'words': 34, 'parser': self.parse_chargin_info},
            {'register': 57348, 'words': 1, 'parser': self.parse_battery_type},
            {'register': 61446, 'words': 10, 'parser': self.parse_historical_data},
            {'register': 61445, 'words': 10, 'parser': self.parse_historical_data},
            {'register': 61444, 'words': 10, 'parser': self.parse_historical_data},
            {'register': 61443, 'words': 10, 'parser': self.parse_historical_data},
            {'register': 61442, 'words': 10, 'parser': self.parse_historical_data},
            {'register': 61441, 'words': 10, 'parser': self.parse_historical_data},
            {'register': 61440, 'words': 10, 'parser': self.parse_historical_data}
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
        asyncio.create_task(self.ble_manager.characteristic_write_value(request))

    def parse_device_info(self, bs):
        data = {}
#        data['function'] = FUNCTION.get(bytes_to_int(bs, 1, 1))
#        data['model'] = (bs[3:19]).decode('utf-8').strip()
        self.data.update(data)

    def parse_device_address(self, bs):
        data = {}
#        data['device_id'] = bytes_to_int(bs, 4, 1)
        self.data.update(data)

    def parse_chargin_info(self, bs):
        data = {}
        temp_unit = self.config['data']['temperature_unit']
 #       data['function'] = FUNCTION.get(bytes_to_int(bs, 1, 1))
        data['battery_percentage'] = bytes_to_int(bs, 3, 2)
        data['battery_voltage V'] = bytes_to_int(bs, 5, 2, scale = 0.1)
        data['battery_current A'] = bytes_to_int(bs, 7, 2, scale = 0.01)
        data['battery_temperature C'] = parse_temperature(bytes_to_int(bs, 10, 1), temp_unit)      
        data['controller_temperature C'] = parse_temperature(bytes_to_int(bs, 9, 1), temp_unit)    
        data['load_status'] = LOAD_STATE.get(bytes_to_int(bs, 67, 1) >> 7)
        data['load_voltage V'] = bytes_to_int(bs, 11, 2, scale = 0.1)
        data['load_current A'] = bytes_to_int(bs, 13, 2, scale = 0.01)
        data['load_power W'] = bytes_to_int(bs, 15, 2)
        data['solarpv_voltage V'] = bytes_to_int(bs, 17, 2, scale = 0.1)
        data['solarpv_current A'] = bytes_to_int(bs, 19, 2, scale = 0.01)
        data['solarpv_power W'] = bytes_to_int(bs, 21, 2)
        data['max_charging_power_today W'] = bytes_to_int(bs, 33, 2)
        data['max_discharging_power_today W'] = bytes_to_int(bs, 35, 2)
        data['charging_amp_hours_today Ah'] = bytes_to_int(bs, 37, 2)
        data['discharging_amp_hours_today Ah'] = bytes_to_int(bs, 39, 2)
        data['power_generation_today Wh'] = bytes_to_int(bs, 41, 2)
        data['power_consumption_today Wh'] = bytes_to_int(bs, 43, 2)
        data['power_generation_total Wh'] = bytes_to_int(bs, 59, 4)
        data['charging_status'] = CHARGING_STATE.get(bytes_to_int(bs, 68, 1))
        self.data.update(data)

    def parse_battery_type(self, bs):
        data = {}
  #      data['function'] = FUNCTION.get(bytes_to_int(bs, 1, 1))
  #      data['battery_type'] = BATTERY_TYPE.get(bytes_to_int(bs, 3, 2))
        self.data.update(data)

    def parse_set_load_response(self, bs):
        data = {}
   #     data['function'] = FUNCTION.get(bytes_to_int(bs, 1, 1))
        data['load_status'] = bytes_to_int(bs, 5, 1)
        self.data.update(data)


#Historical Data
    def parse_historical_data(self, bs):
        logging.info(f"Raw historical data: {bs.hex()}")
        self.data['daily_power_generation Wh'].append(bytes_to_int(bs, 9, 2))
        self.data['daily_charge Ah'].append(bytes_to_int(bs, 5, 2))
        self.data['daily_max_power W'].append(bytes_to_int(bs, 9, 2))
