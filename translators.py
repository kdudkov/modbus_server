import logging
from modbus_tcp import TcpMessage

log = logging.getLogger(__name__)


class SimpleChiniseBoard(object):

    def __init__(self, addr):
        self.addr = addr
        self.regs = [0, 0, 0]

    def translate(self, msg):
        if not isinstance(msg, TcpMessage):
            raise Exception('not a mesage')
        if msg.fn == 3:
            assert len(msg.payload) == 4, 'invalid payload size for fn 3: %s' % len(msg.payload)
            reg_addr = msg.payload[0] * 256 + msg.payload[1]
            reg_size = msg.payload[2] * 256 + msg.payload[3]
            log.debug('got fn 3, addr %s num %s', reg_addr, reg_size)
            if reg_addr in [1, 2] and reg_size == 1:
                ans = [0, self.regs[reg_addr - 1]]
                msg.set_payload_w_size(ans)
                return {'send': False, 'msg': msg}
            if reg_addr == 1 and reg_size == 2:
                ans = [0, self.regs[0], 0, self.regs[1]]
                log.debug('ans: %s', ans)
                msg.set_payload_w_size(ans)
                return {'send': False, 'msg': msg}

        if msg.fn == 6:
            assert len(msg.payload) == 4, 'invalid payload size for fn 6: %s' % len(msg.payload)
            reg_addr = msg.payload[0] * 256 + msg.payload[1]
            val = msg.payload[2] * 256 + msg.payload[3]
            log.debug('got fn 6, addr %s val %s', reg_addr, val)
            if reg_addr in [1, 2] and val in [0, 1]:
                   self.regs[reg_addr - 1] = val
                   msg.payload[2] = [2, 1][val]
                   msg.payload[3] = 0
            return {'send': True, 'msg': msg}
        raise Exception('fn %s is not implemented' % msg.fn)
