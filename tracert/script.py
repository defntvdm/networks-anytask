#!/usr/bin/python3

from argparse import ArgumentParser
import socket
import struct
import time
import sys
import re
import select


def get_args():
	parser = ArgumentParser(epilog="(c)Николаев Вадим КБ-201",
		description="Аналог tracerout",
		prog="python3 script.py vk.com")
	parser.add_argument("hosts", nargs="+", help="До кого делаем трассировку")
	parser.add_argument("-n", help="Число хопов, по умолчанию 30", type=int,
		default=30)
	return parser.parse_args()

def request(sock):
    res = b''
    while select.select([sock], [], [], 0.25)[0]:
        data = sock.recv(4096)
        if len(data) == 0:
            break
        res += data
    return res

def information(ip, whois='whois.iana.org', pattern=[b'REFER', ]):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.settimeout(1)
            sock.connect((whois, 43))
            sock.setblocking(0)
            request(sock)
            sock.sendall((ip + "\r\n").encode())
            data = request(sock)
        except:
            data = ''
        res = []
        if data:
            for i in pattern:
                d = re.search(i + b':(.*)', data.upper())
                if d:
                    res.append(d.group(1).decode().lstrip())
                else:
                    res.append('')
        else:
            for i in pattern:
                res.append('')
    return res


def find(ip):
    if re.match(r'10\.(.*)', ip) or re.match(r'192\.168\.(.*)', ip):
        return False
    elif re.match(r'172\.(.*?)\.(.*)', ip):
        num = int(re.search(r'172\.(.*?)\.(.*)').group(1))
        if 16 <= num <= 31:
            return False
        else:
            return True
    else:
        return True

def hostname(ip):
    try:
        name = socket.gethostbyaddr(ip)
        name = '%s\n\t\t\t\t%s' % (name[0], name[2][0])
        return name
    except:
        return ip

def trace(host, hops):
	host_ip = socket.gethostbyname(host)
	print("\nТрассировка до %s (%s)\nС числом хопов %s\n\n" % 
		(host.upper(), host_ip, hops))
	ttl = 1
	while True:
		trace_sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
		trace_sock.settimeout(1)
		trace_sock.setsockopt(socket.SOL_IP, socket.IP_TTL, ttl)
		data = struct.pack('BBHHH', 8, 0, (8 + 256 * (ttl + 1))^0xFFFF, 256, 256 * ttl)
		for _ in range(64):
			data += struct.pack("b", 0)
		start_time = time.time()
		trace_sock.sendto(data, (host, 10000 + ttl))
		try:
			data = trace_sock.recvfrom(1024)
			ping = str(round((time.time() - start_time)*1000))
			ip = data[1][0]
			if find(ip):
				addr = hostname(ip)
				whois = information(ip)[0]
				info = information(ip, whois, [b'COUNTRY', b'ORIGIN', b'NETNAME'])
			else:
				addr = ip
				info = ['  ', 'LOCAL', '']
			if info[2]:
				addr = info[2] + ':\n' + 4*'\t' + addr
			print('%s   %s ms\t%s\t%s\t%s' % 
				(str(ttl).rjust(3), ping, info[0], info[1], addr))
			if ip == host_ip:
				break
		except socket.timeout:
			print('%s     *\t*\t*\t%s'% (str(ttl).rjust(3), 'Превышен интервал ожидания для запроса'))
		except Exception as e:
			print(e)
		finally:
			trace_sock.close()
		if ttl >= hops:
			sys.exit('\n%s недостижим'% (host))
		ttl += 1
		

def main():
	args = get_args()
	hops = args.n
	hosts = args.hosts
	for host in hosts:
		try:
			trace(host, hops)
		except PermissionError:
			print("Нужны права администратора")
		except KeyboardInterrupt:
			print("Досвидания :-)")

if __name__ == '__main__':
	main()
