from threading import Timer
import os
import logging 
import time
from SolarDevice import SolarDeviceManager, SolarDevice
from Utils import create_request_payload, parse_charge_controller_info, parse_set_load_response, Bytes2Int

DISCOVERY_TIMEOUT = 10 # max wait time to complete the bluetooth scanning (seconds)
DEVICE_ID = 255
POLL_INTERVAL = 30 # seconds

READ_PARAMS = {
    'FUNCTION': 3,
    'REGISTER': 256,
    'WORDS': 34
}

WRITE_PARAMS_LOAD = {
    'FUNCTION': 6,
    'REGISTER': 266
}

class BTOneApp:
    def __init__(self, adapter_name, mac_address, alias=None, on_connected=None, on_data_received=None, interval = POLL_INTERVAL):
        self.adapter_name = adapter_name
        self.mac_address = mac_address
        self.alias = alias
        self.connected_callback = on_connected
        self.data_received_callback = on_data_received
        self.manager = SolarDeviceManager(adapter_name=adapter_name)
        self.device = SolarDevice(mac_address=mac_address, manager=self.manager, on_resolved=self.__on_resolved, on_data=self.__on_data_received)
        self.timer = None
        self.interval = interval
        self.data = {}

        if not self.manager.is_adapter_powered:
            self.manager.is_adapter_powered = True
        logging.info("Adapter status - Powered: {}".format(self.manager.is_adapter_powered))


    def connect(self):
        discovering = True; wait = DISCOVERY_TIMEOUT; found = False;

        self.manager.update_devices()
        logging.info("Starting discovery...")
        self.manager.start_discovery()

        while discovering:
            time.sleep(1)
            logging.info("Devices found: %s", len(self.manager.devices()))
            for dev in self.manager.devices():
                if dev.mac_address == self.mac_address or dev.alias() == self.alias:
                    logging.info("Found bt1 device %s  [%s]", dev.alias(), dev.mac_address)
                    discovering = False; found = True
            wait = wait -1
            if (wait <= 0):
                discovering = False
        self.manager.stop_discovery()
            
        if found:
            self.__connect()
        else:
            logging.error("Device not found: [%s], please check the details provided.", self.mac_address)
            self.__gracefully_exit(True)

    def __connect(self):
        try:
            self.device.connect()
            self.manager.run()
        except Exception as e:
            logging.error(e)
            self.__gracefully_exit(True)
        except KeyboardInterrupt:
            self.__gracefully_exit()

    def __on_resolved(self):
        logging.info("resolved services")
        if self.connected_callback is not None:
            self.connected_callback(self)

    def __on_data_received(self, value):
        operation = Bytes2Int(value, 1, 1)

        if operation == 3:
            logging.info("on_data_received: response for read operation")
            self.data = parse_charge_controller_info(value)
            if self.data_received_callback is not None:
                self.data_received_callback(self, self.data)
        elif operation == 6:
            self.data = parse_set_load_response(value)
            logging.info("on_data_received: response for write operation")
            if self.data_received_callback is not None:
                self.data_received_callback(self, self.data)
        else:
            logging.warn("on_data_received: unknown operation={}.format(operation)")

    def poll_params(self):
        self.__read_params()
        if self.timer is not None and self.timer.is_alive():
            self.timer.cancel()
        self.timer = Timer(self.interval, self.poll_params)
        self.timer.start()

    def __read_params(self):
        logging.info("reading params")
        request = create_request_payload(DEVICE_ID, READ_PARAMS["FUNCTION"], READ_PARAMS["REGISTER"], READ_PARAMS["WORDS"])
        self.device.characteristic_write_value(request)

    def set_load(self, value = 0):
        logging.info("setting load {}".format(value))
        request = create_request_payload(DEVICE_ID, WRITE_PARAMS_LOAD["FUNCTION"], WRITE_PARAMS_LOAD["REGISTER"], value)
        self.device.characteristic_write_value(request)

    def __gracefully_exit(self, connectFailed = False):
        if self.timer is not None and self.timer.is_alive():
            self.timer.cancel()
        if  self.device is not None and not connectFailed and self.device.is_connected():
            logging.info("Exit: Disconnecting device: %s [%s]", self.device.alias(), self.device.mac_address)
            self.device.disconnect()
        self.manager.stop()
        os._exit(os.EX_OK)

    def disconnect(self):
        self.__gracefully_exit()
