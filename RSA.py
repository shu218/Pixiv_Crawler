import rsa
import os
import json
import os.path as op
from binascii import b2a_hex, a2b_hex

class rsacrypt(object):
    def __init__(self, root):
        self.root = root
        # 密钥文件伪装用文件名
        self.private_disguise = "\\cache\\(342929)swd1b2c3_Illust_List_cache"
        self.public_disguise = "\\cache\\public_cache"
        # 读取密钥数据
        self.key_dict = self.load()
        #key_dict	{"public": "", "private": ""}
        # 如果未设定密钥则创建新的密钥
        if not (self.key_dict["public"] and self.key_dict["private"]):
            self.key_dict["public"], self.key_dict["private"] = rsa.newkeys(256) 
        #保存密钥数据
        self.save(self.key_dict)

    def encrypt(self, text):
        self.ciphertext = rsa.encrypt(text.encode(), self.key_dict["public"])
        # 因为rsa加密时候得到的字符串不一定是ascii字符集的，输出到终端或者保存时候可能存在问题
        # 所以这里统一把加密后的字符串转化为16进制字符串
        return b2a_hex(self.ciphertext)

    def decrypt(self, text):
        decrypt_text = rsa.decrypt(a2b_hex(text), self.key_dict["private"])
        return decrypt_text

    def load(self):
        if not (op.exists(self.root + self.private_disguise) and op.exists(self.root + self.public_disguise)):
            return {"public": "", "private": ""}
        # 从本地缓存文件读取公钥和私钥
        with open(self.root + self.private_disguise, "rb") as x:
            private_key = x.read()
            private_key = rsa.PrivateKey.load_pkcs1(private_key)      # load 私钥
        with open(self.root + self.public_disguise, "rb") as x:
            public_key = x.read()
            public_key = rsa.PublicKey.load_pkcs1(public_key)       # load 公钥
        return {"public": public_key, "private": private_key}

    def save(self, data):
        public_key = data["public"]
        private_key = data["private"]
        private_key = private_key.save_pkcs1()  # 保存为 .pem 格式
        with open(self.root + self.private_disguise, "wb") as x:  # 保存私钥
            x.write(private_key)
        public_key = public_key.save_pkcs1()  # 保存为 .pem 格式
        with open(self.root + self.public_disguise, "wb") as x:  # 保存公钥
            x.write(public_key)

class MyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, bytes):
            return str(obj, encoding='utf-8');
        return json.JSONEncoder.default(self, obj)

