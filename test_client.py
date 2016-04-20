#!/usr/bin/env python3

import time
import socket
from modbus_tcp import hex_data, TcpMessage

if __name__ == '__main__':
    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    conn.connect(("127.0.0.1", 55666))
    conn.settimeout(0)

    l = [0, 1, 0, 0, 0, 6, 1, 6, 0, 2, 0, 0]
    # l = [0, 1, 0, 0, 0, 6, 1, 3, 0, 0, 0, 2]
    conn.sendall(bytes(l))
    time.sleep(0.2)

    data = b''
    try:
        tmp = conn.recv(256)
        while tmp:
            data += tmp
            tmp = conn.recv(256)
    except:
        pass


    msg = TcpMessage.decode_tcp(data)
    print(msg.payload)

    conn.close()
