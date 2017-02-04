import struct

from modbus import RtuMessage, to_hex


def test_rtu():
    msg = struct.pack('BBBBBBBB', 1, 6, 0, 1, 1, 0, 0xd9, 0x9a)
    r = RtuMessage.from_bytes(msg, False)
    print(r)
    print(to_hex(r.to_bytes()))
    assert r.to_bytes() == msg


if __name__ == '__main__':
    test_rtu()
