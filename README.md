# Renogy BT
![256924763-940c205e-738d-4a68-982f-1695c80bfed5](https://github.com/cyrils/renogy-bt/assets/5549113/bcdef6ec-efc9-44fd-af70-67165cf6862e)

Python library to read Renogy¹ Solar Charge Controllers and Smart Batteries using  [BT-1](https://www.renogy.com/bt-1-bluetooth-module-new-version/) or [BT-2](https://www.renogy.com/bt-2-bluetooth-module/) type (RS232 or RS485)  bluetooth modules. Tested with **Rover** / **Wanderer** series charge controllers and **Raspberry Pi Zero 2 W**. It might also work with other  "SRNE like" devices like Rich Solar, PowMr etc. See the list of [compatible devices](#compatibility). It can log the data to local **MQTT** broker, **PVOutput** cloud or your own custom server.

## Example
Each device needs a separate [config.ini](https://github.com/cyrils/renogy-bt1/blob/main/config.ini) file. Update  config file with correct values for `mac_addr`, `alias` and `type` and run the following command:

```sh
python3 ./example.py config.ini
```
 Alternatively, use it as a module with your own custom config and callback function:
```python
from renogybt import RoverClient
RoverClient(config, on_data_received).connect()
```
**How to get mac address?**

The library will automatically list possible compatible devices discovered nearby with alias starting `BT-TH`. You can alternatively use apps like [BLE Scanner](https://play.google.com/store/apps/details?id=com.macdom.ble.blescanner).

**Output**

```
INFO:root:Init RoverClient: BT-TH-B00FXXXX => 80:6F:B0:0F:XX:XX
INFO:root:Adapter status - Powered: True
INFO:root:Starting discovery...
INFO:root:Devices found: 5
INFO:root:Found matching device BT-TH-B00FXXXX => [80:6F:B0:0F:XX:XX]
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
DEBUG:root:BT-TH-B00FXXXX => {'function': 'READ', 'model': 'RNG-CTRL-WND10', 'battery_percentage': 87, 'battery_voltage': 12.9, 'battery_current': 2.58, 'battery_temperature': 25, 'controller_temperature': 33, 'load_status': 'off', 'load_voltage': 0.0,'load_current': 0.0, 'load_power': 0, 'pv_voltage': 17.1, 'pv_current': 2.04, 'pv_power': 35, 'max_charging_power_today': 143, 'max_discharging_power_today': 0, 'charging_amp_hours_today': 34, 'discharging_amp_hours_today': 34, 'power_generation_today': 432, 'power_consumption_today': 0, 'power_generation_total': 426038, 'charging_status': 'mppt', 'battery_type': 'lithium', 'device_id': 97}
INFO:root:Exit: Disconnecting device: BT-TH-B00FXXXX [80:6F:B0:0F:XX:XX]
```
```
# Rover historical data (7 days summary)
DEBUG:root:BT-TH-30A3XXXX => {'function': 'READ', 'daily_power_generation': [1754, 1907, 1899, 1804, 1841, 1630, 1344],'daily_charge_ah': [135, 147, 147, 139, 142, 125, 102], 'daily_max_power': [234, 344, 360, 335, 331, 307, 290]}
```
```
# Battery output
DEBUG:root:BT-TH-161EXXXX => {'function': 'READ', 'model': 'RBT100LFP12S-G', 'cell_count': 4, 'cell_voltage_0': 3.6, 'cell_voltage_1': 3.6, 'cell_voltage_2': 3.6, 'cell_voltage_3': 3.6, 'sensor_count': 4, 'temperature_0': 21.0, 'temperature_1': 21.0, 'temperature_2': 21.0, 'temperature_3': 21.0, 'current': 1.4, 'voltage': 14.5, 'remaining_charge': 99.941, 'capacity': 100.0, 'device_id': 48} 
```
```
# Inverter output (experimental)
DEBUG:root:BT-TH-F26EXXXX => {'function': 'READ', 'uei_voltage': 123.9, 'uei_current': 0, 'voltage': 120.0, 'load_current': 2, 'frequency': 60.01, 'temperature': 54.0, 'model': 'RIV4835CSH1S', 'solar_voltage': 93.9, 'solar_current': 0.3, 'solar_power': 32, 'solar_charging_state': 'mppt', 'solar_charging_power': 32, 'load_power': 23, 'charging_current': 0, 'battery_type': 'lithium', '__device': 'BT-TH-F26EXXXX', '__client': 'InverterClient'} 
```

**Have multiple devices in Hub mode?**

If you have multiple devices connected to a single BT-2 module (daisy chained or using [Communication Hub](https://www.renogy.com/communication-hub/)), you need to find out the individual device Id (aka address) of each of these devices. Below are some of the usual suspects:

|  | Stand-alone | Daisy-chained | Hub mode |
| :-------- | :-------- | :-------- | :-------- |
|  Controller | 255, 17 | 17 | 96, 97 |
|  Battery | 255 | 33, 34, 35 | 48, 49, 50 |
|  Inverter | 255, 32 | 32 | 32 |

 If you receive no response or garbled data with above ids, connect a single device to the Hub at a time and use the default broadcast address of 255 in `config.ini` to find out the actual `device_id` from output log. Then use this device Id to connect in Hub mode.

## Dependencies

```sh
python3 -m pip install -r requirements.txt
```

This library is primarily designed to work with Raspberry Pi OS, but should work on any modern Linux platforms. Due to incompatibility of underlying `gatt` library, this project is unsupported in Windows/Mac environments. You can also checkout the new [bleak](https://github.com/cyrils/renogy-bt/pull/66) port which is cross-platform.

## Data logging

Supports logging data to local MQTT brokers like [Mosquitto](https://mosquitto.org/) or [Home Assistant](https://www.home-assistant.io/) dashboards. You can also log it to third party cloud services like [PVOutput](https://pvoutput.org/). See [config.ini](https://github.com/cyrils/renogy-bt1/blob/main/config.ini) for more details. Note that free PVOutput accounts have a cap of one request per minute.

Example config to add to your home assistant `configuration.yaml`:
```yaml
mqtt:
  sensor:
    - name: "Solar Power"
      state_topic: "solar/state"
      device_class: "power"
      unit_of_measurement: "W"
      value_template: "{{ value_json.pv_power }}"
    - name: "Battery SOC"
      state_topic: "solar/state"
      device_class: "battery"
      unit_of_measurement: "%"
      value_template: "{{ value_json.battery_percentage }}"
# check output log for more fields
```

**Custom logging**

Should you choose to upload to your own server, the json data is posted as body of the HTTP POST call. The optional `auth_header` is sent as http header `Authorization: Bearer <auth-header>`

Example php code at the server:
```php
$headers = getallheaders();
if ($headers['Authorization'] != "Bearer 123456789") {
    header( 'HTTP/1.0 403 Forbidden', true, 403 );
    die('403 Forbidden');
}
$json_data = json_decode(file_get_contents('php://input'), true);
```

**How to get continues output?**

 The best way to get continues data is to schedule a cronjob by running `crontab -e` and insert the following command:
```sh
*/5 * * * * python3 /path/to/renogy-bt/example.py config.ini #runs every 5 mins
```
If you want to monitor real-time data, turn on polling in `config.ini` for continues streaming (default interval is 60 secs). You may also register it as a [service](https://github.com/cyrils/renogy-bt/issues/77) for added reliability.

## Compatibility
| Device | Adapter | Supported |
| -------- | :--------: | :--------: |
| Renogy Rover/Wanderer/Adventurer | BT-1 | ✅ |
| Renogy Rover Elite RCC40RVRE | BT-2 |  ✅ |
| Renogy DC-DC Charger DCC50S | BT-2 |  ✅ |
| Renogy Battery RBT100LFP12S / RBT50LFP48S | BT-2 | ✅ |
| Renogy Battery RBT100LFP12-BT / RBT200LFP12-BT (Built-in BLE)| - | ✅ |
| Renogy Battery RBT12100LFP-BT / RBT12200LFP-BT (Pro Series) | - | ✅ |
| Renogy Inverter RIV4835CSH1S*| BT-2 | 🚧 |
| Renogy Smart Shunt | - | ❌ |
| SRNE ML24/ML48 Series | BT-1 | ✅ |
| RICH SOLAR 20/40/60 | BT-1 | ✅ |

*_Experimental support for inverter, not all fields are validated._

### Disclaimer

¹This is not an official library endorsed by the device manufacturer. Renogy and all other trademarks in this repo are the property of their respective owners and their use herein does not imply any sponsorship or endorsement.

## References

 - [Olen/solar-monitor](https://github.com/Olen/solar-monitor)
 - [corbinbs/solarshed](https://github.com/corbinbs/solarshed)
 - [Rover 20A/40A Charge Controller—MODBUS Protocol](https://github.com/cyrils/renogy-bt/files/12787920/ROVER.MODBUS.pdf)
 - [Lithium Iron Battery BMS Modbus Protocol V1.7](https://github.com/cyrils/renogy-bt/files/12444500/Lithium.Iron.Battery.BMS.Modbus.Protocol.V1.7.zh-CN.en.1.pdf)
 - [mavenius/renogy-bt-esphome](//github.com/mavenius/renogy-bt-esphome) - ESPHome port of this project

