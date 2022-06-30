import logging 
from BTOneApp import BTOneApp 

logging.basicConfig(level=logging.DEBUG)

MAC_ADDR = "80:6F:B0:0F:XX:XX"
DEVICE_ALIAS = "BT-TH-B00FXXXX"
POLL_INTERVAL = 30 # read data interval (seconds)

def on_connected(app: BTOneApp):
    app.poll_params() # OR app.set_load(1)

def on_data_received(app: BTOneApp, data):
    logging.debug("{} => {}".format(app.device.alias(), data))
    # app.disconnect() # disconnect here if you do not want polling

bt1 = BTOneApp("hci0", MAC_ADDR, DEVICE_ALIAS, on_connected, on_data_received, POLL_INTERVAL)
bt1.connect()
