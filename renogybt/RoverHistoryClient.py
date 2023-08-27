import logging
from .BaseClient import BaseClient
from .Utils import bytes_to_int, parse_temperature

# Read and parse BT-1 RS232 type bluetooth module connected to Renogy Rover/Wanderer/Adventurer
# series charge controllers. Also works with BT-2 RS485 module on Rover Elite, DC Charger etc.
# Does not support Communication Hub with multiple devices connected

DEVICE_ID = 255

FUNCTION = {
    3: "READ",
    6: "WRITE"
}

class RoverHistoryClient(BaseClient):
    def __init__(self, config, on_data_callback=None):
        super().__init__(config)
        self.on_data_callback = on_data_callback
        self.data = {
            'power_generation': [],
            'amp_hours': [],
            'max_power': []
        }
        self.device_id = DEVICE_ID
        self.sections = [
            {'register': 61440, 'words': 16, 'parser': self.parse_historical_data},
            {'register': 61441, 'words': 15, 'parser': self.parse_historical_data},
            {'register': 61442, 'words': 14, 'parser': self.parse_historical_data},
            {'register': 61443, 'words': 13, 'parser': self.parse_historical_data},
            {'register': 61444, 'words': 12, 'parser': self.parse_historical_data},
            {'register': 61445, 'words': 11, 'parser': self.parse_historical_data},
            {'register': 61446, 'words': 10, 'parser': self.parse_historical_data}
        ]

    def on_data_received(self, response):
        operation = bytes_to_int(response, 1, 1)
        if operation == 3: # read operation
            logging.info(f"on_data_received: response for read operation {response.hex()}")
            index, section = self.find_section_by_response(response)
            parsed_data = section['parser'](response) if section['parser'] != None else {}
            self.data['power_generation'].append(parsed_data['power_generation'])
            self.data['amp_hours'].append(parsed_data['amp_hours'])
            self.data['max_power'].append(parsed_data['max_power'])

            if index >= len(self.sections) - 1: # last section
                self.on_read_operation_complete()
                self.data = {}
            else:
                self.read_section(index + 1)
        else:
            logging.warn("on_data_received: unknown operation={}".format(operation))

    def parse_historical_data(self, bs):
        data = {}
        data['power_generation'] = bytes_to_int(bs, 19, 2)
        data['amp_hours'] = bytes_to_int(bs, 15, 2)
        data['max_power'] = bytes_to_int(bs, 13, 2)
        return data
