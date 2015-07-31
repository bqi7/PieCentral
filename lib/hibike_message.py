import struct
from enum import Enum

"""
Message IDs for each type of hibike message.
"""
class HibikeMessageType(Enum):
    SubscriptionRequest      = 0x00
    SubscriptionResponse     = 0x01
    SubscriptionSensorUpdate = 0x02
    SensorUpdateRequest      = 0x03
    SensorUpdate             = 0x04
    Error                    = 0xFF

"""
Sensor Type IDs.
"""
class SensorType(Enum):
    LimitSwitch  = 0x00
    LineFollower = 0x01

"""
More specific error codes.
"""
class ErrorCode(Enum):
    InvalidMessageType = 0xFB
    MalformedMessage   = 0xFC
    InvalidArduinoId   = 0xFD
    ChecksumMismatch   = 0xFE
    GenericError       = 0xFF

class HibikeMessageException(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

def getByte(value, index):
    return (value >> (index*8)) & 0xFF


class HibikeMessage:
    def __init__(self, messageId, controllerId, serial):
        assert(isinstance(messageId, HibikeMessageType));
        self.__messageId = messageId
        self.__controllerId = controllerId
        self.__checksum = 0
        self.__serial = serial
    def getMessageId():
        return self.__messageId
    def getControllerId():
        return self.__controllerId
    def getChecksum():
        return self.__checksum

class SubscriptionRequest(HibikeMessage):
    def __init__(self, controllerId, subscriptionDelay, serial):
        HibikeMessage.__init__(self, HibikeMessageType.SubscriptionRequest,
                               controllerId, serial)
        # assert subscriptionDelay is a uint32
        self.__subscriptionDelay = subscriptionDelay
        self.__calculateChecksum()
    def getSubscriptionDelay():
        return self.__subscriptionDelay
    def __calculateChecksum():
        pass
    def send():
        pass

class SubscriptionResponse(HibikeMessage):
    def __init__(self, controllerId, serial):
        HibikeMessage.__init__(self, HibikeMessageType.SubscriptionResponse,
                               controllerId, serial)
        self.__calculateChecksum()
    def __calculateChecksum():
        pass
    def send():
        pass

class SubscriptionSensorUpdate(HibikeMessage):
    def __init__(self, controllerId, sensorTypeId, sensorReadingLength, data, serial):
        HibikeMessage.__init__(self, HibikeMessageType.SubscriptionSensorUpdate,
                               controllerId, serial)
        assert(isinstance(sensorTypeId, SensorType))
        # assert uint8
        self.__sensorTypeId = sensorTypeId
        # assert uint16
        self.__sensorReadingLength = sensorReadingLength
        # assert size in bytes is consistent with sensorReadingLength
        self.__data = data
        self.__calculateChecksum()
    def getSensorTypeId():
        return self.__sensorTypeId
    def getSensorReadingLength():
        return self.__sensorReadingLength
    def getData():
        return self.__data
    def __calculateChecksum():
        pass
    def send():
        pass

class Error(HibikeMessage):
    def __init__(self, controllerId, errorCode):
        HibikeMessage.__init__(self, HibikeMessageType.Error, controllerId, serial)
        assert(isinstance(errorCode, ErrorCode))
        self.__errorCode = errorCode
        self.__calculateChecksum()
    def getErrorCode():
        return self.__errorCode
    def __calculateChecksum():
        pass
    def send():
        pass

def receiveHibikeMessage():
    pass
