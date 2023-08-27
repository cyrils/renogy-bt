import logging
import configparser
import os
from renogybt import RoverClient, RoverHistoryClient, BatteryClient, DataLogger

logging.basicConfig(level=logging.DEBUG)

config_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'config.ini')
config = configparser.ConfigParser()
config.read(config_file)
data_logger: DataLogger = DataLogger(config)

# the callback func when you receive data
def on_data_received(client, data):
    logging.debug("{} => {}".format(client.device.alias(), data))
    if config['remote_logging'].getboolean('enabled'):
        data_logger.log_remote(json_data=data)
    if config['mqtt'].getboolean('enabled'):
        data_logger.log_mqtt(json_data=data)
    if config['pvoutput'].getboolean('enabled') and config['device']['type'] == 'RNG_CTRL':
        data_logger.log_pvoutput(json_data=data)
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
