import socket
import keyboard
import time
import clientutils

from threading import Thread


class LiteNetClient:
    def __init__(self, ip, password, port=5050, header=64, encoding="utf-8", debug=False, encrypt=True):
        self.ip, self.port, self.password = ip, port, password

        self.header, self.encoding = header, encoding

        self._close_msg = "[CLOSE]"

        self._login_msg = "[LOGIN]"

        socket.setdefaulttimeout(5)

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

                if self.cipher:
                    msg = self.cipher.decrypt(msg)

                return msg.decode(self.encoding)

            else:
                return None

        except socket.timeout:
            return None

        except socket.error:
            print("Server has closed connection your with the server.")
            time.sleep(2)
            exit()

    def send(self, msg):
        msg = msg.encode(self.encoding)

        if self.cipher:
            msg = self.cipher.encrypt(msg)

        msg_length = len(msg)
        send_length = str(msg_length).encode(self.encoding) + b' ' * (self.header - len(str(msg_length).encode(self.encoding)))
        self.socket.send(send_length)
        self.socket.send(msg)
        if self.debug:
            print("[DEBUG] Message Sent")

    def _start(self, password):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.socket.connect((self.ip, self.port))
        print(f"Connected to {self.ip}:{self.port}")

        login_msg = str(self._login_msg + " " + password).encode(self.encoding)
        self.send(login_msg)

        if self.encrypt:
            self.cipher = clientutils.getcipher('key.txt')
        else:
            self.cipher = False

        while True:
            server_msg = self.get_server_msg()
            if server_msg:
                print(server_msg)

    def disconnect(self):
        self.send(self._close_msg)
        self.socket.close()
