import gatt
import logging 
import time

DISCOVERY_TIMEOUT = 5 # max wait time to complete the bluetooth scanning (seconds)

class DeviceManager(gatt.DeviceManager):
    def __init__(self, adapter_name, mac_address, alias):
        super(). __init__(adapter_name)
        self.device_found = False
        self.mac_address = mac_address
        self.device_alias = alias

        if not self.is_adapter_powered:
            self.is_adapter_powered = True
        logging.info("Adapter status - Powered: {}".format(self.is_adapter_powered))

    def discover(self):
        discovering = True; wait = DISCOVERY_TIMEOUT; self.device_found = False;

        self.update_devices()
        logging.info("Starting discovery...")
        self.start_discovery()

        while discovering:
            time.sleep(1)
            logging.info("Devices found: %s", len(self.devices()))
            for dev in self.devices():
                if (dev.mac_address == self.mac_address or dev.alias() == self.device_alias) and discovering:
                    logging.info("Found matching device %s => [%s]", dev.alias(), dev.mac_address)
                    discovering = False; self.device_found = True
            wait = wait -1
            if (wait <= 0):
                discovering = False
        self.stop_discovery()

    def device_discovered(self, device):
        logging.info("[{}] Discovered, alias = {}".format(device.mac_address, device.alias()))


class Device(gatt.Device):
    def __init__(self, mac_address, manager, on_resolved, on_data, on_connect_fail, notify_uuid, write_uuid):
        super(). __init__(mac_address=mac_address, manager=manager)
        self.data_callback = on_data
        self.resolved_callback = on_resolved
        self.connect_fail_callback = on_connect_fail
        self.manager = manager
        self.notify_char_uuid = notify_uuid
        self.write_char_uuid = write_uuid
        self.mac_address = mac_address

    def connect_succeeded(self):
        super().connect_succeeded()
        logging.info("[%s] Connected" % (self.mac_address))

    def connect_failed(self, error):
        super().connect_failed(error)
        self.connect_fail_callback(error)

    def disconnect_succeeded(self):
        super().disconnect_succeeded()
        logging.info("[%s] Disconnected" % (self.mac_address))
        self.connect_fail_callback('Disconnected')

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
        if super().is_connected():
            logging.info("Exit: Disconnecting device: %s [%s]", self.alias(), self.mac_address)
            super().disconnect()
