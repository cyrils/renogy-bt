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

def Bytes2Int(bs, offset, length):
        # Reads data from a list of bytes, and converts to an int
        # Bytes2Int(bs, 3, 2)
        ret = 0
        if len(bs) < (offset + length):
            return ret
        if length > 0:
            # offset = 11, length = 2 => 11 - 12
            byteorder='big'
            start = offset
            end = offset + length
        else:
            # offset = 11, length = -2 => 10 - 11
            byteorder='little'
            start = offset + length + 1
            end = offset + 1
        # Easier to read than the bitshifting below
        return int.from_bytes(bs[start:end], byteorder=byteorder)


def Int2Bytes(i, pos = 0):
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
        data.append(Int2Bytes(regAddr, 0))
        data.append(Int2Bytes(regAddr, 1))
        data.append(Int2Bytes(readWrd, 0))
        data.append(Int2Bytes(readWrd, 1))

        crc = libscrc.modbus(bytes(data))
        data.append(Int2Bytes(crc, 1))
        data.append(Int2Bytes(crc, 0))
        logging.debug("{} {} => {}".format("create_read_request", regAddr, data))
    return data

def parse_charge_controller_info(bs):
    data = {}
    data['function'] = FUNCTION[Bytes2Int(bs, 1, 1)]
    data['battery_percentage'] = Bytes2Int(bs, 3, 2)
    data['battery_voltage'] = Bytes2Int(bs, 5, 2) * 0.1
    data['battery_current'] = Bytes2Int(bs, 7, 2) * 0.01
    data['battery_temperature'] = parse_temperature(Bytes2Int(bs, 10, 1))
    data['controller_temperature'] = parse_temperature(Bytes2Int(bs, 9, 1))
    data['load_status'] = LOAD_STATE[Bytes2Int(bs, 67, 1) >> 7]
    data['load_voltage'] = Bytes2Int(bs, 11, 2) * 0.1
    data['load_current'] = Bytes2Int(bs, 13, 2) * 0.01
    data['load_power'] = Bytes2Int(bs, 15, 2)
    data['pv_voltage'] = Bytes2Int(bs, 17, 2) * 0.1
    data['pv_current'] = Bytes2Int(bs, 19, 2) * 0.01
    data['pv_power'] = Bytes2Int(bs, 21, 2)
    data['max_charging_power_today'] = Bytes2Int(bs, 33, 2)
    data['max_discharging_power_today'] = Bytes2Int(bs, 35, 2)
    data['charging_amp_hours_today'] = Bytes2Int(bs, 37, 2)
    data['discharging_amp_hours_today'] = Bytes2Int(bs, 39, 2)
    data['power_generation_today'] = Bytes2Int(bs, 41, 2)
    data['power_consumption_today'] = Bytes2Int(bs, 43, 2)
    data['power_generation_total'] = Bytes2Int(bs, 59, 4)
    data['charging_status'] = CHARGING_STATE[Bytes2Int(bs, 68, 1)]
    return data

def parse_set_load_response(bs):
    data = {}
    data['function'] = FUNCTION[Bytes2Int(bs, 1, 1)]
    data['load_status'] = Bytes2Int(bs, 5, 1)
    return data

def parse_temperature(raw_value):
    sign = raw_value >> 7
    return -(raw_value - 128) if sign == 1 else raw_value
