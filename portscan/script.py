#!/usr/bin/python3
import socket
from multiprocessing import Pool
from argparse import ArgumentParser
IP = ""
ICMP_SOCK = None

def get_args():
	parser = ArgumentParser(epilog="(c)Николаев Вадим КБ-201",
							description="Сканнер открытых ТСП портов",
							prog="python3 script.py 127.0.0.1 -s 1 -e 65535")
	parser.add_argument("ip", type=str, help="IP хоста для сканирования")
	parser.add_argument("-s", "--start", type=int, help="Порт начала сканирования (1)",
						default=1)
	parser.add_argument("-e", "--end", type=int, help="Порт конца сканирования (65535)",
						default=65535)
	return parser.parse_args()

def scan_tcp(port):
	try:
		sock = socket.create_connection((IP, port), 0.5)
		sock.close()
		return port
	except:
		return 0

def scan_udp(port):
	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	sock.settimeout(0.5)
	sock.sendto(b"HELLO!", (IP, port))
	try:
		data, addr = sock.recvfrom(512)
		return port
	except:
		return 0
	finally:
		sock.close()

def main():
	global IP, ICMP_SOCK
	access_denied = False
	try:
		ICMP_SOCK = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
	except PermissionError:
		access_denied = True
	args = get_args()
	IP = args.ip
	start = args.start
	end = args.end
	if start < 1 or start > 65535:
		start = 1
	if 65535 < end or end < 0:
		end = 65535
	pool = Pool(50)
	print("HOST:  "+IP)
	print("PORTS: "+str(start)+"-"+str(end))
	tcp_ports = list(filter(lambda x: x, pool.map(scan_tcp, range(start, end+1))))
	if not access_denied:
		udp_ports = list(filter(lambda x: x, pool.map(scan_udp, range(start, end+1))))
	else:
		udp_ports = []
	if tcp_ports:
		print("TCP PORTS:")
		for port in tcp_ports:
			print("    "+str(port))
	if udp_ports:
		print("UDP PORTS:")
		for port in udp_ports:
			print("    "+str(port))
	if not tcp_ports and not udp_ports:
		print("All ports are closed")
	if access_denied:
		print("Для сканирования UDP обратитесь к администратору")


if __name__ == "__main__":
	main()
