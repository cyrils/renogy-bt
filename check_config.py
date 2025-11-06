#!/usr/bin/env python3
"""
Configuration checker for renogy-bt
Validates config.ini and helps diagnose setup issues
"""

import configparser
import sys
import os

def check_config(config_file='config.ini'):
    """Check if config.ini is properly formatted"""

    print("=" * 60)
    print("Renogy BT Configuration Checker")
    print("=" * 60)
    print()

    # Check if config file exists
    if not os.path.exists(config_file):
        print(f"❌ ERROR: Config file '{config_file}' not found!")
        print(f"   Current directory: {os.getcwd()}")
        print(f"   Please ensure you're in the correct directory.")
        return False

    print(f"✓ Config file found: {config_file}")
    print()

    # Try to parse the config
    try:
        config = configparser.ConfigParser(inline_comment_prefixes=('#'))
        config.read(config_file)
    except Exception as e:
        print(f"❌ ERROR: Failed to parse config file: {e}")
        return False

    print(f"✓ Config file parsed successfully")
    print()

    # Check for device sections
    all_sections = config.sections()
    device_sections = [s for s in all_sections if s.startswith('device.')]

    print(f"Found {len(all_sections)} total sections:")
    for section in all_sections:
        print(f"  - [{section}]")
    print()

    if not device_sections and 'device' not in all_sections:
        print("❌ ERROR: No device configuration found!")
        print()
        print("Your config.ini needs device sections. Expected format:")
        print()
        print("[device.controller]")
        print("enabled = true")
        print("mac_addr = XX:XX:XX:XX:XX:XX")
        print("alias = BT-TH-XXXXX")
        print("type = RNG_CTRL")
        print()
        print("Please update your config.ini with the new format.")
        return False

    # Check device sections
    if device_sections:
        print(f"✓ Found {len(device_sections)} device section(s):")
        print()

        for section in device_sections:
            enabled = config.getboolean(section, 'enabled', fallback=True)
            status = "✓ ENABLED" if enabled else "⊗ DISABLED"
            print(f"  {status} [{section}]")

            # Check required fields
            required_fields = ['mac_addr', 'alias', 'type']
            for field in required_fields:
                if config.has_option(section, field):
                    value = config.get(section, field)

                    # Check for placeholder values
                    if field == 'mac_addr' and ('xx' in value.lower() or 'yy' in value.lower()):
                        print(f"      ⚠ {field}: {value} (NEEDS UPDATE!)")
                    elif field == 'alias' and 'update' in value.lower():
                        print(f"      ⚠ {field}: {value} (NEEDS UPDATE!)")
                    else:
                        print(f"      ✓ {field}: {value}")
                else:
                    print(f"      ❌ {field}: MISSING!")

            print()

        # Check for placeholder MAC addresses
        needs_update = False
        for section in device_sections:
            if config.has_option(section, 'mac_addr'):
                mac = config.get(section, 'mac_addr').lower()
                if 'xx' in mac or 'yy' in mac or 'must update' in mac:
                    needs_update = True
                    break

        if needs_update:
            print()
            print("⚠ WARNING: You need to update MAC addresses with real device addresses!")
            print()
            print("To find your device MAC addresses:")
            print("  1. Make sure your Renogy devices are powered on")
            print("  2. Run the script - it will list discovered BT-TH devices")
            print("  3. Update config.ini with the actual MAC addresses")
            print()
            return False

    elif 'device' in all_sections:
        print("⚠ WARNING: Found legacy [device] section (single device mode)")
        print("  Consider upgrading to multi-device format for monitoring both devices")
        print()

    # Check shared sections
    required_shared = ['data', 'remote_logging', 'mqtt', 'pvoutput']
    missing_shared = [s for s in required_shared if s not in all_sections]

    if missing_shared:
        print(f"⚠ WARNING: Missing optional sections: {', '.join(missing_shared)}")
    else:
        print(f"✓ All shared configuration sections present")

    print()
    print("=" * 60)
    print("Configuration check complete!")
    print("=" * 60)

    return not needs_update

if __name__ == '__main__':
    config_file = sys.argv[1] if len(sys.argv) > 1 else 'config.ini'
    success = check_config(config_file)
    sys.exit(0 if success else 1)
