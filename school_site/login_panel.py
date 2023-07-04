from resource.login import Ui_Form
from PyQt5.Qt import *


class LoginPanel(QWidget, Ui_Form):
    login_signal = pyqtSignal(str, str)

    def __init__(self, parent=None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.setupUi(self)
        self.has_login = False
        self.remember = False

    def login(self):
        self.login_signal.emit(self.username.text(), self.password.text())

    def visible(self):
        if self.password.echoMode() == QLineEdit.Password:
            self.password.setEchoMode(QLineEdit.Normal)
            self.pwd_action.setIcon(QIcon('resource/images/attention_forbid.png'))
        else:
            self.password.setEchoMode(QLineEdit.Password)
            self.pwd_action.setIcon(QIcon('resource/images/attention.png'))

    def set_remember(self, flag):
        self.remember = flag


if __name__ == '__main__':
    import sys

    app = QApplication(sys.argv)

    window = LoginPanel()
    window.show()

    sys.exit(app.exec_())
