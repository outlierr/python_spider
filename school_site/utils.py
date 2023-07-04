import configparser
import os

# 读配置文件
CONFIG_PATH = os.getcwd() + '/conf/config.ini'
CONFIG = configparser.ConfigParser()
CONFIG.read(CONFIG_PATH)


def get_user():
    xh = CONFIG.get('User-1', 'username')  # 学号
    pwd = CONFIG.get('User-1', 'password')
    return xh, pwd


def set_user(username, password, cookies):
    if not username:
        CONFIG.set('User-1', 'username', cookies)
    if not password:
        CONFIG.set('User-1', 'password', cookies)
    if not cookies:
        CONFIG.set('User-1', 'cookies', cookies)
    CONFIG.write(open(CONFIG_PATH, 'w'))  # a追加


def encrypt(input):
    key_str = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/="
    output = ''
    c1 = c2 = None
    c3 = ''
    e1 = e2 = e3 = None
    e4 = ''
    i = 0
    length = len(input)
    while i < length:
        c1 = ord(input[i])
        i += 1
        c2 = 0 if i >= length else ord(input[i])
        i += 1
        c3 = 0 if i >= length else ord(input[i])
        i += 1
        e1 = c1 >> 2
        e2 = ((c1 & 3) << 4) | (c2 >> 4)
        e3 = ((c2 & 15) << 2) | (c3 >> 6)
        e4 = c3 & 63
        if not c2:
            e3 = e4 = 64
        elif not c3:
            e4 = 64
        output = output + key_str[e1] + key_str[e2] + key_str[e3] + key_str[e4]
        c1 = c2 = c3 = ''
        e1 = e2 = e3 = e4 = ''
    return output


if __name__ == '__main__':
    pass
