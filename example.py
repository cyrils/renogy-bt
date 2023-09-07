import logging
import configparser
import os
import sys
from renogybt import RoverClient, RoverHistoryClient, BatteryClient, DataLogger, Utils
from renogybt.Utils import filter_fields

logging.basicConfig(level=logging.DEBUG)

config_file = sys.argv.get[1] if len(sys.argv) > 1 else 'config.ini'
config_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), config_file)
config = configparser.ConfigParser()
config.read(config_path)
data_logger: DataLogger = DataLogger(config)

# the callback func when you receive data
def on_data_received(client, data):
    filtered_data = filter_fields(data, config['device']['fields'])
    logging.debug("{} => {}".format(client.device.alias(), filtered_data))
    if config['remote_logging'].getboolean('enabled'):
        data_logger.log_remote(json_data=filtered_data)
    if config['google_sheets'].getboolean('enabled'):
        data_logger.log_google_sheets(json_data=filtered_data)
    if config['mqtt'].getboolean('enabled'):
        data_logger.log_mqtt(json_data=filtered_data)
    if config['pvoutput'].getboolean('enabled') and config['device']['type'] == 'RNG_CTRL':
        data_logger.log_pvoutput(json_data=filtered_data)
    if not config['device'].getboolean('enable_polling'):
        client.disconnect()

# start client
if config['device']['type'] == 'RNG_CTRL':
    RoverClient(config, on_data_received).connect()
elif config['device']['type'] == 'RNG_CTRL_HIST':
    RoverHistoryClient(config, on_data_received).connect()
elif config['device']['type'] == 'RNG_BATT':
    BatteryClient(config, on_data_received).connect()
else:
    logging.error("unknown device type")
