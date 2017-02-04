#!/usr/bin/env python

import logging
import struct


logger = logging.getLogger(__name__)


def hex_data(data):
    return ' '.join((hex(x)[2:].rjust(2, '0') for x in data))


class TcpMessage(object):
    def __init__(self):
        self.tr_id = 0
        self.pr_id = 0
        self.size = 6
        self.addr = 0
        self.payload = bytes()

    @staticmethod
    def decode_tcp(s):
        if isinstance(s, str):
            data = s.encode('utf-8')
        else:
            data = s
        if len(data) < 8:
            raise Exception('invalid tcp message size')
        tr_id, pr_id, size, addr, fn = struct.unpack_from('>HHHBB', data)
        if len(data) != size + 6:
            logger.error('invalid size')
            return {}
        payload = data[8:]
        logger.debug('fn %s to addr %s, data %s', fn, addr, hex_data(payload))
        msg = TcpMessage()
        msg.tr_id = tr_id
        msg.pr_id = pr_id
        msg.addr = addr
        msg.fn = fn
        msg.size = size
        msg.payload = payload
        return msg

    def set_payload(self, data):
        self.payload = data

    def set_payload_w_size(self, data):
        self.payload = struct.pack('B') + data

    def to_bytes(self):
        res = struct.pack('>HHHBB', self.tr_id, self.pr_id, len(self.payload) + 2, self.addr, self.fn)
        res += self.payload
        return res
