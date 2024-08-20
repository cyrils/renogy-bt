from .BaseClient import BaseClient
from .Utils import bytes_to_int

# Retrieve last 7 days of historical data from Rover/Wanderer/Adventurer

class RoverHistoryClient(BaseClient):
    def __init__(self, config, on_data_callback=None, on_error_callback=None):
        super().__init__(config)
        self.on_data_callback = on_data_callback
        self.on_error_callback = on_error_callback
        self.data = {
            'function': 'READ',
            'daily_power_generation': [],
            'daily_charge_ah': [],
            'daily_max_power': []
        }
        self.sections = [
            {'register': 61446, 'words': 10, 'parser': self.parse_historical_data},
            {'register': 61445, 'words': 10, 'parser': self.parse_historical_data},
            {'register': 61444, 'words': 10, 'parser': self.parse_historical_data},
            {'register': 61443, 'words': 10, 'parser': self.parse_historical_data},
            {'register': 61442, 'words': 10, 'parser': self.parse_historical_data},
            {'register': 61441, 'words': 10, 'parser': self.parse_historical_data},
            {'register': 61440, 'words': 10, 'parser': self.parse_historical_data}
        ]

    def parse_historical_data(self, bs):
        self.data['daily_power_generation'].append(bytes_to_int(bs, 19, 2))
        self.data['daily_charge_ah'].append(bytes_to_int(bs, 15, 2))
        self.data['daily_max_power'].append(bytes_to_int(bs, 11, 2))
