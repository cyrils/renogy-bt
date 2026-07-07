import configparser
import pytest

from renogybt.ShuntClient import ShuntClient


@pytest.fixture
def config():
    cfg = configparser.ConfigParser()
    cfg.read_dict(
        {
            "device": {"device_id": "255", "alias": "BT-TH-TEST", "mac_addr": "AA:BB:CC:DD:EE:FF"},
            "data": {"poll_interval": "60", "temperature_unit": "F"},
        }
    )
    return cfg


def test_parse_shunt_info_extracts_expected_fields(config):
    client = ShuntClient(config)
    payload = bytearray(80)
    payload[1] = 87
    payload[21:24] = b"\x00\x03\xE8"
    payload[25:28] = b"\x00\x07\xD0"
    payload[30:32] = b"\x00\x0B\xB8"
    payload[34:36] = b"\x00\x28"
    payload[66:68] = b"\x01\x9A"

    data = client.parse_shunt_info(payload)

    assert data["charge_amps"] == 1.0
    assert data["main_battery_voltage"] == 2.0
    assert data["starter_battery_voltage"] == 0.01
    assert data["main_battery_percent"] == 4.0
    assert data["battery_temperature"] == 105.8


def test_on_data_received_triggers_callback_for_successful_notification(config):
    callback_calls = []

    def on_data_callback(client, data):
        callback_calls.append((client, data))

    client = ShuntClient(config, on_data_callback=on_data_callback)
    payload = bytearray(80)
    payload[1] = 87
    payload[21:24] = b"\x00\x03\xE8"
    payload[25:28] = b"\x00\x07\xD0"
    payload[30:32] = b"\x00\x0B\xB8"
    payload[34:36] = b"\x00\x28"
    payload[66:68] = b"\x01\x9A"

    import asyncio

    asyncio.run(client.on_data_received(payload))

    assert len(callback_calls) == 1
    assert callback_calls[0][1]["charge_amps"] == 1.0
