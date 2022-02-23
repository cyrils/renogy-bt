from threading import Timer
import os
import logging 
import time
from SolarDevice import SolarDeviceManager, SolarDevice
from Utils import create_read_request, parse_charge_controller_info

SYSTEM_TIMEOUT = 15 # exit program after this (seconds)
DISCOVERY_TIMEOUT = 10 # max wait time to complete the bluetooth scanning (seconds)

READ_PARAMS = {
    'DEVICE_ID': 255,
    'FUNCTION': 3, # read: 3, write: 6
    'REGISTER': 256,
    'WORDS': 34
}

class BTOneApp:
    def __init__(self, adapter_name, mac_address, alias=None, on_data_received=None):
        self.adapter_name = adapter_name
        self.mac_address = mac_address
        self.alias = alias
        self.data_callback = on_data_received
        self.device = None
        self.manager = SolarDeviceManager(adapter_name=adapter_name)
        self.device = SolarDevice(mac_address=mac_address, manager=self.manager, on_resolved=self.on_resolved, on_data=self.on_data_received)
        self.timer = Timer(SYSTEM_TIMEOUT, self.gracefully_exit)
        self.timer.start()
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
            self._connect()
        else:
            logging.error("Device not found: [%s], please check the details provided.", self.mac_address)
            self.gracefully_exit(True)

    def _connect(self):
        try:
            self.device.connect()
            self.manager.run()
        except Exception as e:
            logging.error(e)
            self.gracefully_exit(True)
        except KeyboardInterrupt:
            self.gracefully_exit()

    def on_resolved(self):
        logging.info("resolved services")
        request = create_read_request(READ_PARAMS["DEVICE_ID"], READ_PARAMS["FUNCTION"], READ_PARAMS["REGISTER"], READ_PARAMS["WORDS"])
        self.device.characteristic_write_value(request)

    def on_data_received(self, value):
        data = parse_charge_controller_info(value)
        for key in data:
            self.data[key] = data[key]

        if self.data_callback is not None:
            self.data_callback(self.data)

    def gracefully_exit(self, connectFailed = False):
        if self.timer.is_alive():
            self.timer.cancel()
        if  self.device is not None and not connectFailed and self.device.is_connected():
            logging.info("Exit: Disconnecting device: %s [%s]", self.device.alias(), self.device.mac_address)
            self.device.disconnect()
        self.manager.stop()
        os._exit(os.EX_OK)


