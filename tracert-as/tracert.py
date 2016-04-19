#!/usr/bin/python3
"""The tracert utility realization."""
import sys
import re

from socket import socket, AF_INET, SOCK_RAW, IPPROTO_ICMP, \
    IPPROTO_IP, IP_HDRINCL, error, SOCK_DGRAM, create_connection, \
    timeout, gethostbyname
from struct import pack
from argparse import ArgumentParser


DEFAULT_TTL = 30
WHOIS_SERVER = "whois.iana.org"
WHOIS_PORT = 43
TIMEOUT = 5

# Compiled patterns for information about a diven IP-address getting.
REFER = re.compile(r"refer: (.*?)\n")
COUNTRY = re.compile(r"country: (.*?)\n")
NETNAME = re.compile(r"netname: (.*?)\n")
AUTONOMIC_SYSTEM = re.compile(r"origin: (.*?)\n")


def main():
    """
    ICMP-packages with different TTLs packing and
    sending and the answers receiving.
    """
    destinations, max_ttl = argument_parse()

    try:
        sock = socket(AF_INET, SOCK_RAW, IPPROTO_ICMP)
        sock.setsockopt(IPPROTO_IP, IP_HDRINCL, 1)
        sock.settimeout(TIMEOUT)
    except error:
        print("Permission denied")
        sys.exit(0)

    source = get_ip()
    print("Source IP-address: {}".format(source))
    print("Bound TTL: {}".format(max_ttl))
    print()

    try:
        for destination in destinations:
            address = gethostbyname(destination)# In number format.
            print("Route for {}".format(destination))
            hope = 1
            current_address = ""
            while hope <= max_ttl and current_address != address:
                buff = request_assembling(hope, source, address)
                sock.sendto(buff, (destination, 0))
                reply = sock.recvfrom(1024)
                current_address = reply[1][0]
                print("{}) {}".format(hope, current_address))
                country, netname, autonomic_system = get_info(current_address)
                if country is not None:
                    print("\tCountry: {}".format(country))
                if netname is not None:
                    print("\tNetname: {}".format(netname))
                if autonomic_system is not None:
                    print("\tAutonomic system: {}".format(autonomic_system))
                print()
                hope += 1
            print("Finished at {} hopes.".format(hope-1))
            print()
            print()
    except timeout:
        print("Timeout exceeded.")
    finally:
        print("Connection has been closed.")
        sock.close()


def argument_parse():
    """Argument parsing."""
    parser = ArgumentParser(prog="python3 tracert.py", \
        description="The route to each of set destinations tracing utility", \
        epilog="(c) Semyon Makhaev, 2016. All rights reserved.")
    parser.add_argument("destinations", type=str, nargs="*", \
        help="Destination IP-addresses")
    parser.add_argument("-t", "--ttl", type=int, default=DEFAULT_TTL, \
        help="The hops count. Default value is {}".format(DEFAULT_TTL))
    args = parser.parse_args()
    return args.destinations, args.ttl


def request_assembling(ttl, source, destination):
    """Request package assembling."""
    version_ihl = 4 << 4 | 5# A header length is 20 bytes.

    # Zero field for folowing fields: servise type, identification,
    # flags and offset, checksum (firstly for ICMP-header), options,
    # ICMP message code and ICMP checksum.
    zero_field = 0

    total_length = 60
    protocol_icmp = 1
    source = address_format(source)
    destination = address_format(destination)
    echo_icmp = 8

    ip_header = pack("!BBHLBBH", version_ihl, zero_field, total_length, \
            zero_field, ttl, protocol_icmp, zero_field) + source + destination
    icmp_header = pack("!BBHL", echo_icmp, zero_field, zero_field, zero_field)

    # Checksum inserting.
    icmp_checksum = checksum_calculate(icmp_header)
    icmp_header = pack("!BBHL", echo_icmp, zero_field, icmp_checksum, zero_field)

    return ip_header + icmp_header


def address_format(address):
    """Returns a packed IP-address."""
    addr = tuple(int(x) for x in address.split('.'))
    return pack("!BBBB", addr[0], addr[1], addr[2], addr[3])


def get_ip():
    """
    Request to the external host sending.
    Returns an external IP-address of a current host.
    """
    sock = socket(AF_INET, SOCK_DGRAM)
    try:
        # Any arbitrary existing host and port are suitable.
        sock.connect((WHOIS_SERVER, WHOIS_PORT))
        return sock.getsockname()[0]
    finally:
        sock.close()


def checksum_calculate(package):
    """Checksum calculation."""
    checksum = 0
    count_to = (len(package) / 2) * 2
    count = 0

    while count < count_to:
        value = package[count + 1] * 256 + package[count]
        checksum += value
        checksum &= 0xffffffff
        count += 2

    if count_to < len(package):
        checksum += package[len(package) - 1]
        checksum &= 0xffffffff

    checksum = (checksum >> 16) + (checksum & 0xffff)
    checksum += (checksum >> 16)
    result = ~checksum
    result &= 0xffff
    result = result >> 8 | (result << 8 & 0xff00)

    return result


def get_info(address):
    """
    Returns country, network name and an autonomic \
    system number of a given address."""
    reply = send_request(address, (WHOIS_SERVER, WHOIS_PORT))
    refer = re.search(REFER, reply)
    if refer is not None:
        refer = refer.groups()[0].replace(' ', '')
        reply = send_request(address, (refer, WHOIS_PORT))
    for pattern in COUNTRY, NETNAME, AUTONOMIC_SYSTEM:
        match = re.search(pattern, reply)
        if match is not None:
            yield match.groups()[0].replace(' ', '')
        else:
            yield None


def send_request(request, host_port):
    """Sends a request to host on a port, returns a reply."""
    sock = socket(AF_INET, SOCK_DGRAM)
    sock.settimeout(TIMEOUT)
    sock = create_connection(host_port, TIMEOUT)
    data = bytes()

    try:
        sock.sendall("{}\r\n".format(request).encode('utf-8'))
        while True:
            buff = sock.recv(4096)
            if not buff:
                return data.decode("utf-8")
            data += buff
    finally:
        sock.close()


if __name__ == "__main__":
    main()
