from modbus import RtuMessage, to_hex


def test_rtu():
    msg = [1, 6, 0, 1, 1, 0, 0xD9, 0x9a]
    r = RtuMessage.from_list(msg, False)
    print(r)
    print(to_hex(r.to_list()))
    assert r.to_list() == msg


if __name__ == '__main__':
    test_rtu()
