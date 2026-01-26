
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

