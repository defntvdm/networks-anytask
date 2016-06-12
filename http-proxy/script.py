#!/usr/bin/python3

from socket import socket, AF_INET, SOCK_STREAM, timeout, \
				   create_connection
from argparse import ArgumentParser
from threading import Thread
import re
import gzip


class Proxy(Thread):
	def __init__(self, sock, addr):
		super().__init__()
		self.sock_client = sock

	def run(self):
		try:
			self.request_b = self.get_request()
			self.request_s = self.request_b.decode(errors="ignore")
			reg_host = re.compile("Host: .+\r\n")
			host = reg_host.findall(self.request_s)[0][6:-2]
			self.response_b = self.get_response(host)
			self.remove_pictures()
			self.send_result()
		finally:
			self.sock_client.close()

	def remove_pictures(self):
		pass

	def send_result(self):
		self.sock_client.send(self.response_b)

	def get_request(self):
		try:
			data = self.sock_client.recv(65536)
			self.sock_client.settimeout(0.2)
			request = b""
			while data:
				request += data
				data = self.sock_client.recv(65536)
		except timeout:
			pass
		return request

	def get_response(self, host):
		sock_site = create_connection((host, 80))
		sock_site.send(self.request_b)
		data = sock_site.recv(65536)
		sock_site.settimeout(0.2)
		response = b""
		try:
			while data:
				response += data
				data = sock_site.recv(65536)
		except timeout:
			pass
		return response

def parse_args():
	parser = ArgumentParser(epilog="(c)Николаев Вадим КБ-201",
							description="Прокси-сервер заменяющий "
							"картинки на слово PICTURE со ссылкой на "
							"картинку", prog="python3 script.py")
	parser.add_argument("-p", "--port", type=int, help="Порт, на который бинди"
						"м наш сервер по умолчанию 8080", default=8080)
	return parser.parse_args()


def main():
	args = parse_args()
	port = args.port
	server = socket(AF_INET, SOCK_STREAM)
	try:
		server.bind(("", port))
		server.listen()
		while True:
			sock, addr = server.accept()
			Proxy(sock, addr).start()
	finally:
		server.close()


if __name__ == '__main__':
	main()
