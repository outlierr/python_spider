from login_panel import LoginPanel
from PyQt5.Qt import *
from api import Api
from utils import *
import configparser
import os

if __name__ == '__main__':
    import sys

    app = QApplication(sys.argv)
    api = Api()
    login_panel = LoginPanel()

    def login(username, password):
        (login_panel.has_login, info) = api.login(username, password)
        print('是否登录成功:', login_panel.has_login)
        if not login_panel.has_login:
            QMessageBox.critical(login_panel, '提示', info)
            return
        set_user(username, password if login_panel.remember else None)

    login_panel.login_signal.connect(login)

    login_panel.show()

    sys.exit(app.exec_())
