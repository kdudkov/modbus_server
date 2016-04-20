#!/usr/bin/env python3

import time
import socketserver
import logging

import modbus_tcp
import modbus
import settings

logger = logging.getLogger(__name__)


class SimpleTCPHandler(socketserver.BaseRequestHandler):

    def get_next(self):
        if len(self.data) < 6:
            return
        size = self.data[4] * 256 + self.data[5]
        if len(self.data) >= size + 6:
            msg = self.data[:size + 6]
            self.data = self.data[size + 6:]
            return msg
    
    def handle(self):
        self.data = []
        # self.request.settimeout(0)

        buf = self.request.recv(256)
        while buf:
            self.data += list(buf)
            self.get_messages()
            buf = self.request.recv(256)
        self.request.close()

    def get_messages(self):
        while 1:
            msg = self.get_next()
            if not msg:
                return
            try:
                res = self.process_data(list(msg))
                if res:
                    if isinstance(res, modbus_tcp.TcpMessage):
                        logger.debug('sending back %s', modbus_tcp.hex_data(res.to_list()))
                        self.request.sendall(bytes(res.to_list()))
                    else:
                        logger.debug('sending back %s', modbus_tcp.hex_data(res))
                        self.request.sendall(bytes(res))
                    time.sleep(0.1)
            except:
                logger.exception('')

    def process_data(self, d):
        logger.debug('got data %s', modbus_tcp.hex_data(d))
        msg = modbus_tcp.TcpMessage.decode_tcp(d)

        for translator in settings.translators:
            if translator.addr == msg.addr:
                res = translator.translate(msg)
                if not res['send']:
                    return res['msg']
                else:
                    msg = res['msg']
                    break

        data = msg.payload
        logger.debug('payload: %s', data)

        if msg.fn == 1:
            # read coils (1bit, r/w)
            if len(data) != 4:
                logger.error('bad payload size')
                return
            first = data[0] * 256 + data[1]
            size = data[2] * 256 + data[3]
            logger.info('cmd 1 to %s: %s coils from %s' % (msg.addr, size, first))
            n_ans = int((size + 7) / 8)
            res = self.server.modbus_device.read_coils(msg.addr, first, size)
            msg.set_payload_w_size(res)
            return msg

        if msg.fn == 2:
            # read discrete inputs (1 bit, ro)
            if len(data) != 4:
                logger.error('bad payload size')
                return
            first = data[0] * 256 + data[1]
            size = data[2] * 256 + data[3]
            logger.info('cmd 2 to %s: %s coils from %s' % (msg.addr, size, first))
            n_ans = int((size + 7) / 8)
            res = self.server.modbus_device.read_inputs(msg.addr, first, size)
            msg.set_payload_w_size(res)
            return msg

        if msg.fn == 3:
            # read holding regs (2byte, rw)
            if len(data) != 4:
                logger.error('bad payload size')
                return
            first = data[0] * 256 + data[1]
            size = data[2] * 256 + data[3]
            logger.info('cmd 3 to %s: %s regs from %s' % (msg.addr, size, first))
            res = self.server.modbus_device.read_reg(msg.addr, first, size)
            logger.debug('answer: %s', res)
            msg.set_payload_w_size(res)
            return msg

        if msg.fn == 4:
            # read input regs (2 byte, ro)
            if len(data) != 4:
                logger.error('bad payload size')
                return
            first = data[0] * 256 + data[1]
            size = data[2] * 256 + data[3]
            logger.info('cmd 4 to %s: %s regs from %s' % (msg.addr, size, first))
            res = self.server.modbus_device.read_input_analog(msg.addr, first, size)
            msg.set_payload(res)
            return msg

        if msg.fn == 5:
            # write coil
            reg_addr = data[0] * 256 + data[1]
            val = data[2] * 256 + data[3]
            res = self.server.modbus_device.write_coil(msg.addr, reg_addr, val)
            msg.set_payload(res)
            return msg

        if msg.fn == 6:
            # write reg
            reg_addr = data[0] * 256 + data[1]
            val = data[2] * 256 + data[3]
            logger.info('cmd 6 to %s: write %s to reg %s' % (msg.addr, val, reg_addr))
            res = self.server.modbus_device.write_reg(msg.addr, reg_addr, val)
            msg.set_payload(res)
            return msg


class SimpleServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, server_address, RequestHandlerClass):
        logger.info('starting server')
        self.modbus_device = modbus.ModbusDevice(settings.modbus_serial_port)
        socketserver.TCPServer.__init__(self, server_address, RequestHandlerClass)


if __name__ == '__main__':
    logging.basicConfig(level='INFO')
    PORT = 55666

    server = SimpleServer(('', PORT), SimpleTCPHandler)
    server.serve_forever()
