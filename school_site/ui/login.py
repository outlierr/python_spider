from PyQt5.Qt import *


class Window(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("登录")
        self.resize(500, 500)
        self.setup_ui()

    def setup_ui(self):
        gl = QGridLayout()
        self.setLayout(gl)
        for i in range(9):
            label = QLabel()
            label.resize(50, 50)
            label.setText(str(i))
            gl.addWidget(label)
        gl.addWidget(QPushButton())
        print(QLayout.__bases__)
        # student_no = QLabel("学号: ")
        # password = QLabel("密码: ")
        #
        # no_le = QLineEdit()
        # pwd_le = QLineEdit()
        # login_btn = QPushButton()
        # login_btn.setText("登录")
        #
        # form = QFormLayout()
        # form.setFormAlignment(Qt.AlignVCenter)
        #
        # form.addRow(student_no, no_le)
        # form.addRow(password, pwd_le)
        # form.addRow(login_btn)
        #
        #
        # self.setLayout(form)


if __name__ == '__main__':
    import sys

    app = QApplication(sys.argv)

    window = Window()
    window.show()

    sys.exit(app.exec_())
