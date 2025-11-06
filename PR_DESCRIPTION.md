# Pull Request: Multi-Device Monitoring Support with Threading and UV Package Management

## Summary

This PR adds comprehensive support for monitoring multiple Renogy devices simultaneously (e.g., charge controller + battery) along with modern Python package management using uv.

## Key Features

### 1. Multi-Device Monitoring
- **Configuration**: Support for multiple `[device.NAME]` sections in config.ini
- **Concurrent connections**: Each device runs in its own thread with independent Bluetooth connection
- **Toggle devices**: Use `enabled = true/false` to enable/disable specific devices
- **Backwards compatible**: Still supports legacy single `[device]` configuration

### 2. Threading Support
- Each device client runs in a separate thread to avoid blocking
- Allows simultaneous monitoring of charge controller, battery, inverter, etc.
- Graceful shutdown with Ctrl+C handling

### 3. Modern Package Management (uv)
- Added `pyproject.toml` with full project metadata
- Automated setup script (`setup.sh`) for easy installation
- Auto-detects system Python version (Raspberry Pi compatible)
- Properly handles system packages (dbus-python, PyGObject, pycairo)

### 4. Raspberry Pi Compatibility
- Auto-detects system Python version (3.9 for Bullseye, 3.11 for Bookworm)
- Virtual environment uses matching Python version for system package compatibility
- Tested on Raspberry Pi 4

### 5. Helper Tools
- **check_config.py**: Validates configuration and diagnoses setup issues
- **config-example-single.ini**: Template for single-device setup
- Clear error messages and setup guidance

## Installation

### Quick Setup (Recommended)
```sh
./setup.sh
```

### Manual Setup
```sh
# Install system packages
sudo apt-get install -y python3-dev python3-dbus python3-gi python3-cairo \
    libdbus-1-dev libglib2.0-dev libcairo2-dev pkg-config

# Install uv and sync dependencies
curl -LsSf https://astral.sh/uv/install.sh | sh
uv venv --python 3.11 --system-site-packages  # Use your system Python version
uv sync

# Run
uv run python example.py config.ini
```

## Configuration Example

```ini
[device.controller]
enabled = true
mac_addr = AA:BB:CC:DD:EE:FF
alias = BT-TH-Controller
type = RNG_CTRL

[device.battery]
enabled = true
mac_addr = 11:22:33:44:55:66
alias = BT-TH-Battery
type = RNG_BATT

[data]
enable_polling = false
poll_interval = 60
```

## Testing

- ✅ Single device monitoring (backwards compatible)
- ✅ Multi-device monitoring (controller + battery)
- ✅ Raspberry Pi 4 with Python 3.9/3.11
- ✅ uv package management
- ✅ System package integration (dbus-python, PyGObject)

## Commits

- Multi-device configuration support
- Threading for concurrent device connections
- uv package management integration
- Raspberry Pi Python version auto-detection
- System package handling fixes
- Configuration validation tool
- Multiple bug fixes for config parsing

## Breaking Changes

None - fully backwards compatible with single `[device]` configuration.

## Future Work

This PR sets the foundation for:
- Enhanced logging capabilities (MQTT, HTTP, PVOutput improvements)
- Better error handling and retry logic
- Device status monitoring
