def bytes_to_int(bs, offset, length, signed = False):
        # Reads data from a list of bytes, and converts to an int
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
        return int.from_bytes(bs[start:end], byteorder = byteorder, signed = signed)

def int_to_bytes(i, pos = 0):
    # Converts an integer into 2 bytes (16 bits)
    # Returns either the first or second byte as an int
    if pos == 0:
        return int(format(i, '016b')[:8], 2)
    if pos == 1:
        return int(format(i, '016b')[8:], 2)
    return 0

def parse_temperature(raw_value):
    sign = raw_value >> 7
    return -(raw_value - 128) if sign == 1 else raw_value
