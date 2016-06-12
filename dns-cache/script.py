#!/usr/bin/python3
import socket
import threading
import argparse
import time
import sys
import struct

HOST = "127.0.0.1"
PORT = 53
CACHE = dict()

def get_args():
    parser = argparse.ArgumentParser(
            prog="dns-cache",
            description="Кэширующий DNS сервер",
            epilog="(c)Николаев Вадим"
            )
    parser.add_argument("server", type=str, help="Адрес DNS сервера")
    parser.add_argument("--port", "-p", type=int, help="Порт сервера, поумолчанию 53", default=53)
    return parser.parse_args()


class DNS_Packet():
    def __init__(self, data):
        self.data = data
        self.HEADER = None
        self.name = None
        self.len_name = None
        self.QTYPE = None
        self.QCLASS = None
        self.ATYPE = None
        self.ACLASS = None

    def get_header(self):
        self.HEADER = struct.unpack("!HHHHHH", self.data[0:12])

    def set_id(self, ID):
        reply_ID = struct.pack("!H", ID)
        self.data = reply_ID + self.data[2:]

    def get_name(self):
        name_length = 0
        for i in self.data[12:]:
            name_length += 1
            if i == 0 or i == struct.pack("B", 0):
                break
        name = self.data[12:12 + name_length]
        self.len_name = name_length
        self.name = struct.unpack(str(self.len_name) + "s", name)

    def get_ttl(self, begin, end):
        return struct.unpack("!I", self.data[begin:end])[0]

    def set_ttl(self, cache_time, cache_ttl):
        begin = 12 + self.len_name + 4 + 10
        end = 12 + self.len_name + 4 + 12
        for ans in range(self.HEADER[3]):
            RD_len = struct.unpack("!H", self.data[begin:end])[0]
            new_ttl = struct.pack("!I", int(cache_ttl - time.time() + cache_time))
            self.data = self.data[0:begin - 4] + new_ttl + self.data[end - 2:]
            begin += RD_len + 12
            end += RD_len + 12

    def parse_packet(self):
        self.get_header()
        self.get_name()


class DNS_Server(threading.Thread):

    def __init__(self, data, client, server, port, sock):
        threading.Thread.__init__(self)
        self.daemon = True
        self.data = data
        self.client = client
        self.server = server
        self.port = port
        self.sock = sock

    def ask_server(self, key):
        print("\nResponse from SERVER\nFor: ", end="")
        forwarder_s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        forwarder_s.settimeout(0.1)
        try:
            forwarder_s.sendto(self.data, (self.server, self.port))
            response = forwarder_s.recv(4096)
            response_packet = DNS_Packet(response)
            response_packet.parse_packet()
            print(response_packet.name[0])
            self.sock.sendto(response_packet.data, self.client)
            begin = 12 + response_packet.len_name + 4 + 6
            end = 12 + response_packet.len_name + 4 + 10
            CACHE[key] = [response_packet, time.time(), response_packet.get_ttl(begin, end)]
        except socket.error:
            print("Wait... smth wrong")

    def run(self):
        request = DNS_Packet(self.data)
        request.parse_packet()
        key = request.data[2:]
        if key in CACHE:
            cache_data = CACHE[key][0].data
            cache_time = CACHE[key][1]
            cache_ttl = CACHE[key][2]
            if time.time() - cache_time <= cache_ttl:
                print("\nResponse from CACHE\nFor: ", end="")
                reply_packet = DNS_Packet(cache_data)
                reply_packet.parse_packet()
                print(reply_packet.name[0])
                reply_packet.set_id(request.HEADER[0])
                reply_packet.set_ttl(cache_time, cache_ttl)
                self.sock.sendto(reply_packet.data, self.client)
            else:
                self.ask_server(key)
        else:
            self.ask_server(key)


def main():
    udp_server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        args = get_args()
        server = args.server
        port = args.port
        if server == "127.0.0.1" and port == PORT:
            server = "8.8.8.8"
            port = 53
        udp_server.bind((HOST, PORT))
        while True:
            data, addr = udp_server.recvfrom(4096)
            DNS_Server(data, addr, server, port, udp_server).start()
    except Exception as ex:
        udp_server.close()
        print(ex)
        sys.exit(0)

if __name__ == "__main__":
    main()
