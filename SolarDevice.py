import gatt
import logging 
import time

NOTIFY_CHAR_UUID = "0000fff1-0000-1000-8000-00805f9b34fb"
WRITE_CHAR_UUID  = "0000ffd1-0000-1000-8000-00805f9b34fb"


class SolarDeviceManager(gatt.DeviceManager):
    def __init__(self, adapter_name):
        super(). __init__(adapter_name)
        
    def device_discovered(self, device):
        logging.info("[{}] Discovered, alias = {}".format(device.mac_address, device.alias()))


class SolarDevice(gatt.Device):
    def __init__(self, mac_address, manager, on_resolved, on_data):
        super(). __init__(mac_address=mac_address, manager=manager)
        self.data_callback = on_data
        self.resolved_callback = on_resolved
        
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
                if characteristic.uuid == NOTIFY_CHAR_UUID:
                    characteristic.enable_notifications()
                    logging.info("subscribed to notification {}".format(characteristic.uuid))
                elif characteristic.uuid == WRITE_CHAR_UUID:
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
        logging.info('characteristic_enable_notifications_succeeded')
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

