import re

import requests
import rsa
from Crypto.Cipher import PKCS1_v1_5
from Crypto.PublicKey import RSA
import base64
import time
import base64


def encrypt(text, pk):
    rsa_key = RSA.importKey(pk)
    cipher = PKCS1_v1_5.new(rsa_key)
    b64_cipher = base64.b64encode(cipher.encrypt(text.encode())).decode()
    return b64_cipher


def login():
    url = 'https://www.yiban.cn/login/doLoginAjax'
    account = '13750431422'
    password = '11142897403+zxb'
    pk, tk, captcha = login_keys()
    captcha = '' if captcha == '0' else do_captcha()

    data = {
        'account': account,
        'password': encrypt(password, pk),
        'captcha': captcha,
        'keysTime': tk
    }
    res = requests.post(url, data, cookies=cookies)
    if res.cookies:
        cookies.update(res.cookies.get_dict())
    print(res.json())


def do_captcha():
    print('需要输入验证码')
    captcha_url = 'https://www.yiban.cn/captcha/index?Thu%20Aug%2012%202021%2014:55:16%20GMT+0800%20(%E4%B8%AD%E5%9B%BD%E6%A0%87%E5%87%86%E6%97%B6%E9%97%B4)'
    res = requests.get(captcha_url)
    with open('captcha.jpg', 'rb') as f:
        f.write(res.content)
    return None


def login_keys():
    res = requests.get('https://www.yiban.cn/login')
    cookies.update(res.cookies.get_dict())
    res = re.findall(
        r"data-keys='(.*)\s' data-keys-time='(.*)'>[\s\S]+data-isCaptcha=\"(\d)\"",
        res.text, re.S)[0]
    pk, kt, captcha = res
    return pk, kt, captcha


if __name__ == '__main__':
    cookies = {}
    login()
    print(cookies)

# login()
