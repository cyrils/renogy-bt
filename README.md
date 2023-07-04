# Renogy BT-1
Python library to read Renogy RS232 compatible solar charge controllers using [BT-1](https://www.renogy.com/bt-1-bluetooth-module-new-version/) bluetooth adapter. Tested with **Rover** / **Wanderer** series charge controllers and **Raspberry Pi Zero 2 W**. It might also work with other  "SRNE like" devices like Rich Solar, PowMr etc. It supports periodic data polling and can also log the data to local [MQTT](https://mqtt.org/) broker, [PVOutput](https://pvoutput.org/) cloud or your own custom server.

This was also found working with RS485 type [BT-2](https://www.renogy.com/bt-2-bluetooth-module/) adapter, but does not work with communication hub. Also it reads only charge controller data, and will fail with any other bluetooth connected peripherals like renogy battery (see [thread](https://github.com/cyrils/renogy-bt1/issues/7#issuecomment-1500237677)).

## Dependencies

```sh
python3 -m pip install -r requirements.txt
```

## Example
Make sure to update [config.ini](https://github.com/cyrils/renogy-bt1/blob/main/config.ini) with correct values for `mac_addr` and `alias` and run the following command:

```sh
python3 ./example.py
```

Alternatively, use it as a module with your own custom config and callback function:
```python
from renogybt import BTOneClient
BTOneClient(config, on_data_received).connect()
```

**How to get mac address?**

The library will automatically list possible bt-1 devices discovered nearby with alias starting `BT-TH`. You can alternatively use apps like [BLE Scanner](https://play.google.com/store/apps/details?id=com.macdom.ble.blescanner).

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
DEBUG:root:BT-TH-B00FXXXX => {'function': 'READ', 'battery_percentage': 87, 'battery_voltage': 12.9, 'battery_current': 2.58, 'battery_temperature': 25, 'controller_temperature': 33, 'load_status': 'off', 'load_voltage': 0.0,'load_current': 0.0, 'load_power': 0, 'pv_voltage': 17.1, 'pv_current': 2.04, 'pv_power': 35, 'max_charging_power_today': 143, 'max_discharging_power_today': 0, 'charging_amp_hours_today': 34, 'discharging_amp_hours_today': 34, 'power_generation_today': 432, 'power_consumption_today': 0, 'power_generation_total': 426038, 'charging_status': 'mppt'}
INFO:root:Exit: Disconnecting device: BT-TH-B00FXXXX [80:6F:B0:0F:XX:XX]
```

## Data logging

Supports logging data to local MQTT brokers like [Mosquitto](https://mosquitto.org/) or [Home Assistant](https://www.home-assistant.io/) dashboards. You can also log it to third party cloud services like [PVOutput](https://pvoutput.org/). See [config.ini](https://github.com/cyrils/renogy-bt1/blob/main/config.ini) for more details. Note that free PVOutput accounts have a cap of one request per minute.

Example config to add to your home assistant `configuration.yaml`:
```yaml
mqtt:
  sensor:
    - name: "Solar Power"
      state_topic: "solar/stats"
      unit_of_measurement: "W"
      value_template: "{{ value_json.pv_power }}"
    - name: "Battery SOC"
      state_topic: "solar/stats"
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
## Compatibility
| Device | Adapter | Tested |
| -------- | :--------: | :--------: |
| Renogy Rover/Wanderer/Adventurer | BT-1 | ✅ |
| Renogy Rover Elite | BT-2 |  ✅ |
| RICH SOLAR 20/40/60 | BT-1 | ❓ |
| SRNE ML24/ML48 Series | BT-1 | ❓ |

## References

 - [Olen/solar-monitor](https://github.com/Olen/solar-monitor)
 - [corbinbs/solarshed](https://github.com/corbinbs/solarshed)
 - [Rover 20A/40A Charge Controller—MODBUS Protocol](https://docs.google.com/document/d/1OSW3gluYNK8d_gSz4Bk89LMQ4ZrzjQY6/edit)

