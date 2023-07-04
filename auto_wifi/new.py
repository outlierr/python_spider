from urllib.parse import quote_plus
import rsa
import time
import re
import requests
import os
from PyQt5.QtCore import *
from auto_wifi.orc_test.ocr import DdddOcr

ocr = DdddOcr(old=True)


# 图片处理 灰度+二值化
def convert_img(img, threshold):
    img = img.convert("L")  # 处理灰度
    pixels = img.load()
    for x in range(img.width):
        for y in range(img.height):
            if pixels[x, y] > threshold:
                pixels[x, y] = 255
            else:
                pixels[x, y] = 0
    return img


def padding_crypto(info):
    pk = 'b2867727e19e1163cc084ea57b9fa8406a910c6703413fa7df96c1acdca7b983a262e005af35f9485d92cd4c622eca4a14d6fd818adca5cae73d9d228b4ef05d732b41fb85f80af578a150ebd9a2eb5ececb853372ca4731ca1c8686892987409be3247f9b26cae8e787d8c135fc0652ec0678a5eda0c3d95cc1741517c0c9c3'
    modulus = int(pk, 16)
    exponent = int('10001', 16)

    rsa_key = rsa.PublicKey(modulus, exponent)

    pwd = rsa.encrypt(info.encode(), rsa_key)
    return pwd.hex()


def connect_wifi():
    return False


class ConnectThread(QThread):
    change_text_signal = pyqtSignal(dict)
    result_signal = pyqtSignal(int, str)
    ip_signal = pyqtSignal()
    enable_signal = pyqtSignal(bool)

    ERROR = 0
    SUCCESS = 1
    RETRY = 2

    def __init__(self):
        super().__init__()
        self.second_page_url = 'http://125.88.59.131:10001/qs/index_gz.jsp?wlanacip=183.6.63.1&wlanuserip=10.22.27.237'
        self.ss = requests.session()
        self.ss.trust_env = False
        self.startup_conn = False
        self.connected = False
        self.cip = '183.6.63.1'
        self.username1 = ''
        self.password1 = ''
        self.username2 = ''
        self.password2 = ''
        self.user_ip = ''
        self.query_str = ''
        connect_wifi()

    def network_status(self):
        # if subprocess.run('ping -n 1 www.baidu.com', stdout=subprocess.PIPE, shell=True).returncode != 0:
        #     self.change_status_text(False)
        #     return False
        try:
            requests.get("https://www.baidu.com", timeout=0.5)
        except requests.exceptions.ReadTimeout:
            self.change_status_text(False)
            return False
        return False

    def run(self) -> None:
        self.enable_signal.emit(False)
        if not self.connected:
            print('连接')
            self.get_verify()
        else:
            print('断开')
            self.connected = self.logout()

        self.enable_signal.emit(True)

    def set_account(self, info):
        for key, value in info.items():
            if key in self.__dict__.keys():
                setattr(self, key, value)

    def check_account(self):
        return self.username1 and self.username2 and self.password1 and self.password2

    def add_2_startup(self):
        file_path = os.getcwd() + '\\auto_wifi.py'
        user = os.getlogin()
        with open(rf'C:\Users\{user}\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup校园网.bat', 'w') as f:
            f.write(f'python {file_path}')

    def get_online_userinfo(self):
        res = self.ss.post('http://192.168.200.84/eportal/InterFace.do?method=getOnlineUserInfo')
        res.encoding = 'utf-8'
        self.ss.cookies.clear()  # cookies要清空 不然第二页面退出就不会获得新的 SessionID
        return res.json()

    def _first_query_str(self):
        url = 'http://www.gstatic.com/generate_204'
        # url = 'http://qq.com'
        res = self.ss.get(url)
        # 204为第一页面已登录 无法重定向
        if not res.history and res.status_code != 204:
            # groups 返回捕获组元组  group通过索引获捕获的字符串
            self.query_str = quote_plus(re.match(".*?href='(.*?)'", res.text).group(1))
        # else:
        #     # 第一页面已经登录 退出重新登录获取 query_str
        #     self.first_page_logout()
        #     time.sleep(1)
        #     self._first_query_str('http://www.baidu.com')

    def _first_page(self):
        # 检查第一页面是否已登录
        info = self.get_online_userinfo()
        if info['result'] != 'fail':
            self.user_ip = info['userIp']
            print('第一页面已经登录')
            return True
        self._first_query_str()
        # username = '2013400104'
        # password = 'Pyp184218'
        data = f'userId={self.username1}&password={self.password1}&service=dianxin&queryString={self.query_str}&operatorPwd=&operatorUserId=&validcode=&passwordEncrypt=false'
        res = self.ss.post('http://192.168.200.84/eportal/InterFace.do?method=login', data=data,
                           headers={'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'})
        res.encoding = 'utf-8'
        _json = res.json()
        print(_json)
        if _json['result'] != 'success':
            self.emit_result_signal(self.ERROR, _json['message'])
            return False
        res = self.ss.get('http://www.msftconnecttest.com/redirect')
        self.second_page_url = res.url
        try:
            (self.cip, self.user_ip) = re.match('.*?wlanacip=(.*?)&wlanuserip=(.*)', res.url).groups()
            self.ip_signal.emit()
            print(self.cip, self.user_ip)
        except AttributeError:
            print('第二页面已经登录')

            # 第一次连接静默 不提示
            # if self.startup_conn:
            #     self.emit_result_signal(self.SUCCESS, '')
            # else:
            #     self.emit_result_signal(self.SUCCESS, '连接校园网成功')

            self.emit_result_signal(self.SUCCESS, '连接校园网成功')
            self.change_status_text(True)
            return False
        return True

    def _second_page(self, logout=False):
        # username = '19124232365'
        # password = 'a6318421'
        code = self.get_verify()
        print('验证码为:', code)

        info = '{"userName":"' + self.username2 + '","password":"' + self.password2 + '","rand":"' + code + '"}'
        login_key = padding_crypto(info)

        data = {
            'loginKey': login_key,
            'wlanuserip': self.user_ip,
            'wlanacip': self.cip
        }

        res = self.ss.request("POST", 'http://125.88.59.131:10001/ajax/login', data=data)
        json = res.json()
        print('第二页面登录结果:', 'success' if json['resultCode'] == '0' else 'failed', ', 响应信息:', json['resultInfo'])
        print(json)
        if json['resultCode'] == '0':
            if not logout:
                # if not self.startup_conn:
                self.emit_result_signal(self.SUCCESS, '连接校园网成功')
                self.change_status_text(True)

        elif json['resultInfo'] == '验证码错误':
            return self._second_page()

        else:
            if not logout:
                self.emit_result_signal(self.ERROR, json['resultInfo'])
                self.change_status_text(False)
            return False
        return True

    def first_page_logout(self):
        # 退出第一页面
        res = self.ss.get('http://192.168.200.84/eportal/InterFace.do?method=logout', timeout=0.5)
        res.encoding = 'utf-8'
        print(res.text)

    def logout(self):
        print(self.ss.cookies)
        if not self.cip or not self.user_ip:
            self.user_ip = self.get_online_userinfo()['userIp']
            self.ss.cookies.clear()
            # 获取 uip 和 cip 第二页面才能正常退出
            # self._first_page()  # 退出重新登录获取 aip 和 uip

        if not self.ss.cookies:
            self._second_page(True)

        # 退出第二页面
        params = {
            'wlanacip': self.cip,
            'wlanuserip': self.user_ip
        }
        res = self.ss.post('http://125.88.59.131:10001/ajax/logout', data=params)
        print(res.text)

        # 退出第一页面
        try:
            self.first_page_logout()
        except requests.exceptions.ConnectionError:
            self.emit_result_signal(self.ERROR, '当前连接的WIFI不是校园网')
            return True

        self.emit_result_signal(self.SUCCESS, '断开校园网成功')
        self.change_status_text(False)
        return False

    def get_verify(self):
        url = 'https://jiaowu.gzpyp.edu.cn/jsxsd/verifycode.servlet?t=' + str(int(round(time.time() * 1000)))
        res = self.ss.get(url)
        try:
            code = ocr.classification(res.content)
        except AttributeError:
            return self.get_verify()
        if len(code) != 4:
            return self.get_verify()
        self.emit_result_signal(self.SUCCESS, code)

    def change_status_text(self, conn):
        if conn:
            self.emit_change_text_signal({'btn': '断开校园网', 'status': '已连接', 'tray_conn': '断开校园网'})
        else:
            self.emit_change_text_signal({'btn': '连接校园网', 'status': '已断开', 'tray_conn': '连接校园网'})

    def emit_result_signal(self, code, msg):
        self.result_signal.emit(code, msg)

    def emit_change_text_signal(self, text):
        self.change_text_signal.emit(text)
