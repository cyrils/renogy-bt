import logging
from .BaseClient import BaseClient
from .Utils import bytes_to_int

FUNCTION = {
    3: "READ",
    6: "WRITE"
}

class InverterClient(BaseClient):
    def __init__(self, config, on_data_callback=None):
        super().__init__(config)
        self.on_data_callback = on_data_callback
        self.data = { 'function': 'READ' }
        self.sections = [
            {'register': 4000, 'words': 8, 'parser': self.parse_inverter_stats},
            {'register': 4311, 'words': 8, 'parser': self.parse_inverter_model},
            {'register': 4329, 'words': 5, 'parser': self.parse_solar_charging},
            {'register': 4410, 'words': 2, 'parser': self.parse_inverter_load},
        ]

    def parse_inverter_stats(self, bs):
        logging.info(f"parse_inverter_stats {bs.hex()}")
        data = {}
        data['function'] = FUNCTION.get(bytes_to_int(bs, 1, 1))
        data['uei_voltage'] = bytes_to_int(bs, 3, 2)
        data['uei_current'] = bytes_to_int(bs, 5, 2)
        data['voltage'] = bytes_to_int(bs, 7, 2)
        data['load_current'] = bytes_to_int(bs, 9, 2)
        data['frequency'] = bytes_to_int(bs, 11, 2)
        data['temperature'] = bytes_to_int(bs, 13, 2)
        self.data.update(data)

    def parse_inverter_model(self, bs):
        logging.info(f"parse_inverter_model {bs.hex()}")
        data = {}
        data['model'] = (bs[3:17]).decode('utf-8')
        self.data.update(data)

    def parse_solar_charging(self, bs):
        logging.info(f"parse_solar_charging {bs.hex()}")
        data = {}
        data['solar_voltage'] = bytes_to_int(bs, 3, 2)
        data['solar_current'] = bytes_to_int(bs, 5, 2)
        data['solar_power'] = bytes_to_int(bs, 7, 2)
        data['solar_charging_state'] = bytes_to_int(bs, 9, 2)
        data['solar_charging_power'] = bytes_to_int(bs, 11, 2)
        self.data.update(data)

    def parse_inverter_load(self, bs):
        logging.info(f"parse_inverter_load {bs.hex()}")
        data = {}
        data['load_power'] = bytes_to_int(bs, 3, 2)
        data['charging_current'] = bytes_to_int(bs, 5, 2)
        self.data.update(data)
