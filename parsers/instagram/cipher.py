import binascii

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad


class Cipher:
    def __init__(self, encryption_key: str):
        self._encryption_key = encryption_key

    def encrypt(self, data: str) -> str:
        key = self._encryption_key.encode('utf-8')
        data_bytes = data.encode('utf-8')

        cipher = AES.new(key, AES.MODE_ECB)
        padded_data = pad(data_bytes, AES.block_size)
        encrypted = cipher.encrypt(padded_data)

        return binascii.hexlify(encrypted).decode('utf-8')
