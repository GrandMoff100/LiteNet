import socket
import keyboard
import time
import clientutils
import sys

from cryptography.fernet import Fernet, InvalidToken
from threading import Thread


class LiteNetClient:
    def __init__(self, ip, password, port=5050, header=64, encoding="utf-8", debug=False, encrypt=True):
        self.ip, self.port, self.password = ip, port, password

        self.header, self.encoding = header, encoding

        self._close_msg = "[CLOSE]"

        self._login_msg = "[LOGIN]"

        socket.setdefaulttimeout(0.5)

        keyboard.add_hotkey("t", self.message)

        self.debug = debug
        
        self.encrypt = encrypt

        self._temp = None

        self.cipher = False

    def start(self):
        Thread(target=self._start(self.password)).start()

    def message(self):
        message = input("std::You >> ")
        self.send(message)

    def get_server_msg(self):
        try:
            msg_length = self.socket.recv(self.header).decode(self.encoding)

            if msg_length:
                msg = self.socket.recv(int(msg_length))

                if self.cipher and self.encrypt:
                    try:
                        msg = self.cipher.decrypt(msg)
                    except InvalidToken:
                        pass
                
                if msg.decode('utf-8') == self._close_msg:
                    self.disconnect(False)
                return msg.decode(self.encoding)

            else:
                return None

        except socket.timeout:
            return None

        except socket.error:
            print("Server has closed connection your with the server.")
            time.sleep(2)
            sys.exit()
        

    def send(self, msg, encrypt=True):
        msg = msg.encode(self.encoding)

        if self.cipher and self.encrypt and encrypt:
            msg = self.cipher.encrypt(msg)

        msg_length = len(msg)
        send_length = str(msg_length).encode(self.encoding) + b' ' * (self.header - len(str(msg_length).encode(self.encoding)))
        self.socket.send(send_length)
        self.socket.send(msg)
        if self.debug:
            print("[DEBUG] Message Sent")

    def _start(self, password):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        started = False
        while not started:
            try:
                self.socket.connect((self.ip, self.port))
                started = True
            except OSError:
                print("IP still in use - Please wait")
                time.sleep(2)
        
        print(f"Connected to {self.ip}:{self.port}")

        login_msg = str(self._login_msg + " " + password)

        if self.encrypt:
            self.cipher = clientutils.getcipher('key.txt')
        else:
            self.cipher = False
        
        self.send(login_msg)

        while True:
            server_msg = self.get_server_msg()
            if server_msg:
                print(server_msg)
            if server_msg == "Login Failed":
                self.disconnect()
                sys.exit()
            self.message()

    def disconnect(self, send_close=True):
        if send_close:
            self.send(self._close_msg, False)
        self.socket.close()
