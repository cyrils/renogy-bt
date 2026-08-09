import configparser
import pytest

from renogybt.HFInverterClient import HFInverterClient


@pytest.fixture
def config():
    cfg = configparser.ConfigParser()
    cfg.read_dict(
        {
            "device": {"device_id": "32", "alias": "BT-TH-TEST", "mac_addr": "AA:BB:CC:DD:EE:FF"},
            "data": {"poll_interval": "60", "temperature_unit": "F"},
        }
    )
    return cfg


def test_parse_stats_extracts_expected_fields(config):
    client = HFInverterClient(config)
    
    # 3 bytes header + 7 words (14 bytes) = 17 bytes
    payload = bytearray(17)
    payload[0] = 32
    payload[1] = 3
    payload[2] = 14
    
    # ac_input_voltage = 230.5V (2305) -> 0x09 0x01
    payload[3:5] = b"\x09\x01"
    # ac_input_frequency = 50.0Hz (500) -> 0x01 0xf4
    payload[5:7] = b"\x01\xf4"
    # ac_voltage_setting = 230.0V (2300) -> 0x08 0xfc
    payload[7:9] = b"\x08\xfc"
    # battery_discharge_current = 15.5A (155) -> 0x00 0x9b
    payload[9:11] = b"\x00\x9b"
    # battery_temperature = 25.0C (250) -> 0x00 0xfa. In F: 25.0 * 1.8 + 32 = 77.0
    payload[13:15] = b"\x00\xfa"
    # internal_temperature = 35.0C (350) -> 0x01 0x5e. In F: 35.0 * 1.8 + 32 = 95.0
    payload[15:17] = b"\x01\x5e"

    client.parse_stats(payload)
    
    assert client.data["ac_input_voltage"] == 230.5
    assert client.data["ac_input_frequency"] == 50.0
    assert client.data["ac_voltage_setting"] == 230.0
    assert client.data["battery_discharge_current"] == 15.5
    assert client.data["battery_temperature"] == 77.0
    assert client.data["internal_temperature"] == 95.0


def test_parse_device_id(config):
    client = HFInverterClient(config)
    
    # 3 bytes header + 1 word (2 bytes) = 5 bytes
    payload = bytearray(5)
    payload[0] = 32
    payload[1] = 3
    payload[2] = 2
    payload[3:5] = b"\x00\x20" # 32
    
    client.parse_device_id(payload)
    assert client.data["device_id"] == 32


def test_parse_ac_input_present(config):
    client = HFInverterClient(config)
    
    payload = bytearray(5)
    payload[0] = 32
    payload[1] = 3
    payload[2] = 2
    payload[3:5] = b"\x00\x01" # 1
    
    client.parse_ac_input_present(payload)
    assert client.data["ac_input_present"] == 1


def test_parse_inverter_model(config):
    client = HFInverterClient(config)
    
    # 3 bytes header + 8 words (16 bytes) = 19 bytes
    payload = bytearray(19)
    payload[0] = 32
    payload[1] = 3
    payload[2] = 16
    payload[3:19] = b"RIV1230PCH-23S\x00\x00"
    
    client.parse_inverter_model(payload)
    assert client.data["model"] == "RIV1230PCH-23S"


def test_parse_charging_info(config):
    client = HFInverterClient(config)
    
    # 3 bytes header + 6 words (12 bytes) = 15 bytes
    payload = bytearray(15)
    payload[0] = 32
    payload[1] = 3
    payload[2] = 12
    # battery_current = -12.5A (-125) -> signed 16-bit: 65411 -> 0xff 0x83
    payload[3:5] = b"\xff\x83"
    # charging_active = 1 -> 0x00 0x01
    payload[11:13] = b"\x00\x01"
    # charging_power_amps = 12.5A (125) -> 0x00 0x7d
    payload[13:15] = b"\x00\x7d"
    
    client.parse_charging_info(payload)
    assert client.data["battery_current"] == -12.5
    assert client.data["charging_active"] == 1
    assert client.data["charging_power_amps"] == 12.5


def test_parse_operating_info(config):
    client = HFInverterClient(config)
    
    # 3 bytes header + 18 words (36 bytes) = 39 bytes
    payload = bytearray(39)
    payload[0] = 32
    payload[1] = 3
    payload[2] = 36
    # operating_mode_raw = 4 (line/charging) -> 0x00 0x04
    payload[3:5] = b"\x00\x04"
    # charging_current = 20.0A (200) -> word 7 -> index 3 + 7*2 = 17
    payload[17:19] = b"\x00\xc8"
    # max_charging_current_setting = 50.0A (500) -> word 17 -> index 3 + 17*2 = 37
    payload[37:39] = b"\x01\xf4"
    
    client.parse_operating_info(payload)
    assert client.data["operating_mode_raw"] == 4
    assert client.data["operating_mode"] == "line/charging"
    assert client.data["charging_current"] == 20.0
    assert client.data["max_charging_current_setting"] == 50.0
