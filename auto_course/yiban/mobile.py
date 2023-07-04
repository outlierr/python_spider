import configparser
import base64
import random
import os
import requests
from Crypto.Cipher import PKCS1_v1_5
from Crypto.PublicKey import RSA
from entry import *

BASE_URL = 'https://m.yiban.cn/api/v4'
CONFIG_PATH = os.getcwd() + '/config.ini'
CONFIG = configparser.ConfigParser()
CONFIG.read(CONFIG_PATH)


def multiple_choice(index, option, cur, opts):
    if cur.__len__() > 1:
        # list生成一个数组
        opts.append(list(cur))

    while index < len(option):
        cur.append(option[index])
        multiple_choice(index + 1, option, cur, opts)
        cur.pop()
        index += 1


def encrypt(text):
    public_key = '''-----BEGIN PUBLIC KEY-----
        MIICIjANBgkqhkiG9w0BAQEFAAOCAg8AMIICCgKCAgEA6aTDM8BhCS8O0wlx2KzAAjffez4G4A/Q
        Snn1ZDuvLRbKBHm0vVBtBhD03QUnnHXvqigsOOwr4onUeNljegICXC9h5exLFidQVB58MBjItMA8
        1YVlZKBY9zth1neHeRTWlFTCx+WasvbS0HuYpF8+KPl7LJPjtI4XAAOLBntQGnPwCX2Ff/LgwqkZ
        bOrHHkN444iLmViCXxNUDUMUR9bPA9/I5kwfyZ/mM5m8+IPhSXZ0f2uw1WLov1P4aeKkaaKCf5eL
        3n7/2vgq7kw2qSmRAGBZzW45PsjOEvygXFOy2n7AXL9nHogDiMdbe4aY2VT70sl0ccc4uvVOvVBM
        inOpd2rEpX0/8YE0dRXxukrM7i+r6lWy1lSKbP+0tQxQHNa/Cjg5W3uU+W9YmNUFc1w/7QT4SZrn
        RBEo++Xf9D3YNaOCFZXhy63IpY4eTQCJFQcXdnRbTXEdC3CtWNd7SV/hmfJYekb3GEV+10xLOvpe
        /+tCTeCDpFDJP6UuzLXBBADL2oV3D56hYlOlscjBokNUAYYlWgfwA91NjDsWW9mwapm/eLs4FNyH
        0JcMFTWH9dnl8B7PCUra/Lg/IVv6HkFEuCL7hVXGMbw2BZuCIC2VG1ZQ6QD64X8g5zL+HDsusQDb
        EJV2ZtojalTIjpxMksbRZRsH+P3+NNOZOEwUdjJUAx8CAwEAAQ==
        -----END PUBLIC KEY-----'''
    rsa_key = RSA.importKey(public_key)
    cipher = PKCS1_v1_5.new(rsa_key)
    cipher_text = base64.b64encode(cipher.encrypt(text.encode())).decode()
    return cipher_text


def login(user_section):
    global user
    account = CONFIG.get(user_section, 'account')
    password = CONFIG.get(user_section, 'password')

    data = {'app': '1',
            'sig': '6929e62d8fad18a8',
            'ct': '2',
            'password': encrypt(password),
            'authCode': '', 'identify': 'b294a68564f27ee2', 'v': '5.0.1',
            'mobile': account,
            'sversion': '30',
            'device': 'Xiaomi%3ARedmi%20K30i%205G',
            'apn': 'wifi',
            'token': ''}
    res = requests.post(BASE_URL + '/passport/login', data=data, headers=headers)
    if res.cookies:
        cookies.update(res.cookies.get_dict())
    data = res.json()
    school_info = data['data']['user']['school']
    user_info = data['data']['user']
    school = School(school_info)
    user_info['school'] = school
    user = User(user_info)

    token = data['data']['access_token']
    headers['loginToken'] = token
    headers['Authorization'] = 'Bearer ' + token
    CONFIG.set(user_section, 'token', token)
    CONFIG.set(user_section, 'https_waf_cookie', cookies['https_waf_cookie'])
    CONFIG.write(open(CONFIG_PATH, 'w'))  # a追加
    # cookies['loginToken'] = token


def checkin():
    # 获取题目
    res = requests.get(BASE_URL + '/checkin/question', cookies=cookies, headers=headers)
    data = res.json()['data']
    if data['isChecked'] == 1:
        print('今天已经签到过了')
        return
    print('今天的签到题目: ' + data['survey']['question']['title'], end='')
    question = data['survey']['question']
    option = question['option']
    answer = []
    title = []
    if question['type'] == '1':
        print(' [单选题]')
        r = random.randint(0, len(option) - 1)
        answer.append(option[r]['id'])
        title.append(option[r]['content'])
    if question['type'] == '2':
        print(' [多选题]')
        opts = []
        multiple_choice(0, option, [], opts)
        r = random.randint(0, len(opts) - 1)
        random_opts = opts[r]
        for d in random_opts:
            answer.append(d['id'])
            title.append(d['content'])

    print('随机选择: ', title)
    data = {
        'optionId': answer
    }
    res = requests.post(BASE_URL + '/checkin/answer', cookies=cookies, headers=headers, data=data)
    days = res.json()['data']['days']
    print(f'签到成功,当前已经签到了{days}天')


def initialize(user_section):  # 读取配置文件
    global user
    token = CONFIG.get(user_section, 'token')
    headers['loginToken'] = token
    headers['Authorization'] = 'Bearer ' + token
    user_id = get_user_id()
    if not user_id:
        print('当前token已过期, 正在重新登录')
        return False
    user_info = get_user_info(user_id)
    school_info = get_school_info(user_id)
    school = School(school_info)
    user_info['school'] = school
    user = User(user_info)
    return True


def get_user_id():
    res = requests.get(BASE_URL + '/home', headers=headers)
    data = res.json()['data']
    if not data:
        return None
    user_id = data['user']['id']
    return user_id


def get_user_info(user_id):
    res = requests.get(f'{BASE_URL}/users/{user_id}', headers=headers)
    user_info = res.json()['data']['profile']
    user_info['user_id'] = user_id
    return user_info


def get_school_info(user_id):
    res = requests.get(f'{BASE_URL}/users/{user_id}/school', headers=headers)
    school_info = res.json()['data']
    return school_info


def yooc():
    # 首页入口
    url = 'https://www.yooc.me/banner/api/placement/index-entrance'
    # cookies['client'] = 'android'
    res = requests.get(url, cookies=cookies, headers=headers)
    # print(res.single.json())
    # 首页轮播图
    url = 'https://www.yooc.me/banner/api/placement/index-banner'
    # 个人中心
    url = 'https://www.yooc.me/mobile/dashboard'
    res = requests.get(url, cookies=cookies, headers=headers)
    # print(res.text)


def main(user_section):
    if not initialize(user_section):
        login(user_section)
    print(user)
    checkin()
    yooc()


def run():
    sections = CONFIG.sections()
    print('正在读取配置文件...')
    for section in sections:
        main(section)
        print('=' * 60)


if __name__ == '__main__':
    headers = {
        "Authorization": "Bearer",
        "loginToken": "",
        "AppVersion": "5.0.1",
        "User-Agent": "YiBan/5.0.1 Mozilla/5.0 (Linux; Android 11; Redmi K30i 5G Build/RKQ1.200826.002; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/87.0.4280.141 Mobile Safari/537.36",
    }
    cookies = {}
    user = User
    run()

