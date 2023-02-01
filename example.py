import logging
import configparser
from renogybtone import BTOneClient
from renogybtone import DataLogger

logging.basicConfig(level=logging.DEBUG)

config = configparser.ConfigParser()
config.read('config.ini')
data_logger: DataLogger = DataLogger(config)

def on_data_received(client, data):
    logging.debug("{} => {}".format(client.device.alias(), data))
    if client.config['remote_logging']['enabled'] == True:
        data_logger.log_remote(json_data=data)
    if client.config['mqtt']['enabled'] == True:
        data_logger.log_mqtt(json_data=data)
    if client.config['device']['poll_data'] != True:
        client.disconnect()

logging.info(f"Starting client: {config['device']['alias']} => {config['device']['mac_addr']}")

BTOneClient(config, on_data_received).connect()
