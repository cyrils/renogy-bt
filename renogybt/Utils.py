import logging
import libscrc

CHARGING_STATE = {
    0: 'deactivated',
    1: 'activated',
    2: 'mppt',
    3: 'equalizing',
    4: 'boost',
    5: 'floating',
    6: 'current limiting'
}

LOAD_STATE = {
  0: 'off',
  1: 'on'
}

FUNCTION = {
    3: "READ",
    6: "WRITE"
}

def bytes_to_int(bs, offset, length):
        # Reads data from a list of bytes, and converts to an int
        # bytes_to_int(bs, 3, 2)
        ret = 0
        if len(bs) < (offset + length):
            return ret
        if length > 0:
            byteorder='big'
            start = offset
            end = offset + length
        else:
            byteorder='little'
            start = offset + length + 1
            end = offset + 1
        return int.from_bytes(bs[start:end], byteorder=byteorder)


def int_to_bytes(i, pos = 0):
    # Converts an integer into 2 bytes (16 bits)
    # Returns either the first or second byte as an int
    if pos == 0:
        return int(format(i, '016b')[:8], 2)
    if pos == 1:
        return int(format(i, '016b')[8:], 2)
    return 0


def create_request_payload(device_id, function, regAddr, readWrd):                             
    data = None                                

    if regAddr:
        data = []
        data.append(device_id)
        data.append(function)
        data.append(int_to_bytes(regAddr, 0))
        data.append(int_to_bytes(regAddr, 1))
        data.append(int_to_bytes(readWrd, 0))
        data.append(int_to_bytes(readWrd, 1))

        crc = libscrc.modbus(bytes(data))
        data.append(int_to_bytes(crc, 1))
        data.append(int_to_bytes(crc, 0))
        logging.debug("{} {} => {}".format("create_read_request", regAddr, data))
    return data

def parse_charge_controller_info(bs):
    data = {}
    data['function'] = FUNCTION[bytes_to_int(bs, 1, 1)]
    data['battery_percentage'] = bytes_to_int(bs, 3, 2)
    data['battery_voltage'] = bytes_to_int(bs, 5, 2) * 0.1
    data['battery_current'] = bytes_to_int(bs, 7, 2) * 0.01
    data['battery_temperature'] = parse_temperature(bytes_to_int(bs, 10, 1))
    data['controller_temperature'] = parse_temperature(bytes_to_int(bs, 9, 1))
    data['load_status'] = LOAD_STATE[bytes_to_int(bs, 67, 1) >> 7]
    data['load_voltage'] = bytes_to_int(bs, 11, 2) * 0.1
    data['load_current'] = bytes_to_int(bs, 13, 2) * 0.01
    data['load_power'] = bytes_to_int(bs, 15, 2)
    data['pv_voltage'] = bytes_to_int(bs, 17, 2) * 0.1
    data['pv_current'] = bytes_to_int(bs, 19, 2) * 0.01
    data['pv_power'] = bytes_to_int(bs, 21, 2)
    data['max_charging_power_today'] = bytes_to_int(bs, 33, 2)
    data['max_discharging_power_today'] = bytes_to_int(bs, 35, 2)
    data['charging_amp_hours_today'] = bytes_to_int(bs, 37, 2)
    data['discharging_amp_hours_today'] = bytes_to_int(bs, 39, 2)
    data['power_generation_today'] = bytes_to_int(bs, 41, 2)
    data['power_consumption_today'] = bytes_to_int(bs, 43, 2)
    data['power_generation_total'] = bytes_to_int(bs, 59, 4)
    data['charging_status'] = CHARGING_STATE[bytes_to_int(bs, 68, 1)]
    return data

def parse_set_load_response(bs):
    data = {}
    data['function'] = FUNCTION[bytes_to_int(bs, 1, 1)]
    data['load_status'] = bytes_to_int(bs, 5, 1)
    return data

def parse_temperature(raw_value):
    sign = raw_value >> 7
    return -(raw_value - 128) if sign == 1 else raw_value

def parse_battery_info(bs):
    data = {}
    data['function'] = FUNCTION.get(bytes_to_int(bs, 1, 1))
    data['cell_count'] = bytes_to_int(bs, 3, 2)
    data['sensor_count'] = bytes_to_int(bs, 37, 2)

    for i in range(0, data['cell_count']):
        data[f'cell_voltage_{i}'] = bytes_to_int(bs, 5 + i*2, 2) * 0.1

    for i in range(0, data['sensor_count']):
        data[f'temperature_{i}'] = bytes_to_int(bs, 39 + i*2, 2) * 0.1

    data['current'] = bytes_to_int(bs, 87, 2) * 0.01
    data['voltage'] = bytes_to_int(bs, 89, 2) * 0.1
    data['remaining_charge'] = bytes_to_int(bs, 91, 4) * 0.001
    data['capacity'] = bytes_to_int(bs, 95, 4) * 0.001

    return data
