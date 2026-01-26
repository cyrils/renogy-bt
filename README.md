
# RenogyBT Custom Client :jigsaw:

This repository contains a **customized version** of the RenogyBT Python library for interacting with Renogy solar devices such as **Charge contollers + Battery + BT-1 Module**, batteries, inverters, and DC chargers.  

The original code was sourced from [The Renogy-bt Git Hub Repository](https://github.com/cyrils/renogy-bt), but it has been **modified and enhanced** for **robustness, historical data support, and Node-RED integration** for personal use.

---

##  Project Overview :open_file_folder:

The code interacts with Renogy devices over Bluetooth (BT-1 / BT-2 modules) and collects live and historical data, including:

- Battery voltage, current, temperature
- Load and solar PV status, voltage, current, power
- Daily and total energy metrics
- Historical data for power generation, charging, and maximum power

---

##  Modifications / Enhancements  :gear:

The changes in the code have been only been made in the BLEManager.py, BaseClient, RoverClient, example.py and config.ini
The following table summarizes the **changes made to the original code**:

## Modifications / Enhancements  :toolbox:

| File | Original Behavior | Modifications | Benefit |
|------|-----------------|---------------|---------|
| **BLEManager.py** | - BLE discovery and connection retries were limited<br>- Stale cached clients could be reused, causing errors<br>- Errors in BlueZ/DBus could crash the program<br>- Connection failures not propagated cleanly | - Added **robust retry loops** for discovery and connection<br>- Option `use_cached=False` to avoid stale client reuse<br>- Added **safe handling** for BlueZ/DBus errors<br>- Connection errors propagate to BaseClient for proper handling<br>- Cleanly disconnects and resolves future on errors | Greatly improves BLE reliability, prevents crashes, ensures automatic reconnection when Bluetooth adapter is off, and allows safe error propagation to client |
| **BaseClient.py** | - Crashes if Bluetooth gateway is off or device not found<br>- `disconnect()` could fail if loop/future not initialized<br>- `on_read_operation_complete` reset data prematurely<br>- Timeout handling less robust<br>- Logging for discovery/connection limited | - **Robust handling** if Bluetooth gateway is off or device not found<br>- Async-safe `disconnect()` using `_stop_async()`<br>- `future` safely resolved in all scenarios<br>- `read_timeout` properly canceled on disconnect or error<br>- `on_read_operation_complete` no longer overwrites existing data before callback<br>- Enhanced logging for BLE discovery and connection failures | Prevents client crashes, ensures clean stop, better BLE error handling, and reliable operation even when Bluetooth is unavailable |
| **RoverClient.py** | - Only live data parsed<br>- Fields had no units<br>- No historical data<br>- Load write operation was basic<br>- Device info parsing included function and model | - **Historical data parsing** for multiple registers<br>- Added arrays: `daily_power_generation Wh`, `daily_charge Ah`, `daily_max_power W`<br>- All fields now have **units** (`V`, `A`, `W`, `Wh`, `Ah`)<br>- Device info and battery type parsing simplified<br>- Load write operation improved with async BLE write<br>- Logs raw historical data for debugging | Enables historical tracking, consistent units, better load control, simplified parsing, and debug-friendly data |
| `example.py` | - Logs filtered data and optionally publishes to MQTT, PVOutput, remote logging<br>- No Node-RED / stdout integration | - Outputs JSON to stdout for **Node-RED** integration<br>- Flush stdout after print to ensure immediate delivery<br>- Original logging/publishing retained | Allows real-time automation dashboards, integrates with Node-RED flows |
| `config.ini` | - Example MAC and alias<br>- Temperature unit = F<br>- Polling and fields placeholders<br>- Full comments included | - Updated MAC address and alias<br>- Temperature unit set to **Celsius**<br>- Cleaned unused placeholders<br>- Polling left configurable | Ready-to-use, clean, maintainable configuration for personal devices |


---

##  Features :package:

- **Live data collection** from Renogy devices
- **Historical data parsing** for energy metrics
- **Data integration** via JSON output
- **Unit-consistent metrics** for volts, amps, watts, watt-hours, and amp-hours

---

##  Example Usage :desktop_computer:

```bash
# Run the client using a configuration file
python3 example.py config.ini
```

## Sample Output  :floppy_disk:

```
dexter:~/renogy-bt$ python3 example.py config.ini
INFO:root:Init RoverClient: BT-TH-A58A7XYZ => CC:45:A5:XX:YY:ZZ
INFO:root:Starting discovery...
INFO:root:Devices found: 55
INFO:root:Found matching device BT-TH-A58A7XYZ => CC:45:A5:XX:YY:ZZ
INFO:root:Connecting (attempt 1)...
WARNING:bleak.backends.bluezdbus.client:Failed to cancel connection (/org/bluez/hci0/dev_CC_45_A5_XX_YY_ZZ):
WARNING:root:Connection attempt 1 failed: [org.bluez.Error.Failed] Disconnected early
INFO:root:Connecting (attempt 2)...
INFO:root:Client connection: True
INFO:root:Found write characteristic 0000ffd1-0000-1000-8000-00805f9b34fb, service 0000ffd0-0000-1000-8000-00805f9b34fb
INFO:root:Subscribed to notification 0000fff1-0000-1000-8000-00805f9b34fb
INFO:root:BLE connection established successfully
INFO:root:Writing to 0000ffd1-0000-1000-8000-00805f9b34fb: [255, 3, 0, 12, 0, 8, 145, 209]
INFO:root:Characteristic write succeeded
INFO:root:notification_callback
INFO:root:on_data_received: read operation success
INFO:root:Writing to 0000ffd1-0000-1000-8000-00805f9b34fb: [255, 3, 0, 26, 0, 1, 176, 19]
INFO:root:Characteristic write succeeded
INFO:root:notification_callback
INFO:root:on_data_received: read operation success
INFO:root:Writing to 0000ffd1-0000-1000-8000-00805f9b34fb: [255, 3, 1, 0, 0, 34, 209, 241]
INFO:root:Characteristic write succeeded
INFO:root:notification_callback
INFO:root:on_data_received: read operation success
INFO:root:Writing to 0000ffd1-0000-1000-8000-00805f9b34fb: [255, 3, 224, 4, 0, 1, 231, 213]
INFO:root:Characteristic write succeeded
INFO:root:notification_callback
INFO:root:on_data_received: read operation success
INFO:root:Writing to 0000ffd1-0000-1000-8000-00805f9b34fb: [255, 3, 240, 6, 0, 10, 3, 18]
INFO:root:Characteristic write succeeded
INFO:root:notification_callback
INFO:root:on_data_received: read operation success
INFO:root:Raw historical data: ff03140080008000000026000000040000000000000000685b
INFO:root:Writing to 0000ffd1-0000-1000-8000-00805f9b34fb: [255, 3, 240, 5, 0, 10, 243, 18]
INFO:root:Characteristic write succeeded
INFO:root:notification_callback
INFO:root:on_data_received: read operation success
INFO:root:Raw historical data: ff031400840085000000250000000400000000000000008ff9
INFO:root:Writing to 0000ffd1-0000-1000-8000-00805f9b34fb: [255, 3, 240, 4, 0, 10, 162, 210]
INFO:root:Characteristic write succeeded
INFO:root:notification_callback
INFO:root:on_data_received: read operation success
INFO:root:Raw historical data: ff03140084008400000025000000040000000000000000de69
INFO:root:Writing to 0000ffd1-0000-1000-8000-00805f9b34fb: [255, 3, 240, 3, 0, 10, 19, 19]
INFO:root:Characteristic write succeeded
INFO:root:notification_callback
INFO:root:on_data_received: read operation success
INFO:root:Raw historical data: ff031400830084000000250000000400000000000000006b1d
INFO:root:Writing to 0000ffd1-0000-1000-8000-00805f9b34fb: [255, 3, 240, 2, 0, 10, 66, 211]
INFO:root:Characteristic write succeeded
INFO:root:notification_callback
INFO:root:on_data_received: read operation success
INFO:root:Raw historical data: ff0314008d008f000000220000000400000000000000007d81
INFO:root:Writing to 0000ffd1-0000-1000-8000-00805f9b34fb: [255, 3, 240, 1, 0, 10, 178, 211]
INFO:root:Characteristic write succeeded
INFO:root:notification_callback
INFO:root:on_data_received: read operation success
INFO:root:Raw historical data: ff0314008600860000002500000004000000000000000006b1
INFO:root:Writing to 0000ffd1-0000-1000-8000-00805f9b34fb: [255, 3, 240, 0, 0, 10, 227, 19]
INFO:root:Characteristic write succeeded
INFO:root:notification_callback
INFO:root:on_data_received: read operation success
INFO:root:Raw historical data: ff0314008500860000002500000004000000140000010af361
INFO:root:on_read_operation_complete
INFO:root:BT-TH-A58A7XYZ => {'daily_power_generation Wh': [38, 37, 37, 37, 34, 37, 37], 'daily_charge Ah': [128, 133, 132, 132, 143, 134, 134], 'daily_max_power W': [38, 37, 37, 37, 34, 37, 37], 'battery_percentage': 100, 'battery_voltage V': 13.3, 'battery_current A': 0.0, 'battery_temperature C': 22, 'controller_temperature C': 23, 'load_status': 'on', 'load_voltage V': 13.3, 'load_current A': 0.28, 'load_power W': 3, 'solarpv_voltage V': 0.0, 'solarpv_current A': 0.0, 'solarpv_power W': 0, 'max_charging_power_today W': 0, 'max_discharging_power_today W': 4, 'charging_amp_hours_today Ah': 0, 'discharging_amp_hours_today Ah': 20, 'power_generation_today Wh': 0, 'power_consumption_today Wh': 266, 'power_generation_total Wh': 0, 'charging_status': 'deactivated'}
{"daily_power_generation Wh": [38, 37, 37, 37, 34, 37, 37], "daily_charge Ah": [128, 133, 132, 132, 143, 134, 134], "daily_max_power W": [38, 37, 37, 37, 34, 37, 37], "battery_percentage": 100, "battery_voltage V": 13.3, "battery_current A": 0.0, "battery_temperature C": 22, "controller_temperature C": 23, "load_status": "on", "load_voltage V": 13.3, "load_current A": 0.28, "load_power W": 3, "solarpv_voltage V": 0.0, "solarpv_current A": 0.0, "solarpv_power W": 0, "max_charging_power_today W": 0, "max_discharging_power_today W": 4, "charging_amp_hours_today Ah": 0, "discharging_amp_hours_today Ah": 20, "power_generation_today Wh": 0, "power_consumption_today Wh": 266, "power_generation_total Wh": 0, "charging_status": "deactivated"}
INFO:root:Disconnecting device: BT-TH-A58A7XYZ CC:45:A5:XX:YY:ZZ

```



