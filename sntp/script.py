#!/usr/bin/python3

import socket
from argparse import ArgumentParser
from threading import Thread
import struct
from datetime import datetime
from time import time


def get_args():
	parser = ArgumentParser(epilog="(с)Николаев Вадим КБ-201",
							description="SNTP сервер обманщик",
							prog="python3 script.py -s 100")
	parser.add_argument("-s", "--shift", type=int, default=0, 
		help="Число секунд, на которое сервер будет врать, по умолчанию 0")
	return parser.parse_args()


def current_time(shift):
	return int(time()) + 2208988800 + shift


class Client(Thread):
	def __init__(self, addr, packet, shift, sock):
		super().__init__()
		self.shift = shift
		self.addr = addr
		self.packet = packet
		self.sock = sock

	def run(self):
		li_vn_mode, stratum, poll, precision, root_delay, root_dispersion,\
		reference_identifier, reference_timestamp, originate_timestamp,\
		rec, transmit_timestamp = struct.unpack("!BBBBIIIQQQQ", self.packet)
		#2208988800-количество секунд между 01.01.1900 и 01.01.1970
		receive_timestamp = current_time(self.shift)
		li_vn_mode = 36
		if datetime.now().day == 30 and datetime.now().month == 6 or\
		datetime.now().day == 31 and datetime.new().month == 12:
			li_vn_mode += 64
		stratum = 1
		self.packet = struct.pack("!BBBBIIIQQQQ", li_vn_mode, stratum, 0, 0,
								  0, 0, 0, 0, transmit_timestamp,
								  receive_timestamp*2**32,
								  current_time(self.shift)*2**32)
		self.sock.sendto(self.packet, self.addr)


def main():
	shift = get_args().shift
	server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	try:
		server.bind(("", 123)) #SNTP на 123 порту, требует права администратора
		while True:
			data, addr = server.recvfrom(512)
			Client(addr, data, shift, server).start()
	except PermissionError:
		print("Доступ запрещён, обратитесь к администратору")
	except KeyboardInterrupt:
		print("\nУдачного дня!")
	finally:
		server.close()


if __name__ == '__main__':
	main()
