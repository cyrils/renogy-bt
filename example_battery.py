import logging
import configparser
import os
from renogybt import BatteryClient
from renogybt import DataLogger

logging.basicConfig(level=logging.DEBUG)
config_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'config.ini')

config = configparser.ConfigParser()
config.read(config_file)
data_logger: DataLogger = DataLogger(config)

def on_data_received(client: BatteryClient, data):
    logging.debug("{} => {}".format(client.device.alias(), data))
    client.disconnect()

logging.info(f"Starting client: {config['device']['alias']} => {config['device']['mac_addr']}")

BatteryClient(config, on_data_received).connect()
