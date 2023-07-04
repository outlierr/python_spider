import os

from PyQt5.QtCore import *
from PyQt5.QtGui import QCloseEvent, QIcon
from PyQt5.QtWidgets import *

from connector import ConnectThread
from login_dialog import LoginDialog
from ui.campus_wifi_ui import Ui_MainWindow


class Window(QMainWindow, Ui_MainWindow):

    def __init__(self):
        super().__init__()
        self.login_dialog = LoginDialog(self)
        self.worker = ConnectThread()
        self.args = qApp.arguments()
        self.app_path = os.path.dirname(self.args[0]).replace('/', '\\')
        self.tray_icon = QSystemTrayIcon(self)
        self.settings = QSettings(f'{self.app_path}\\config.ini', QSettings.IniFormat)
        self.init_configuration()

        self.setupUi(self)
        self.setWindowIcon(QIcon(f'{self.app_path}\\favicon.png'))
        self.conn_act = QAction(self.pushButton.text())
        self.set_tray_widget()

        self.status_label = QLabel()
        self.statusBar().addPermanentWidget(self.status_label)
        self.init_tab_data()
        self.bind_signal()
        self.worker.connected = self.worker.network_status()  # 这一行必须在绑定信号后 内触发了信号
        self.auto_connect()

    # wrapper
    def set_group(group):
        def wrapper(func):
            def inner_wrapper(self, *args, **kwargs):
                print(self)
                print(group)
                self.settings.beginGroup(group)
                func(self, *args, **kwargs)
                self.settings.endGroup()

            return inner_wrapper

        return wrapper

    def init_configuration(self):
        if not self.settings.allKeys():
            self.__account()
            self.__app()

    @set_group('account')
    def __account(self):
        self.settings.setValue('username1', '')
        self.settings.setValue('password1', '')
        self.settings.setValue('username2', '')
        self.settings.setValue('password2', '')

    @set_group('app')
    def __app(self):
        self.settings.setValue('quit_app_when_connected', False)
        self.settings.setValue('start_after_system_boot', False)

    def auto_connect(self):
        if not self.worker.connected and self.worker.check_account():
            self.worker.startup_conn = True
            self.worker.start()
        elif self.worker.connected and '--startup' in self.args:
            self.quit()

    def init_tab_data(self):
        self.settings.beginGroup('app')
        self.quit_ck.setChecked(True if self.settings.value('quit_app_when_connected') == 'true' else False)
        self.startup_ck.setChecked(True if self.settings.value('start_after_system_boot') == 'true' else False)
        self.settings.endGroup()

        self.settings.beginGroup('account')
        arr = self.settings.childKeys()
        flag = False
        info = {}
        for k in arr:
            v = self.settings.value(k)
            info[k] = v
            if v == '':
                flag = True

        if flag:
            self.login_dialog.open()
        else:
            self.worker.set_account(info)
            self.__fulfill_account_info(self, info)
        self.settings.endGroup()

    # 回显用户信息
    @set_group('account')
    def __fulfill_account_info(self, widget, info):
        widget.username1.setText(info['username1'])
        widget.password1.setText(info['password1'])
        widget.username2.setText(info['username2'])
        widget.password2.setText(info['password2'])

    def login_dialog_save(self):
        info = {
            'username1': self.login_dialog.username1.text().strip(),
            'password1': self.login_dialog.password1.text().strip(),
            'username2': self.login_dialog.username2.text().strip(),
            'password2': self.login_dialog.password2.text().strip()
        }
        self.__save_account(info, True)
        # 填充 tab2
        self.__fulfill_account_info(self, info)

    def login_tab_save(self):
        self.__save_account({
            'username1': self.username1.text().strip(),
            'password1': self.password1.text().strip(),
            'username2': self.username2.text().strip(),
            'password2': self.password2.text().strip()
        })

    def pwd1_visible(self):
        if self.password1.echoMode() == QLineEdit.Password:
            self.password1.setEchoMode(QLineEdit.Normal)
            self.pwd1_action.setIcon(QIcon(f'{self.app_path}\\attention_forbid.png'))
        else:
            self.password1.setEchoMode(QLineEdit.Password)
            self.pwd1_action.setIcon(QIcon(f'{self.app_path}\\attention.png'))

    def pwd2_visible(self):
        self.pwd2_action.setIcon(QIcon(f'{self.app_path}\\attention_forbid.png'))
        if self.password2.echoMode() == QLineEdit.Password:
            self.password2.setEchoMode(QLineEdit.Normal)
            self.pwd2_action.setIcon(QIcon(f'{self.app_path}\\attention_forbid.png'))
        else:
            self.password2.setEchoMode(QLineEdit.Password)
            self.pwd2_action.setIcon(QIcon(f'{self.app_path}\\attention.png'))

    @set_group('account')
    def __save_account(self, data, dialog=False):
        if '' not in data.values():
            for k, v in data.items():
                self.settings.setValue(k, v)
            self.worker.set_account(data)
            QMessageBox.information(self, '提示', '设置成功', QMessageBox.Yes)
            if dialog:
                # 登录 dialog 后面不需要用了
                self.login_dialog.deleteLater()
                del self.login_dialog
        else:
            QMessageBox.warning(self, '警告', '第一页面和第二页面的账号密码都要填', QMessageBox.Yes)

    @set_group('app')
    def app_settings(self, key, value):
        self.settings.value(key, value)

    def startup_2_registry(self, boot):
        registry = QSettings('HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run',
                             QSettings.NativeFormat)
        path = QDir.currentPath().replace('/', '\\')
        if boot:
            if not registry.value('campus_wifi'):
                registry.setValue('campus_wifi', f'{path}\\campus_wifi.exe --startup')
        else:
            registry.remove('campus_wifi')

    def set_tray_widget(self):
        self.tray_icon.setIcon(self.windowIcon())
        menu = QMenu()
        self.conn_act.triggered.connect(self.worker.start)

        quit_act = QAction('退出', self)

        quit_act.triggered.connect(self.quit)

        menu.addAction(self.conn_act)
        menu.addAction(quit_act)

        self.tray_icon.setContextMenu(menu)
        self.tray_icon.setToolTip(self.windowTitle())
        self.tray_icon.show()
        self.tray_icon.activated.connect(self.show_window)

    def quit(self):
        self.tray_icon.deleteLater()
        # QCoreApplication.quit()
        # QCoreApplication.exit(0)
        # 延时 使程序进入事件循环 在未进入事件循环情况下 程序将不会退出
        QTimer.singleShot(0, QCoreApplication.quit)

    def bind_signal(self):
        self.worker.result_signal.connect(self.prompt)
        self.worker.change_text_signal.connect(self.set_text)
        self.worker.ip_signal.connect(self.set_ip)
        self.worker.enable_signal.connect(self.enable_btn)

    def show_window(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            if not self.isVisible():
                self.show()
            if self.isMinimized():
                self.showNormal()

    def prompt(self, code, msg):
        if code == self.worker.ERROR:
            QMessageBox.critical(self, '提示', msg, QMessageBox.Yes)
        elif code == self.worker.SUCCESS:
            QMessageBox.information(self, '提示', msg, QMessageBox.Yes)
            if self.worker.startup_conn and self.settings.value(
                    'app/quit_app_when_connected') == 'true' and self.worker.connected:
                self.quit()
            self.worker.startup_conn = False

        elif code == self.worker.RETRY:
            box = QMessageBox(self)
            box.setIcon(QMessageBox.Warning)
            box.setWindowTitle('警告')
            box.setText(msg)
            box.addButton('重试', QMessageBox.YesRole)
            btn_no = box.addButton('退出', QMessageBox.RejectRole)
            box.exec_()
            box.deleteLater()
            if box.clickedButton() == btn_no:
                raise RuntimeError

    def __set_progress_value(self, value):
        self.download_dialog.progressBar.setValue(value)

    def set_text(self, dct):
        self.pushButton.setText(dct['btn'])
        self.status_label.setText(dct['status'])
        self.conn_act.setText(dct['tray_conn'])

    def click(self):
        self.worker.start()

    def set_ip(self):
        self.ip.setText(self.worker.user_ip)

    def enable_btn(self, b):
        self.pushButton.setEnabled(b)

    def closeEvent(self, e: QCloseEvent):
        print('关闭事件')
        ret = QMessageBox.information(self, '提示', '是否最小化到托盘?', QMessageBox.No | QMessageBox.Yes)
        if ret == QMessageBox.Yes:
            e.ignore()
            self.hide()
        else:
            self.settings.setValue('app/quit_app_when_connected', self.quit_ck.isChecked())
            self.settings.setValue('app/start_after_system_boot', self.startup_ck.isChecked())
            self.startup_2_registry(self.settings.value('app/start_after_system_boot'))
            super().closeEvent(e)


if __name__ == '__main__':
    import sys

    app = QApplication(sys.argv)

    window = Window()
    window.show()

    sys.exit(app.exec_())

# 第一页面没登陆时 访问页面会重定向获得第一页面地址
# res = self.ss.get('http://www.qq.com')
# (href) = re.match(".*?href='(.*?)'", res.text).groups()
