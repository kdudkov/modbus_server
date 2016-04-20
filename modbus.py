#!/usr/bin/env python
from threading import Lock

import serial
import logging

logger = logging.getLogger(__name__)

_CRC16TABLE = (0x0, 0xc0c1, 0xc181, 0x140, 0xc301, 0x3c0, 0x280, 0xc241, 0xc601, 0x6c0, 0x780, 0xc741, 0x500, 0xc5c1, 0xc481, 
    0x440, 0xcc01, 0xcc0, 0xd80, 0xcd41, 0xf00, 0xcfc1, 0xce81, 0xe40, 0xa00, 0xcac1, 0xcb81, 0xb40, 0xc901, 0x9c0, 0x880, 
    0xc841, 0xd801, 0x18c0, 0x1980, 0xd941, 0x1b00, 0xdbc1, 0xda81, 0x1a40, 0x1e00, 0xdec1, 0xdf81, 0x1f40, 0xdd01, 0x1dc0, 
    0x1c80, 0xdc41, 0x1400, 0xd4c1, 0xd581, 0x1540, 0xd701, 0x17c0, 0x1680, 0xd641, 0xd201, 0x12c0, 0x1380, 0xd341, 0x1100, 
    0xd1c1, 0xd081, 0x1040, 0xf001, 0x30c0, 0x3180, 0xf141, 0x3300, 0xf3c1, 0xf281, 0x3240, 0x3600, 0xf6c1, 0xf781, 0x3740, 
    0xf501, 0x35c0, 0x3480, 0xf441, 0x3c00, 0xfcc1, 0xfd81, 0x3d40, 0xff01, 0x3fc0, 0x3e80, 0xfe41, 0xfa01, 0x3ac0, 0x3b80, 
    0xfb41, 0x3900, 0xf9c1, 0xf881, 0x3840, 0x2800, 0xe8c1, 0xe981, 0x2940, 0xeb01, 0x2bc0, 0x2a80, 0xea41, 0xee01, 0x2ec0, 
    0x2f80, 0xef41, 0x2d00, 0xedc1, 0xec81, 0x2c40, 0xe401, 0x24c0, 0x2580, 0xe541, 0x2700, 0xe7c1, 0xe681, 0x2640, 0x2200, 
    0xe2c1, 0xe381, 0x2340, 0xe101, 0x21c0, 0x2080, 0xe041, 0xa001, 0x60c0, 0x6180, 0xa141, 0x6300, 0xa3c1, 0xa281, 0x6240, 
    0x6600, 0xa6c1, 0xa781, 0x6740, 0xa501, 0x65c0, 0x6480, 0xa441, 0x6c00, 0xacc1, 0xad81, 0x6d40, 0xaf01, 0x6fc0, 0x6e80, 
    0xae41, 0xaa01, 0x6ac0, 0x6b80, 0xab41, 0x6900, 0xa9c1, 0xa881, 0x6840, 0x7800, 0xb8c1, 0xb981, 0x7940, 0xbb01, 0x7bc0, 
    0x7a80, 0xba41, 0xbe01, 0x7ec0, 0x7f80, 0xbf41, 0x7d00, 0xbdc1, 0xbc81, 0x7c40, 0xb401, 0x74c0, 0x7580, 0xb541, 0x7700, 
    0xb7c1, 0xb681, 0x7640, 0x7200, 0xb2c1, 0xb381, 0x7340, 0xb101, 0x71c0, 0x7080, 0xb041, 0x5000, 0x90c1, 0x9181, 0x5140, 
    0x9301, 0x53c0, 0x5280, 0x9241, 0x9601, 0x56c0, 0x5780, 0x9741, 0x5500, 0x95c1, 0x9481, 0x5440, 0x9c01, 0x5cc0, 0x5d80, 
    0x9d41, 0x5f00, 0x9fc1, 0x9e81, 0x5e40, 0x5a00, 0x9ac1, 0x9b81, 0x5b40, 0x9901, 0x59c0, 0x5880, 0x9841, 0x8801, 0x48c0, 
    0x4980, 0x8941, 0x4b00, 0x8bc1, 0x8a81, 0x4a40, 0x4e00, 0x8ec1, 0x8f81, 0x4f40, 0x8d01, 0x4dc0, 0x4c80, 0x8c41, 0x4400, 
    0x84c1, 0x8581, 0x4540, 0x8701, 0x47c0, 0x4680, 0x8641, 0x8201, 0x42c0, 0x4380, 0x8341, 0x4100, 0x81c1, 0x8081, 0x4040)


def to_be(n):
    return n & 0xff, (n & 0xff00) >> 8


def to_le(n):
    return (n & 0xff00) >> 8, n & 0xff


def string_crc(s):
    crc = 0xFFFF

    for char in s:
        crc = (crc >> 8) ^ _CRC16TABLE[(crc ^ ord(char)) & 0xFF]
    
    return to_be(crc)


def msg_crc(s):
    crc = 0xFFFF

    for c in s:
        crc = (crc >> 8) ^ _CRC16TABLE[(crc ^ c) & 0xFF]
    
    return to_be(crc)


def to_hex(s):
    return ' '.join(hex(x)[2:].zfill(2) for x in s)


def _calculate_minimum_silent_period(baudrate):
    """Calculate the silent period length to comply with the 3.5 character silence between messages.
    Args:
        baudrate (numerical): The baudrate for the serial port
    Returns:
        The number of seconds (float) that should pass between each message on the bus.
    """

    BITTIMES_PER_CHARACTERTIME = 11
    MINIMUM_SILENT_CHARACTERTIMES = 3.5

    bittime = 1 / float(baudrate)
    return bittime * BITTIMES_PER_CHARACTERTIME * MINIMUM_SILENT_CHARACTERTIMES


class RtuMessage(object):
    
    def __init__(self):
        self.addr = 0
        self.fn = 0
        self.payload = ''
        
    @classmethod
    def from_list(cls, s, answer=True):
        if not s or len(s) < 5:
            raise Exception('invalid message')
        if isinstance(s, str):
            msg = [ord(x) for x in s]
        else:
            msg = s
        r = RtuMessage()
        r.addr = msg[0]
        r.fn = msg[1]
        if answer:
            r.size = msg[2]
            r.payload = msg[3:-2]
        else:
            r.size = 0
            r.payload = msg[2:-2]
        crc = msg_crc(msg[:-2])
        assert list(crc) == msg[-2:], 'invalid crc'
        return r
        
    @classmethod
    def make(cls, addr, fn, payload):
        r = RtuMessage()
        r.addr = addr
        r.fn = fn
        r.payload = payload
        return r
    
    def to_list(self):
        msg = [self.addr, self.fn]
        msg += self.payload
        msg += msg_crc(msg)
        return msg

    def __repr__(self):
        return 'addr: {}, fn: {}, payload: {}'.format(self.addr, self.fn, to_hex(self.payload))


class ModbusDevice(object):
    debug = False

    def __init__(self, dev, baudrate=9600):
        self.serial = serial.Serial(port=dev, baudrate=baudrate, parity=serial.PARITY_NONE, bytesize=8, stopbits=1, timeout=0.05)
        self.serial.baudrate = baudrate
        self.lock = Lock()

    def _communicate(self, request, read_size):
        self.lock.acquire()
        try:
            self.serial.write(request)
            s = self.serial.read(read_size)
            if isinstance(s, str):
                answer = [ord(x) for x in s]
            else:
                answer = [x for x in s]
            if not answer:
                raise Exception('timeout')
            logger.debug('answer: %s', to_hex(answer))
            msg = RtuMessage.from_list(answer, False)
            return msg
        finally:
            self.lock.release()

    def read_coils(self, addr, start, num):
        msg = RtuMessage.make(addr, 1, to_le(start) + to_le(num))
        req = msg.to_list()
        logger.debug('msg: %s', to_hex(req))
        resp = self._communicate(req, 5 + int((num + 8) / 8))
        return resp.payload

    def read_input(self, addr, reg_addr, num=1):
        msg = RtuMessage.make(addr, 2, to_le(reg_addr) + to_le(num))
        req = msg.to_list()
        logger.debug('msg: %s', to_hex(req))
        resp = self._communicate(req, 5 + int((num + 8) / 8))
        return resp.payload

    def read_reg(self, addr, reg_addr, num=1):
        msg = RtuMessage.make(addr, 3, to_le(reg_addr) + to_le(num))
        req = msg.to_list()
        logger.debug('msg: %s', to_hex(req))
        resp = self._communicate(req, len(req))
        return resp.payload

    def read_input_analog(self, addr, reg_addr, num=1):
        msg = RtuMessage.make(addr, 4, to_le(reg_addr) + to_le(num))
        req = msg.to_list()
        logger.debug('msg: %s', to_hex(req))
        resp = self._communicate(req, 5 + num * 2)
        return resp.payload

    def write_coil(self, addr, reg_addr, val):
        msg = RtuMessage.make(addr, 5, to_le(reg_addr) + to_le(val))
        req = msg.to_list()
        logger.debug('msg: %s', to_hex(req))
        resp = self._communicate(req, len(req))
        return resp.payload

    def write_reg(self, addr, reg_addr, val):
        msg = RtuMessage.make(addr, 6, to_le(reg_addr) + to_le(val))
        req = msg.to_list()
        logger.debug('msg: %s', to_hex(req))
        resp = self._communicate(req, len(req))
        return resp.payload

if __name__ == '__main__':
    logging.basicConfig(level='DEBUG')

    d = ModbusDevice('/dev/rs485')

    print(d.write_reg(1, 2, 0x200))
    # print(d.read_reg(1, 2, 1))

    #d.write_coil(1, 0x0)

    #print d.read_coils(2, 2)
    #print d.read_input(1, 4)