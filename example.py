import logging 
from BTOneApp import BTOneApp 

logging.basicConfig(level=logging.DEBUG)

def data_callback(data):
    logging.debug(data)

MAC_ADDR = "80:6F:B0:0F:XX:XX"
DEVICE_ALIAS = "BT-TH-B00FXXXX"

bt1 = BTOneApp("hci0", MAC_ADDR, DEVICE_ALIAS, data_callback)
bt1.connect()


