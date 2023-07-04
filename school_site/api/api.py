import requests
from aip import AipOcr
import configparser
import os
import re

BASE_URL = 'http://jiaowu.gzpyp.edu.cn'

# 读配置文件
CONFIG_PATH = os.getcwd() + '/config.ini'
CONFIG = configparser.ConfigParser()
CONFIG.read(CONFIG_PATH)
COOKIES = ''
APP_ID = '20134137'
API_KEY = '9aetAvxmVAEyGnpEl1pHcmVw'
SECRET_KEY = 'sKinSBRBWczac5CiHWv53rQRU8VYFnRv'
client = AipOcr(APP_ID, API_KEY, SECRET_KEY)
