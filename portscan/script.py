#!/usr/bin/python3
"""
Вводдится первым аргументом 1 IP, например 192.168.1.9 вторым диапазон портов, например, 65-138 (от 65 до 138)
"""
import sys
import socket
import os
from threading import Thread

THERE_IS_OPEN_PORTS = False

class Port:
	def __init__(self, port):
		self.port = port
		self.open_tcp = False
		self.open_udp = False

def check_port(ip, port):
	global THERE_IS_OPEN_PORTS
	try:
		con = socket.create_connection((ip, port.port), 5)
		port.open_tcp = True
		THERE_IS_OPEN_PORTS = True
		try:
			con.close()
		except:
			pass
	except:
		pass

def main():
	try:
		args = sys.argv[1:]
		ip = args[0]
		s_e = args[1].split("-")
		start = int(s_e[0])
		end = int(s_e[1])
		if start < 0 or start > 65535:
			start = 0
		if 65535 < end or end < 0:
			end = 65535
		tcp_ports = []
		threads = []
		for port in range(start, end+1):
			c_port = Port(port)
			tcp_ports.append(c_port)
			th = Thread(target=check_port, args=(ip, c_port))
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
	except:
		print("Проверьте правильность аргументов")

if __name__ == "__main__":
	main()

