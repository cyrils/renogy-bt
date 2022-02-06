import logging 
from BTOneApp import BTOneApp 

logging.basicConfig(level=logging.DEBUG)

def data_callback(data):
    logging.debug(data)

bt1 = BTOneApp("hci0", "80:6F:B0:0F:XX:XX", "BT-TH-B00FXXX", data_callback)
bt1.connect()


