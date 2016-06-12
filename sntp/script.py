#!/usr/bin/python3
import socket
import struct
import sys

IP = "pool.ntp.org"
PORT = 123


def  main():
    try:
        lie = int(sys.argv[1])
    except:
        lie = 0
    print(lie)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.bind(("", 4040))
        while True:
            data, addr = sock.recvfrom(4096)
            sock.sendto(data, (IP, PORT))
            data, _ = sock.recvfrom(4096)
            fmt = "!BBBBIIIIIIIIIII"
            data = list(struct.unpack(fmt, data))
            data[-2] = data[-2]+lie
            data = struct.pack(fmt, *data)
            sock.sendto(data, addr)
    except:
        print("Закрылись")
    finally:
        sock.close()

if __name__ == '__main__':
    main()