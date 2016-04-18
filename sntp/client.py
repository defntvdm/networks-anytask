#!/usr/bin/python3

import socket
import struct
import time

IP = "127.0.0.1"
PORT = 4040


def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(4)
    try:
        fmt_pack = "!BBBBIIIQQQQ"
        li = 0
        vn = 2 << 3
        mode = 3
        stratum = 2
        pack = struct.pack(fmt_pack, li+vn+mode, stratum, 0, 0, 0, 0, 0, 0, 0, 0, 0)
        sock.sendto(pack, (IP, PORT))
        data, addr = sock.recvfrom(4096)
        fmt_unpack = "!BBBBIIIIIIIIIII"
        y,m,d,h,mi,s, *arg = time.localtime(struct.unpack(fmt_unpack, data)[-2]-2208988800)
        my_time = []
        for i in [h, mi, s]:
            if -1<i<10:
                my_time.append("0"+str(i))
            else:
                my_time.append(str(i))
        print("Время:", ":".join(my_time))
        my_date = []
        for i in [d, m, y]:
            if -1<i<10:
                my_date.append("0"+str(i))
            else:
                my_date.append(str(i))
        print("Дата :", ".".join(my_date))
    except(socket.timeout):
        print("Проблемы с соединениями")
    finally:
        sock.close()

if __name__ == '__main__':
    main()