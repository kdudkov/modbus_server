#!/usr/bin/env python

import logging
import time


logger = logging.getLogger(__name__)


def hex_data(data):
    return ' '.join((hex(x)[2:].rjust(2, '0') for x in data))


def to_le(n):
    return (n & 0xff00) >> 8, n & 0xff


class TcpMessage(object):
    def __init__(self):
        tr_id = 0
        pr_id = 0
        size = 6
        addr = 0
        payload = []

    @staticmethod
    def decode_tcp(s):
        if isinstance(s, str):
            data = [ord(x) for x in s]
        else:
            data = [x for x in s]
        if len(data) < 8:
            raise Exception('invalid tcp message size')
        tr_id = data[0] * 256 + data[1]
        pr_id = data[2] * 256 + data[3]
        size = data[4] * 256 + data[5]
        if len(data) != size + 6:
            logger.error('invalid size')
            return {}
        addr = data[6]
        fn = data[7]
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
        self.payload = [len(data), ]
        self.payload += data

    def to_list(self):
        res = []
        res += to_le(self.tr_id)
        res += to_le(self.pr_id)
        res += to_le(len(self.payload) + 2)
        res += [self.addr, self.fn]
        res += self.payload
        return res