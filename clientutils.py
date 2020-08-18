from cryptography.fernet import Fernet


def getcipher(filename: str):
    with open(filename, 'r') as readfile:
        lines = readfile.readlines()
    key = lines[0].encode('utf-8')
    cipher = Fernet(key)
    return cipher