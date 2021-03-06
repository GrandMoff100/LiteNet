import socket
import threading
import time
import sys

from cryptography.fernet import Fernet, InvalidToken
from utils import to_liteaddr, get_addr_cipher, valid_login


class LiteNetServer:
    def __init__(self, ip, port=5050, header=64, encoding="utf-8", debug=False, encrypt=True):
        self.ip, self.port = ip, port

        self.header, self.encoding = header, encoding

        self._close_msg = "[CLOSE]"

        self._login_msg = "[LOGIN]"

        self.clients = {}

        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.debug = debug

        self.encrypt = encrypt

        self._stopped = False

    def start(self):
        try:
            threading.Thread(target=self._start).start()
        except KeyboardInterrupt:
            self.stop()
            sys.exit()

    def _start(self):
        started = False
        while not started:
            try:
                self.server.bind((self.ip, self.port))
                started = True
            except OSError:
                print("IP still in use - Please wait")
                time.sleep(4)

        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.listen()

        print(f"LiteNet Server Listening on {self.ip}:{self.port}")

        while not self._stopped:
            conn, addr = self.server.accept()
            thread = threading.Thread(target=self.handle_client, args=(conn, addr))
            thread.start()
            print(f"[NEW CONNECTION] {addr}")

            if self.debug:
                print("Active Clients:", self.active_client_count)
                print(self.clients, "\n")

        self.server.close()

    def handle_client(self, conn, addr):
        self.clients[addr] = {
            "alias": to_liteaddr(addr),
            "connection": conn,
            "alive": True,
            "verified": False
        }

        while self.clients[addr]["alive"]:
            try:
                msg_length = self.clients[addr]["connection"].recv(self.header)
            except OSError:
                print(f"One connection has been closed by {addr[0]}:{addr[1]}")
                input("Press enter to continue")
                break

            if msg_length:
                try:
                    msg_length = int(msg_length.decode(self.encoding))
                except ValueError:
                    continue

                msg = self.clients[addr]["connection"].recv(msg_length)

                if self.debug:
                    print('Incoming message:', msg)

                if self.encrypt:
                    user_addr = to_liteaddr(addr) 
                    cipher = get_addr_cipher(user_addr, 'client_keys.json')
                    if cipher:
                        try:
                            msg = cipher.decrypt(msg)
                        except InvalidToken:
                            pass
                msg = msg.decode(self.encoding)

                if msg[0:len(self._login_msg)] == self._login_msg:
                    alias = self.clients[addr]['alias']
                    password = ' '.join(msg.split()[1:])
                    if valid_login(alias, password, 'users.json'):
                        self.clients[addr]['verified'] = True
                        continue


                if msg == self._close_msg:
                    break

                if self.clients[addr]['verified']:
                    print(addr[0] + ":" + str(addr[1]), ">>", msg)

                    msg = str(f"{to_liteaddr(addr[0:1]) + ':' + str(addr[2:3])} >> {msg}")

                    for client in self.clients.keys():
                        if client == addr:
                            if self.clients[client]["alive"] and self.clients[client]["verified"]:
                                if self.debug:
                                    print("Msg Len:", len(msg.encode(self.encoding)))
                                
                                if self.encrypt:
                                    user_addr = to_liteaddr(addr)
                                    cipher = get_addr_cipher(user_addr, 'client_keys.json')
                                    if cipher:
                                        msg = cipher.encrypt(msg.encode(self.encoding))
                                    else:
                                        msg = msg.encode(self.encoding)
                            
                                sending = str(len(msg)).encode(self.encoding) + b" " * (self.header - len(msg))

                                self.clients.get(client)["connection"].send(sending)

                                time.sleep(.3)

                                self.clients.get(client)["connection"].send(
                                    msg.encode(self.encoding)
                                )
                            else:
                                print(addr, "is disconnected.")
                else:
                    try:
                        conn.send(b'12')
                        time.sleep(0.3)
                        conn.send(b"Login Failed")
                    except (BrokenPipeError, ConnectionResetError):
                        if self.debug:
                            print(f"Failed Login by {to_liteaddr(addr)}")

        conn.close()
        self.close_client(addr)

    def close_client(self, addr):
        if addr in self.clients:
            self.clients[addr]["alive"] = False
            self.clients[addr]["verified"] = False
        else:
            raise socket.error(f"{addr} isn't connected to the server.")

    @property
    def active_client_count(self):
        return threading.activeCount() - 2

    def stop(self):
        for client in self.clients:
            if client['alive']:
                client['connection'].send(self._close_msg)
        self._stopped = True
