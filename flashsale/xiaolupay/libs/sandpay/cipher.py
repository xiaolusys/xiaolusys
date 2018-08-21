# coding: utf8
from __future__ import absolute_import, unicode_literals

import base64
import hashlib

import rsa
from Crypto import Random
from Crypto.Cipher import AES
import six

BS = AES.block_size
pad = lambda s: s + (BS - len(s) % BS) * chr(BS - len(s) % BS)
unpad = lambda s : s[0:-ord(s[-1])]

def read_file(file_path):
    with open(file_path, "r") as f:
        return f.read()

class AESCipher(object):
    """ RSA / ECB/ PKCS5Padding """

    @staticmethod
    def ecb_encrypt(raw, aes_ecb_key):
        cipher = AES.new(aes_ecb_key)
        return base64.b64encode(cipher.encrypt(pad(raw)))

    @staticmethod
    def ecb_decrypt(enc, aes_ecb_key):
        cipher = AES.new(aes_ecb_key)
        return cipher.decrypt(base64.b64decode(enc))


class RSACipher(object):
    """ RSA / ECB/ PKCS1Padding """
    @staticmethod
    def encrypt(message, publickey_file):
        rsa_public_key = rsa.PublicKey.load_pkcs1(read_file(publickey_file))
        message = message.encode('utf8')
        crypto = base64.b64encode(rsa.encrypt(message, rsa_public_key))
        return crypto

    @staticmethod
    def decrypt(encoded_encrypted_message, privatekey_file):
        encrypted_message = base64.b64decode(encoded_encrypted_message)
        rsa_private_key = rsa.PrivateKey.load_pkcs1(read_file(privatekey_file))
        decrypted_message = rsa.decrypt(encrypted_message, rsa_private_key)
        return six.text_type(decrypted_message, encoding='utf8')

    @staticmethod
    def sign(message, privatekey_file, hash):
        rsa_privatekey = rsa.PrivateKey.load_pkcs1(read_file(privatekey_file))
        return base64.b64encode(rsa.sign(message, rsa_privatekey, hash))


