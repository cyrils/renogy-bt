import logging
import configparser
import os
import sys
from renogybt import InverterClient, RoverClient, RoverHistoryClient, BatteryClient, DataLogger, Utils

logging.basicConfig(level=logging.DEBUG)

config_file = sys.argv[1] if len(sys.argv) > 1 else 'config.ini'
config_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), config_file)
config = configparser.ConfigParser(inline_comment_prefixes=('#'))
config.read(config_path)
data_logger: DataLogger = DataLogger(config)

# the callback func when you receive data
def on_data_received(client, data):
    filtered_data = Utils.filter_fields(data, config['data']['fields'])
    logging.debug("{} => {}".format(client.device.alias(), filtered_data))
    if config['remote_logging'].getboolean('enabled'):
        data_logger.log_remote(json_data=filtered_data)
    if config['mqtt'].getboolean('enabled'):
        data_logger.log_mqtt(json_data=filtered_data)
    # Check device type from the client's config section
    device_type = client.config.get('type', '')
    if config['pvoutput'].getboolean('enabled') and device_type == 'RNG_CTRL':
        data_logger.log_pvoutput(json_data=filtered_data)
    if not config['data'].getboolean('enable_polling'):
        client.disconnect()

# error callback
def on_error(client, error):
    logging.error(f"on_error from {client.device.alias() if hasattr(client, 'device') else 'unknown'}: {error}")

# Find all device sections and create clients
clients = []
device_sections = [section for section in config.sections() if section.startswith('device.')]

if not device_sections:
    # Fallback to legacy single device configuration
    logging.warning("No 'device.*' sections found. Attempting legacy [device] section...")
    if 'device' in config.sections():
        device_sections = ['device']
    else:
        logging.error("No device configuration found. Please configure at least one device in config.ini")
        sys.exit(1)

logging.info(f"Found {len(device_sections)} device configuration(s)")

for section in device_sections:
    # Check if device is enabled (default to true for backwards compatibility)
    if config.has_option(section, 'enabled') and not config[section].getboolean('enabled'):
        logging.info(f"Skipping disabled device: {section}")
        continue

    device_type = config[section]['type']
    device_alias = config[section].get('alias', section)

    logging.info(f"Initializing device: {device_alias} (type: {device_type})")

    # Create device-specific config by merging device section with shared sections
    device_config = configparser.ConfigParser(inline_comment_prefixes=('#'))

    # Copy the device section as 'device' for compatibility with client code
    device_config.add_section('device')
    for key in config.options(section):
        value = config.get(section, key)
        device_config.set('device', key, value)

    # Copy shared sections (data, remote_logging, mqtt, pvoutput)
    for shared_section in ['data', 'remote_logging', 'mqtt', 'pvoutput']:
        if config.has_section(shared_section):
            device_config.add_section(shared_section)
            for key in config.options(shared_section):
                value = config.get(shared_section, key)
                device_config.set(shared_section, key, value)

    # Create the appropriate client based on device type
    client = None
    if device_type == 'RNG_CTRL':
        client = RoverClient(device_config, on_data_received, on_error)
    elif device_type == 'RNG_CTRL_HIST':
        client = RoverHistoryClient(device_config, on_data_received, on_error)
    elif device_type == 'RNG_BATT':
        client = BatteryClient(device_config, on_data_received, on_error)
    elif device_type == 'RNG_INVT':
        client = InverterClient(device_config, on_data_received, on_error)
    else:
        logging.error(f"Unknown device type '{device_type}' for {section}")
        continue

    if client:
        # Store reference to the config section for use in callbacks
        client.config = config[section]
        clients.append(client)
        client.connect()

if not clients:
    logging.error("No devices were initialized. Please check your configuration.")
    sys.exit(1)

logging.info(f"Successfully initialized {len(clients)} device(s)")
