#!/usr/bin/python3
import sys
import socket
import os
from threading import Thread
from argparse import ArgumentParser

THERE_IS_OPEN_PORTS = False

class Port:
	def __init__(self, port):
		self.port = port
		self.open_tcp = False
		self.open_udp = False

def get_args():
	parser = ArgumentParser(epilog="(c)Николаев Вадим КБ-201",
							description="Сканнер открытых ТСП портов",
							prog="python3 script.py 127.0.0.1 -s 0 -e 65535")
	parser.add_argument("ip", type=str, help="IP хоста для сканирования")
	parser.add_argument("-s", "--start", type=int, help="Порт начала сканирования (0)",
						default=0)
	parser.add_argument("-e", "--end", type=int, help="Порт конца сканирования (65535)",
						default=65535)
	return parser.parse_args()

class Checker(Thread):
	def __init__(self, ip, ports):
		super().__init__()
		self.ports = ports
		self.ip = ip

	def run(self):
		global THERE_IS_OPEN_PORTS
		for port in self.ports:
			try:
				con = socket.create_connection((self.ip, port.port), 5)
				port.open_tcp = True
				THERE_IS_OPEN_PORTS = True
				con.close()
			except:
				pass


def main():
	args = get_args()
	ip = args.ip
	start = args.start
	end = args.end
	if start < 0 or start > 65535:
		start = 0
	if 65535 < end or end < 0:
		end = 65535
	threads = []
	tcp_ports = [Port(port) for port in range(start, end + 1)]
	for port in range(start, end+1, 20):
		th = Checker(ip, tcp_ports[port:port+20])
		threads.append(th)
		th.start()
	for thread in threads:
		thread.join()
	print("HOST: ", ip)
	print("PORTS: ", start, "-", end, sep="")
	if THERE_IS_OPEN_PORTS:
		print("TCP ports:")
		for port in tcp_ports:
			if port.open_tcp:
				print("   ", port.port)
	else:
		print("All ports are closed")

if __name__ == "__main__":
	main()

