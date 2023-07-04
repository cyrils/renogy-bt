import logging
import configparser
import os
from renogybt import BTOneClient
from renogybt import DataLogger

logging.basicConfig(level=logging.DEBUG)
config_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'config.ini')

config = configparser.ConfigParser()
config.read(config_file)
data_logger: DataLogger = DataLogger(config)

def on_data_received(client: BTOneClient, data):
    logging.debug("{} => {}".format(client.device.alias(), data))
    if config['remote_logging'].getboolean('enabled'):
        data_logger.log_remote(json_data=data)
    if config['mqtt'].getboolean('enabled'):
        data_logger.log_mqtt(json_data=data)
    if config['pvoutput'].getboolean('enabled'):
        data_logger.log_pvoutput(json_data=data)
    if not config['device'].getboolean('enable_polling'):
        client.disconnect()

logging.info(f"Starting client: {config['device']['alias']} => {config['device']['mac_addr']}")

BTOneClient(config, on_data_received).connect()
