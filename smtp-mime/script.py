#!/usr/bin/python3

import socket
import argparse
import ssl
from os import getcwd, walk
import re
import base64

def get_args():
    parser = argparse.ArgumentParser(prog="smtp_mime", epilog="(с)Николаев Вадим",\
        description="Отправка картинок по адресу, серверу, порту и папке с картинками")
    parser.add_argument("email", type=str, help="email получателя")
    parser.add_argument("server", type=str, help="smtp или mx сервер")
    parser.add_argument("port", type=int, help="порт для сервера")
    parser.add_argument("--directory", "-d", type=str, help="папка с картиночками")
    parser.add_argument("--login", "-l", type=str, help="логин для авторизации")
    parser.add_argument("--password", "-p", type=str, help="пароль для авторизации")
    return parser.parse_args()

def to_base64(line):
    return base64.b64encode(line.encode()).decode()

def get_code_of_pictures(directory):
    re_images = re.compile('(jpeg|jpg|png|bmp|gif)')
    dict_images = dict()
    files = []
    for (dir_path, dir_names, file_names) in walk(directory):
        files.extend(file_names)
        break
    for file in files:
        if len(re_images.findall(file)) > 0:
            with open(directory+"/"+file, "rb") as normal_file:
                try:
                    encoded_string = base64.standard_b64encode(normal_file.read())
                    dict_images[file] = encoded_string.decode()
                except Exception as er:
                    print('\nSomething is wrong with file ' + str(file) + '\n')
                    continue
    return dict_images

class Sender:
    def __init__(self, email, server, port, directory, login=None, passwd=None):
        self.email = email
        self.server = server
        self.port = port
        if directory:
            self.directory = directory
        else:
            self.directory = getcwd()
        if login:
            self.login = login
        else:
            self.login = "floop1711@gmail.com"
        self.password = passwd

    def ehlo(self, sock):
        try:
            sock.send("EHLO sender.com\r\n".encode())
            data = sock.recv(4096).decode()
            if data[0] == "2":
                print("Приветствие прошло успешно")
            else:
                print("ehlo problems")
                print(data)
                sock.close()
                exit(0)
        except socket.timeout:
            print("Timeout ehlo")
            sock.close()
            exit(0)

    def mail(self, sock):
        try:
            sock.send(("MAIL FROM: <"+self.login+">\r\n").encode())
            data = sock.recv(4096).decode()
            if data[0] == "2":
                print("'От кого' указано")
            else:
                print("mail problems")
                print(data)
                sock.close()
                exit(0)
        except socket.timeout:
            print("Timeout mail")
            sock.close()
            exit(0)

    def rcpt(self, sock):
        try:
            sock.send(("RCPT TO: <"+self.email+">\r\n").encode())
            data = sock.recv(4096).decode()
            if data[0] == "2":
                print("'Кому' указано")
            else:
                print("rcpt problems")
                print(data)
                sock.close()
                exit(0)
        except socket.timeout:
            print("Timeout rcpt")
            sock.close()
            exit(0)

    def data(self, sock):
        try:
            sock.send("DATA\r\n".encode())
            data = sock.recv(4096).decode()
            if data[0] == "3":
                print("Отправка письма")
            else:
                print("data problems")
                print(data)
                sock.close()
                exit(0)
            sock.send(self.get_message())
        except socket.timeout:
            print("Timeout data")
            sock.close()
            exit(0)

    def end_data(self, sock):
        sock.settimeout(10)
        try:
            sock.send("\r\n.\r\n".encode())
            data = sock.recv(4096).decode()
            if data[0] == "2":
                print("Сообщение отправлено")
            else:
                print("Sending problems")
                print(data)
                sock.close()
                exit(0)
        except socket.timeout:
            print("Timeout end_data")
            sock.close()
            exit(0)

    def get_message(self):
        msg = []
        msg.append("From: "+self.login + " <" + self.login + ">\r\n")
        msg.append("To: "+self.email + " <" + self.email + ">\r\n")
        msg.append("Subject: pictures\r\n")
        msg.append('Content-Type: multipart/related; boundary="qUaDs74"\r\n\r\n')
        msg.append("--qUaDs74\r\n")
        msg.append("Content-Type: text/html; charset=utf-8\r\n\r\n")
        msg.append("<h5>Картиночки, которые надо было скинуть, но это не точно</h5>\r\n\r\n")
        file_base64 = get_code_of_pictures(self.directory)
        for file in file_base64.keys():
            print(file)
            msg.append("--qUaDs74\r\n")
            if file[-3:] == "jpg":
            	msg.append("Content-Type: image/jpg\r\n")
            elif file[-3:] == "png":
            	msg.append("Content-Type: image/png\r\n")
            elif file[-3:] == "bmp":
            	msg.append("Content-Type: image/bmp\r\n")
            elif file[-3:] == "gif":
            	msg.append("Content-Type: image/gif\r\n")
            else:
            	msg.append("Content-Type: image/jpeg\r\n")
            msg.append("Content-Transfer-Encoding: base64\r\n")
            msg.append('Content-Disposition: attachment; filename="' + file + '"\r\n\r\n')
            msg.append(file_base64[file])
            msg.append("\r\n\r\n")
        msg.append("--qUaDs74--")
        return "".join(msg).encode()

    def auth(self, sock):
        try:
            sock.send("AUTH LOGIN\r\n".encode())
            data = sock.recv(4096).decode()
            if data[0] == "3":
                print("Login")
            else:
                print("Auth problems")
                print(data)
                sock.close()
                exit(0)
            sock.send((to_base64(self.login)+"\r\n").encode())
            data = sock.recv(4096).decode()
            if data[0] == "3":
                print("Password")
            else:
                print("Auth problems")
                print(data)
                sock.close()
                exit(0)
            sock.send((to_base64(self.password)+"\r\n").encode())
            data = sock.recv(4096).decode()
            if data[0] == "2":
                print("Авторизация пройдена")
            else:
                print("Auth problems")
                print(data)
                sock.close()
                exit(0)
        except socket.timeout:
            print("Timeout AUTH")
            sock.close()
            exit(0)

    def quit(self, sock):
        try:
            sock.send("QUIT\r\n".encode())
            data = sock.recv(4096).decode()
            if data[0] == "2":
                print("Соединение закрыли")
            else:
                print("Quit problems")
                print(data)
                sock.close()
                exit(0)
        except socket.timeout:
            print("Timeout quit")
            sock.close()
            exit(0)

    def create_simple_connection(self):
        sock = socket.create_connection((self.server, self.port), 2)
        try:
            data = sock.recv(4096).decode()
            if data[0] == "2":
                print("Соединения установлено")
            else:
                print("connection problems")
                print(data)
                sock.close()
                exit(0)
            self.ehlo(sock)
            return sock
        except socket.timeout:
            print("Timeout create connection")
            sock.close()
            exit(0)

    def create_ssl_connection(self):
        sock = socket.create_connection((self.server, self.port), 2)
        try:
            data = sock.recv(4096).decode()
            if data[0] == "2":
                print("Соединение установлено")
            else:
                print("Connection problems")
                print(data)
                sock.close()
                exit(0)
            self.ehlo(sock)
            sock.send("STARTTLS\r\n".encode())
            data = sock.recv(4096).decode()
            if data[0] == "2":
                print("TLS установлено")
            else:
                print("Starttls problems")
            sock = ssl.wrap_socket(sock)
            self.ehlo(sock)
            self.auth(sock)
            return sock
        except socket.timeout:
            print("Timeout create connection")

    def send_message(self):
        if not self.password:
            sock = self.create_simple_connection()
        else:
            sock = self.create_ssl_connection()
        self.mail(sock)
        self.rcpt(sock)
        self.data(sock)
        self.end_data(sock)
        self.quit(sock)

def main():
    args = get_args()
    sender = Sender(args.email, args.server, args.port, args.directory, \
        args.login, args.password)
    sender.send_message()

if __name__ == "__main__":
    main()
