import json

from cryptography.fernet import Fernet


def to_liteaddr(ip):
    ip = ip[0].split(".")
    return "Lite|" + "_".join([int_to_lite_num(int(n)) for n in ip])


def int_to_lite_num(number):
    row = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"

    base = len(row)

    lite_num = [(number - (number % base)) / base, number % base]

    return "".join([list(row)[int(digit) - 1] for digit in lite_num])


def valid_login(liteaddr: str, password: str, users_json: str):
    with open(users_json, 'r') as readfile:
        users = json.load(readfile)
    if (liteaddr in list(users.keys())) and (users[liteaddr] == password):
        return True
    else:
        return False


def get_addr_cipher(liteaddr: str, key_file: str):
    with open(key_file, 'r') as readfile:
        keys = json.load(readfile)
    if not liteaddr in keys:
        return False
    addr_key = keys[liteaddr]
    addr_cipher = Fernet(addr_key.encode('utf-8'))
    return addr_cipher