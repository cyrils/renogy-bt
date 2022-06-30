import gatt
import logging 
import time
import os

DISCOVERY_TIMEOUT = 10 # max wait time to complete the bluetooth scanning (seconds)

class DeviceManager(gatt.DeviceManager):
    def __init__(self, adapter_name):
        super(). __init__(adapter_name)

        if not self.is_adapter_powered:
            self.is_adapter_powered = True
        logging.info("Adapter status - Powered: {}".format(self.is_adapter_powered))
        
    def device_discovered(self, device):
        logging.info("[{}] Discovered, alias = {}".format(device.mac_address, device.alias()))


class Device(gatt.Device):
    def __init__(self, mac_address, alias, manager, on_resolved, on_data, notify_uuid, write_uuid):
        super(). __init__(mac_address=mac_address, manager=manager)
        self.data_callback = on_data
        self.resolved_callback = on_resolved
        self.manager = manager
        self.notify_char_uuid = notify_uuid
        self.write_char_uuid = write_uuid
        self.device_alias = alias

    def connect(self):
        discovering = True; wait = DISCOVERY_TIMEOUT; found = False;

        self.manager.update_devices()
        logging.info("Starting discovery...")
        self.manager.start_discovery()

        while discovering:
            time.sleep(1)
            logging.info("Devices found: %s", len(self.manager.devices()))
            for dev in self.manager.devices():
                if dev.mac_address == self.mac_address or dev.alias() == self.device_alias:
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
            super().connect()
            self.manager.run()
        except Exception as e:
            logging.error(e)
            self.__gracefully_exit(True)
        except KeyboardInterrupt:
            self.__gracefully_exit()

    def connect_succeeded(self):
        super().connect_succeeded()
        logging.info("[%s] Connected" % (self.mac_address))

    def connect_failed(self, error):
        super().connect_failed(error)
        logging.info("[%s] Connection failed: %s" % (self.mac_address, str(error)))
        raise Exception("Connect failed")

    def disconnect_succeeded(self):
        super().disconnect_succeeded()
        logging.info("[%s] Disconnected" % (self.mac_address))

    def services_resolved(self):
        super().services_resolved()

        logging.info("[%s] Resolved services" % (self.mac_address))
        for service in self.services:
            for characteristic in service.characteristics:
                if characteristic.uuid == self.notify_char_uuid:
                    characteristic.enable_notifications()
                    logging.info("subscribed to notification {}".format(characteristic.uuid))
                if characteristic.uuid == self.write_char_uuid:
                    self.write_characteristic = characteristic
                    logging.info("found write characteristic {}".format(characteristic.uuid))
        
        self.resolved_callback()
                    
    def descriptor_read_value_failed(self, descriptor, error):
        logging.info('descriptor_value_failed')

    def characteristic_enable_notifications_succeeded(self, characteristic):
        logging.info('characteristic_enable_notifications_succeeded')

    def characteristic_enable_notifications_failed(self, characteristic, error):
        logging.info('characteristic_enable_notifications_failed')

    def characteristic_value_updated(self, characteristic, value):
        super().characteristic_value_updated(characteristic, value)
        self.data_callback(value)

    def characteristic_write_value(self, value):
        self.write_characteristic.write_value(value)
        self.writing = value

    def characteristic_write_value_succeeded(self, characteristic):
        super().characteristic_write_value_succeeded(characteristic)
        logging.info('characteristic_write_value_succeeded')
        self.writing = False

    def characteristic_write_value_failed(self, characteristic, error):
        super().characteristic_write_value_failed(characteristic, error)
        logging.info('characteristic_write_value_failed')
        if error == "In Progress" and self.writing is not False:
            time.sleep(0.1)
            self.characteristic_write_value(self.writing, characteristic)
        else:
            self.writing = False

    def alias(self):
        alias = super().alias()
        if alias:
            return alias.strip()
        return None

    def disconnect(self):
        self.__gracefully_exit()

    def __gracefully_exit(self, connectFailed = False):
        if not connectFailed and super().is_connected():
            logging.info("Exit: Disconnecting device: %s [%s]", self.alias(), self.mac_address)
            super().disconnect()
        self.manager.stop()
        os._exit(os.EX_OK)

