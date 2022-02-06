import logging 
from BTOneApp import BTOneApp 

logging.basicConfig(level=logging.DEBUG)

def data_callback(data):
    logging.debug(data)

bt1 = BTOneApp("hci0", "80:6F:B0:0F:EA:2B", "BT-TH-B00FEA2B", data_callback)
bt1.connect()


