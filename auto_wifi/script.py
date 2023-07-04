# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'test.ui'
#
# Created by: PyQt5 UI code generator 5.15.4
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.
import time

import requests
from PyQt5 import QtCore, QtGui, QtWidgets

from ocr import DdddOcr

ocr = DdddOcr(old=True)


class Ui_MainWindow(object):
    def __init__(self):
        self.ss = requests.session()

    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(503, 370)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.img = QtWidgets.QLabel(self.centralwidget)
        self.img.setGeometry(QtCore.QRect(190, 60, 72, 15))
        self.img.setText("")
        self.img.setScaledContents(True)
        self.img.setObjectName("img")
        self.show = QtWidgets.QLabel(self.centralwidget)
        self.show.setGeometry(QtCore.QRect(190, 220, 72, 15))
        self.show.setObjectName("show")
        self.pushButton = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton.setGeometry(QtCore.QRect(190, 280, 93, 28))
        self.pushButton.setObjectName("pushButton")
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 503, 26))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.pushButton.clicked.connect(self.get_verify)
        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "验证码识别测试"))
        self.show.setText(_translate("MainWindow", "验证码"))
        self.pushButton.setText(_translate("MainWindow", "测试"))

    def get_verify(self):
        print("test")
        url = 'https://jiaowu.gzpyp.edu.cn/jsxsd/verifycode.servlet?t=' + str(int(round(time.time() * 1000)))
        res = self.ss.get(url)
        with open("../img.jpg", "wb") as f:
            f.write(res.content)
        pix = QtGui.QPixmap("../img.jpg")
        self.img.setPixmap(pix)
        try:
            code = ocr.classification(res.content)
        except AttributeError:
            return self.get_verify()
        if len(code) != 4:
            return self.get_verify()
        print(code)
        self.show.setText(code)


if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())