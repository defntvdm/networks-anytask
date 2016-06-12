#!/usr/bin/python3

import argparse
import socket
import ssl
import re
import base64
import os, sys


def get_args():
    parser = argparse.ArgumentParser(epilog="(с) Николаев Вадим",
                                     description="Показывает письма почты "
                                     "по логину паролю и серверу",
                                     prog="pop3")
    parser.add_argument("server", type=str, help="Сервер для получения почты")
    parser.add_argument("login", type=str, help="Логин для авторизации")
    parser.add_argument("password", type=str, help="Пароль для авторизации")
    parser.add_argument("--port", "-p",
                        type=int,
                        default=995,
                        help="Порт сервера, по умолчанию 995")
    parser.add_argument("--range", "-r", type=str,
                        help="Диапазон писем в виде 1-30,"
                        " то есть с первого по тридцатое")
    return parser.parse_args()


def decode_header(line):
    if line[0] != "=":
        return line
    else:
        return base64.b64decode(line[10:-2]).decode()


def parse_message(num, message, amount):
    reg_from = re.compile(r'From: [\S]*[\s]*<[\S]*>')
    lst_from = reg_from.findall(message)[0].split()[1:]
    try:
        from_name, from_email = lst_from
    except ValueError:
        from_name = ""
        from_email = lst_from[0]
    reg_to = re.compile(r'To: [\S]* <[\S]*>')
    lst_to = reg_to.findall(message)[0].split()[1:]
    try:
        to_name, to_email = lst_to
    except ValueError:
        to_name = ""
        to_email = lst_to[0]
    reg_subject = re.compile(r'Subject: [\S]*')
    subject = reg_subject.findall(message)[0][9:]
    reg_date = re.compile(r"Date:[\s]*[\S]*[\s]*[\S]*[\s]*[\S]*[\s]*[\S]*[\s]*[\S]*")
    try:
        date = " ".join(reg_date.findall(message)[0].split()[2:])
    except IndexError:
        date = ""
    reg_filename = re.compile(r"filename=[\S]+")
    files = reg_filename.findall(message)
    from_name = decode_header(from_name)
    to_name = decode_header(to_name)
    from_email = decode_header(from_email)
    to_email = decode_header(to_email)
    subject = decode_header(subject)
    print("ПИСЬМО №", num, sep="")
    print("  От кого:", from_name, from_email)
    print("  Кому: ", to_name, to_email)
    print("  Тема:", subject)
    if date:
        print("  Дата:", date)
    print("  Размер:", amount)
    if files:
    	print("  Вложений:", len(files))
    	print("  Имена вложений:")
    	for file in files:
    		print("   ", file[9:])


class Mail:
    def __init__(self, server, port, login, password, start, end):
        self.server = server
        self.port = port
        self.login = login
        self.password = password
        self.start = start
        self.end = end

    def connect(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ssl_sock = ssl.wrap_socket(sock)
        self.ssl_sock.settimeout(2)
        try:
            self.ssl_sock.connect((self.server, self.port))
            data = self.ssl_sock.recv(4096).decode()
            if data[:3] == "+OK":
                print("Connection created")
            else:
                print("Connection problems")
                print(data)
                self.ssl_sock.close()
                exit(0)
        except socket.timeout:
            print("Connection timeout")
            self.ssl_sock.close()
            exit(0)

    def auth(self):
        login = "USER " + self.login + "\r\n"
        password = "PASS " + self.password + "\r\n"
        try:
            self.ssl_sock.send(login.encode())
            data = self.ssl_sock.recv(4096).decode()
            if data[:3] == "+OK":
                print("USER accepted")
            else:
                print("USER problems")
                print(data)
                self.ssl_sock.close()
                exit(0)
            self.ssl_sock.send(password.encode())
            data = self.ssl_sock.recv(4096).decode()
            if data[:3] == "+OK":
                print("PASS accepted")
            else:
                print("PASS problems")
                print(data)
                self.ssl_sock.close()
                exit(0)
        except socket.timeout:
            print("AUTH timeout")
            self.ssl_sock.close()
            exit(0)

    def stat(self):
        try:
            self.ssl_sock.send("STAT\r\n".encode())
            data = self.ssl_sock.recv(4096).decode()
            num = int(data.split()[1])
            if self.start > num:
                print("Нет запрошенного количества писем, их всего", num)
                self.ssl_sock.close()
                exit(0)
            if num < self.end:
                self.end = num
            if data[:3] == "+OK":
                print("STAT ok")
            else:
                print("STAT problems")
                self.sock.close()
                exit(0)
        except socket.timeout:
            print("STAT timeout")
            self.ssl_sock.close()
            exit(0)

    def get_messages(self):
        if sys.platform == "win32":
            os.system("cls")
        else:
            os.system("clear")
        retr = "RETR {}\r\n"
        try:
            for i in range(self.start, self.end+1):
                self.ssl_sock.send(retr.format(str(i)).encode())
                data = self.ssl_sock.recv(4096).decode()
                amount = int(data.split()[1])
                message = ""
                while data:
                    try:
                        message += data
                        data = self.ssl_sock.recv(4096).decode()
                    except socket.timeout:
                        break
                parse_message(i, message, amount)
        except socket.timeout:
            print("GET MESSAGES problems")
            self.ssl_sock.close()
            exit(0)

    def quit(self):
        try:
            self.ssl_sock.send("QUIT\r\n")
            print("QUIT")
            print(self.ssl_sock.recv(4096).decode())
        except:
            self.ssl_sock.close()
            exit(0)

    def get_mail(self):
        self.connect()
        self.auth()
        self.stat()
        self.get_messages()
        self.quit()


def main():
    args = get_args()
    server = args.server
    login = args.login
    password = args.password
    port = args.port
    ran = args.range
    if ran:
        ran = ran.split("-")
        start = int(ran[0])
        end = int(ran[1])
    else:
        start = 1
        end = 10
    mail = Mail(server, port, login, password, start, end)
    mail.get_mail()

if __name__ == '__main__':
    main()
