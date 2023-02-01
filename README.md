# Renogy BT-1
Python library to read Renogy RS232 compatible [BT-1](https://www.renogy.com/bt-1-bluetooth-module-new-version/) bluetooth adapter. Tested with **Rover** / **Wanderer** series charge controllers and **Raspberry Pi Zero 2 W**. It might also work with other  "SRNE like" devices like Rich Solar, PowMr, WEIZE etc.

## Installation

```
pip3 install rng-bt1
``` 
To obtain the full code, including examples and documentation, you can clone the git repository:
```
git clone https://github.com/cyrils/renogy-bt1.git
```
## Example
Make sure to update `config.ini` with correct values for `mac_addr` and `alias`. If you want to use it as a module, take a look at the examples provided.

```
python3 ./src/rng-bt1/BTOneApp.py
```

**How to get mac address?**

Run the above command and look for discovered devices nearby with alias `BT-TH-XXXX..`. Alternatively you can use apps like [BLE Scanner](https://play.google.com/store/apps/details?id=com.macdom.ble.blescanner) 

**Output**

```
INFO:root:Adapter status - Powered: True
INFO:root:Starting discovery...
INFO:root:Devices found: 5
INFO:root:Found bt1 device BT-TH-B00FXXXX  [XX:6F:B0:0F:XX:XX]
INFO:root:[80:6f:b0:0f:XX:XX] Discovered, alias = BT-TH-B00FXXXX
INFO:root:[80:6F:B0:0F:XX:XX] Connected
INFO:root:[80:6F:B0:0F:XX:XX] Resolved services
INFO:root:found write characteristic 0000ffd1-0000-1000-8000-00805f9b34fb
INFO:root:subscribed to notification 0000fff1-0000-1000-8000-00805f9b34fb
INFO:root:resolved services
INFO:root:reading params
DEBUG:root:create_read_request 256 => [255, 3, 1, 0, 0, 34, 209, 241]
INFO:root:characteristic_write_value_succeeded
INFO:root:characteristic_enable_notifications_succeeded
INFO:root:on_data_received: response for read operation
DEBUG:root:BT-TH-B00FXXXX => {'function': 'READ', 'battery_percentage': 100, 'battery_voltage': 14.4, 'controller_temperature': 34, 'battery_temperature': 25, 'load_status': 'off', 'load_voltage': 0.0, 'load_current': 0.0, 'load_power': 0, 'pv_voltage': 17.1, 'pv_current': 5.26, 'pv_power': 101, 'max_charging_power_today': 276, 'max_discharging_power_today': 4, 'charging_amp_hours_today': 59, 'discharging_amp_hours_today': 2, 'power_generation_today': 797, 'power_generation_total': 291253, 'charging_status': 'mppt'}
INFO:root:Exit: Disconnecting device: BT-TH-B00FXXXX [80:6F:B0:0F:XX:XX]
```


## Dependencies

```
python3 -m pip install -r requirements.txt
```

## References

 - [Olen/solar-monitor](https://github.com/Olen/solar-monitor)
 - [corbinbs/solarshed](https://github.com/corbinbs/solarshed)
 - [Rover 20A/40A Charge Controller—MODBUS Protocol](https://docs.google.com/document/d/1OSW3gluYNK8d_gSz4Bk89LMQ4ZrzjQY6/edit)

