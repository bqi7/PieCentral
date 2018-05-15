"""
Functions and classes for dealing with Hibike packets.
"""
from __future__ import print_function
# Rewritten because Python.__version__ != 3
import struct
import os
import json
import threading

CONFIG_FILE = open(os.path.join(
    os.path.dirname(__file__), 'hibikeDevices.json'), 'r')
DEVICES = json.load(CONFIG_FILE)

PARAM_MAP = {device["id"]: {param["name"]: (param["number"],
                                            param["type"],
                                            param["read"],
                                            param["write"]) for param in device["params"]}
             for device in DEVICES}
"""
A mapping from device IDs to information about devices.
"""
DEVICES = {device["id"]: device for device in DEVICES}
"""
Smart sensors and their associated device IDs.
"""
# pylint: disable=pointless-string-statement
"""
structure of devices
{0:
    {"id": 0, "name": "LimitSwitch",
    "params": [
        {"number": 0, "name": "switch0", "type": "bool", "read": True, "write": False}
    ]
    }
}

"""


PARAM_TYPES = {
    "bool": "?",
    "uint8_t": "B",
    "int8_t": "b",
    "uint16_t": "H",
    "int16_t": "h",
    "uint32_t": "I",
    "int32_t": "i",
    "uint64_t": "Q",
    "int64_t": "q",
    "float": "f",
    "double": "d"
}
"""
Dictionary mapping parameter types to Python ``struct`` format characters.
"""


MESSAGE_TYPES = {
    "Ping":                 0x10,
    "SubscriptionRequest":  0x11,
    "SubscriptionResponse": 0x12,
    "DeviceRead":           0x13,
    "DeviceWrite":          0x14,
    "DeviceData":           0x15,
    "Disable":               0x16,
    "HeartBeatRequest":     0x17,
    "HeartBeatResponse":    0x18,
    "Error":                0xFF
}
"""
A mapping from message type to message ID.
"""


ERROR_CODES = {
    "UnexpectedDelimiter": 0xFD,
    "CheckumError": 0xFE,
    "GenericError": 0xFF
}
"""
A mapping from error types to error codes.
"""


class HibikeMessage:
    """
    An Hibike packet.
    """
    def __init__(self, message_id, payload):
        assert message_id in MESSAGE_TYPES.values()
        self._message_id = message_id
        self._payload = payload[:]
        self._length = len(payload)

    def get_message_id(self):
        """
        Get the message ID.
        """
        return self._message_id

    def get_payload(self):
        """
        Get a copy of the payload as a bytearray.
        """
        return self._payload[:]

    def to_bytes(self):
        """
        A representation of this message in bytes.
        """
        m_buff = bytearray()
        m_buff.append(self._message_id)
        m_buff.append(self._length)
        m_buff.extend(self.get_payload())
        return m_buff

    def __str__(self):
        return str([self._message_id] + [self._length] + list(self._payload))

    def __repr__(self):
        return str(self)


def get_device_type(uid):
    """
    Decode a device type from a UID.
    """
    return int(uid >> 72)


def get_year(uid):
    """
    Decode the year from a uid.
    """
    temp = uid >> 64
    return int(temp & 0xFF)


def get_id(uid):
    """
    Decode the unique part of a UID.
    """
    return uid & 0xFFFFFFFFFFFFFFFF


def checksum(data):
    """
    Compute a checksum for DATA.
    """
    # Remove this later after development
    assert isinstance(data, bytearray), "data must be a bytearray"

    chk = data[0]
    for i in range(1, len(data)):
        chk ^= data[i]
    return chk


def send(serial_conn, message):
    """
    Send a message over a serial connection.

    :param serial_conn: The serial connection object
    :param message: A ``HibikeMessage``
    """
    m_buff = message.to_bytes()
    chk = checksum(m_buff)
    m_buff.append(chk)
    encoded = cobs_encode(m_buff)
    out_buf = bytearray([0x00, len(encoded)]) + encoded
    serial_conn.write(out_buf)


def encode_params(device_id, params):
    """
    Encode a list of parameter names into a bitmask.

    :param device_id: A device type ID (not UID)
    :param params: A list of parameter names
    :return: An int that contains the parameter bitmask
    """
    param_nums = [PARAM_MAP[device_id][name][0] for name in params]
    entries = [1 << num for num in param_nums]
    mask = 0
    for entry in entries:
        mask = mask | entry
    return mask


def decode_params(device_id, params_bitmask):
    """
    Decode a bitmask into a list of parameter names.

    :param device_id: A device type ID
    :param params_bitmask: An integer containing the bitmask
    :return: A list of parameter names corresponding to the bitmask
    """
    converted_params = []
    for param_count in range(16):
        if (params_bitmask & (1 << param_count)) > 0:
            converted_params.append(param_count)
    named_params = []
    for param in converted_params:
        if param >= len(DEVICES[device_id]["params"]):
            break
        named_params.append(DEVICES[device_id]["params"][param]["name"])
    return named_params


def format_string(device_id, params):
    """
    The ``struct`` format string representing the types of parameters.

    :param device_id: A device type ID
    :param params: A list of parameter names
    """
    param_types = [PARAM_MAP[device_id][name][1] for name in params]

    type_string = ''
    for ptype_key in param_types:
        type_string += PARAM_TYPES[ptype_key]
    return type_string


def make_ping():
    """ Makes and returns Ping message."""
    payload = bytearray()
    message = HibikeMessage(MESSAGE_TYPES["Ping"], payload)
    return message


def make_disable():
    """ Makes and returns a Disable message."""
    payload = bytearray()
    message = HibikeMessage(MESSAGE_TYPES["Disable"], payload)
    return message


def make_heartbeat_response(heartbeat_id=0):
    """ Makes and returns HeartBeat message."""
    payload = bytearray(struct.pack('<B', heartbeat_id))
    message = HibikeMessage(MESSAGE_TYPES["HeartBeatResponse"], payload)
    return message


def make_subscription_request(device_id, params, delay):
    """
    Makes and returns SubscriptionRequest message.

    Looks up config data about the specified
    device_id to properly construct the message.

    :param device_id: a device type id (not uid).
    :param params: an iterable of param names
    :param delay: the delay in milliseconds
    """
    params_bitmask = encode_params(device_id, params)
    temp_payload = struct.pack('<HH', params_bitmask, delay)
    payload = bytearray(temp_payload)
    message = HibikeMessage(MESSAGE_TYPES["SubscriptionRequest"], payload)
    return message


def make_subscription_response(device_id, params, delay, uid):
    """
    Makes and returns SubscriptionResponse message.

    Looks up config data about the specified
    device_id to properly construct the message.

    :param device_id: a device type id (not uid).
    :param params: an iterable of param names
    :param delay: the delay in milliseconds
    :param uid: the uid
    """
    params_bitmask = encode_params(device_id, params)
    device_type = get_device_type(uid)
    year = get_year(uid)
    id_num = get_id(uid)
    temp_payload = struct.pack(
        "<HHHBQ", params_bitmask, delay, device_type, year, id_num)
    payload = bytearray(temp_payload)
    message = HibikeMessage(MESSAGE_TYPES["SubscriptionResponse"], payload)

    return message


def make_device_read(device_id, params):
    """
    Makes and returns DeviceRead message.

    Looks up config data about the specified
    device_id to properly construct the message.

    :param device_id: a device type id (not uid).
    :param params: an iterable of param names
    """
    params_bitmask = encode_params(device_id, params)
    temp_payload = struct.pack('<H', params_bitmask)
    payload = bytearray(temp_payload)
    message = HibikeMessage(MESSAGE_TYPES["DeviceRead"], payload)
    return message


def make_device_write(device_id, params_and_values):
    """
    Makes and returns DeviceWrite message.
    If all the params cannot fit, it will fill as many as it can.

    Looks up config data about the specified
    device_id to properly construct the message.

    :param device_id: a device type id (not uid).
    :param params_and_values: an iterable of param (name, value) tuples
    """
    params_and_values = sorted(
        params_and_values, key=lambda x: PARAM_MAP[device_id][x[0]][0])
    params = [param[0] for param in params_and_values]
    params_bitmask = encode_params(device_id, params)
    values = [param[1] for param in params_and_values]

    type_string = '<H' + format_string(device_id, params)
    temp_payload = struct.pack(type_string, params_bitmask, *values)
    payload = bytearray(temp_payload)
    message = HibikeMessage(MESSAGE_TYPES["DeviceWrite"], payload)
    return message


def make_device_data(device_id, params_and_values):
    """
    Makes and returns DeviceData message.

    If all the params cannot fit, it will fill as many as it can.
    Looks up config data about the specified
    device_id to properly construct the message.

    :param device_id: a device type id (not uid).
    :param params_and_values: an iterable of param (name, value) tuples
    """
    params = [param_tuple[0] for param_tuple in params_and_values]
    params_bitmask = encode_params(device_id, params)
    values = [param_tuple[1] for param_tuple in params_and_values]

    type_string = '<H' + format_string(device_id, params)

    temp_payload = struct.pack(type_string, params_bitmask, *values)
    payload = bytearray(temp_payload)

    message = HibikeMessage(MESSAGE_TYPES["DeviceData"], payload)
    return message


def make_error(error_code):
    """ Makes and returns Error message."""
    temp_payload = struct.pack('<B', error_code)
    payload = bytearray(temp_payload)
    message = HibikeMessage(MESSAGE_TYPES["Error"], payload)
    return message


def parse_subscription_response(msg):
    """
    Decode a subscription response into its parts.

    :param msg: A ``HibikeMessage`` containing a subscription response packet
    :return: A tuple containing a list of parameter names, the delay, and the UID
    """
    assert msg.get_message_id() == MESSAGE_TYPES["SubscriptionResponse"]
    payload = msg.get_payload()
    assert len(payload) == 15
    params, delay, device_id, year, id_num = struct.unpack("<HHHBQ", payload)
    params = decode_params(device_id, params)
    uid = (device_id << 72) | (year << 64) | id_num
    return (params, delay, uid)


def decode_device_write(msg, device_id):
    """
    Decode a device write packet.

    :param msg: A ``HibikeMessage`` containing a device write packet
    :param device_id: A device id
    :return: A list of (parameter name, value) pairs
    """
    assert msg.get_message_id() == MESSAGE_TYPES["DeviceWrite"]
    payload = msg.get_payload()
    assert len(payload) >= 2
    params, = struct.unpack("<H", payload[:2])
    params = decode_params(device_id, params)
    struct_format = "<" + format_string(device_id, params)
    values = struct.unpack(struct_format, payload[2:])
    return list(zip(params, values))


def parse_device_data(msg, device_id):
    """
    Decode a device data packet into parameters and values.

    :param msg: A ``HibikeMessage`` containing a device data packet
    :param device_id: A device ID
    :returns: A list of (parameter name, value) pairs
    """
    assert msg.get_message_id() == MESSAGE_TYPES["DeviceData"]
    payload = msg.get_payload()
    assert len(payload) >= 2
    params, = struct.unpack("<H", payload[:2])
    params = decode_params(device_id, params)
    struct_format = "<" + format_string(device_id, params)
    values = struct.unpack(struct_format, payload[2:])
    return list(zip(params, values))


def parse_bytes(msg_bytes):
    """
    Try to parse bytes into a valid packet.

    :param msg_bytes: The raw bytes of the packet
    :return: A ``HibikeMessage`` with the packet data, or ``None``, if it couldn't be parsed
    """
    if len(msg_bytes) < 2:
        return None
    cobs_frame, message_size = struct.unpack('<BB', msg_bytes[:2])
    if cobs_frame != 0 or len(msg_bytes) < message_size + 2:
        return None
    message = cobs_decode(msg_bytes[2:message_size + 2])

    if len(message) < 2:
        return None
    message_id, payload_length = struct.unpack('<BB', message[:2])
    if len(message) < 2 + payload_length + 1:
        return None
    payload = message[2:2 + payload_length]
    chk = struct.unpack(
        '<B', message[2 + payload_length:2 + payload_length + 1])[0]
    if chk != checksum(message[:-1]):
        return None
    return HibikeMessage(message_id, payload)


def blocking_read_generator(serial_conn, stop_event=threading.Event()):
    """
    Yield packets from a serial connection.

    :param serial_conn: The connection to read from
    :param stop_event: An Event that, if triggered, stops additional reads
    """
    zero_byte = bytes([0])
    packets_buffer = bytearray()
    # Switch to nonblocking mode so that we don't get stuck reading
    old_timeout = serial_conn.timeout
    serial_conn.timeout = 0
    while not stop_event.is_set():
        # Wait for a 0 byte to appear
        if packets_buffer.find(zero_byte) == -1:
            new_bytes = serial_conn.read(max(1, serial_conn.inWaiting()))
            packets_buffer.extend(new_bytes)
            continue

        # Truncate incomplete packets at start of buffer
        packets_buffer = packets_buffer[packets_buffer.find(zero_byte):]

        # Attempt to parse a packet
        packet = parse_bytes(packets_buffer)

        if packet != None:
            # Chop off a byte so we don't output this packet again
            packets_buffer = packets_buffer[1:]
            yield packet
        else:
            # If there's another packet in the buffer
            # we can safely jump to it for the next iteration
            if packets_buffer.count(zero_byte) > 1:
                new_packet = packets_buffer[1:].find(zero_byte) + 1
                packets_buffer = packets_buffer[new_packet:]
            # Otherwise, there might be more incoming bytes for the current packet,
            # so we do a read and try again
            else:
                new_bytes = serial_conn.read(max(1, serial_conn.inWaiting()))
                packets_buffer.extend(new_bytes)

    serial_conn.timeout = old_timeout



def blocking_read(serial_conn):
    """
    Read a list of packets from a serial connection, blocking until they are complete.

    `This function is deprecated.`

    :param serial_conn: The connection to read from
    :return: A list of packets read from the connection
    """
    zero_byte = bytes([0])
    packets = bytearray()
    while packets.find(zero_byte) == -1:
        packets.extend(serial_conn.read(max(1, serial_conn.inWaiting())))

    # Truncate incomplete packets at start of buffer
    packets = packets[packets.find(zero_byte):]

    # Read until we have no incomplete packets
    last_zero = packets.rfind(zero_byte)
    if last_zero == len(packets) - 1:
        packets.extend(serial_conn.read(size=1))
    last_message_size = packets[last_zero + 1]

    # -2 because payload length and zero byte are not counted
    received_payload = len(packets) - last_zero - 2

    # We don't need to account for the checksum because it is part of the payload
    packets.extend(serial_conn.read(last_message_size - received_payload))

    packet_list = []
    while packets:
        next_packet = packets[1:].find(zero_byte)
        if next_packet == -1:
            next_packet = len(packets)
        else:
            # because we searched in packets[1:] instead of packets
            next_packet += 1
        packet = parse_bytes(packets)
        if packet != None:
            packet_list.append(packet)
        packets = packets[next_packet:]

    return packet_list

# constructs a new object Message by continually reading from input
# Uses dictionary to figure out length of data to know how many bytes to read
# Returns:
    # None if no message
    # -1 if checksum does not match
    # Otherwise returns a new HibikeMessage with message contents


def read(serial_conn):
    """
    Continually read from a serial connection to construct a packet.

    `This function is deprecated.`

    :param serial_conn: The connection to read from
    :return: ``None`` if no message, ``-1`` if bad checksum, otherwise a new ``HibikeMessage``
    """
    # deal with cobs encoding
    while serial_conn.inWaiting() > 0:
        if struct.unpack('<B', serial_conn.read())[0] == 0:
            break
    else:
        return None
    message_size = struct.unpack('<B', serial_conn.read())[0]
    encoded_message = serial_conn.read(message_size)
    message = cobs_decode(encoded_message)

    if len(message) < 2:
        return None
    message_id, payload_length = struct.unpack('<BB', message[:2])
    if len(message) < 2 + payload_length+ 1:
        return None
    payload = message[2:2 + payload_length]

    chk = struct.unpack(
        '<B', message[2 + payload_length:2 + payload_length+ 1])[0]
    if chk != checksum(message[:-1]):
        print(chk, checksum(message[:-1]), list(message))
        return -1

    return HibikeMessage(message_id, payload)


def cobs_encode(data):
    """
    COBS-encode some data.
    """
    output = bytearray()
    curr_block = bytearray()
    for byte in data:
        if byte:
            curr_block.append(byte)
            if len(curr_block) == 254:
                output.append(1 + len(curr_block))
                output.extend(curr_block)
                curr_block = bytearray()
        else:
            output.append(1 + len(curr_block))
            output.extend(curr_block)
            curr_block = bytearray()
    output.append(1 + len(curr_block))
    output.extend(curr_block)
    return output


def cobs_decode(data):
    """
    Decode COBS-encoded data.
    """
    output = bytearray()
    index = 0
    while index < len(data):
        block_size = data[index] - 1
        index += 1
        if index + block_size > len(data):
            return bytearray()
        output.extend(data[index:index + block_size])
        index += block_size
        if block_size + 1 < 255 and index < len(data):
            output.append(0)
    return output


class HibikeMessageException(Exception):
    """
    An exception caused by a Hibike message.
    """
    pass
# Config file helper functions


def device_name_to_id(name):
    """
    Turn a device name to a device ID.
    """
    for device in DEVICES.values():
        if device["name"] == name:
            return device["id"]
    raise HibikeMessageException("Invalid device name: %s" % name)


def device_id_to_name(device_id):
    """
    Turn a device ID into a device name.
    """
    for device in DEVICES.values():
        if device["id"] == device_id:
            return device["name"]
    raise HibikeMessageException("Invalid device id: %d" % id)


def uid_to_device_name(uid):
    """
    Turn a UID into a device name.
    """
    return device_id_to_name(uid_to_device_id(uid))


def uid_to_device_id(uid):
    """
    Turn a UID into a device ID.
    """
    return uid >> 72


def all_params_for_device_id(device_id):
    """
    Get all parameters that a device has.
    """
    return list(PARAM_MAP[device_id].keys())


def readable(device_id, param):
    """
    Check that a parameter is readable for a device.
    """
    return PARAM_MAP[device_id][param][2]


def writable(device_id, param):
    """
    Check that a parameter is writeable for a device.
    """
    return PARAM_MAP[device_id][param][3]


def param_type(device_id, param):
    """
    Return the data type of the requested parameter.
    """
    return PARAM_MAP[device_id][param][1]
