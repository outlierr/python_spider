from PyQt5.Qt import *
import sys

class SelectSource(QWidget):
    def __init__(self, url, title):
        super(SelectSource, self).__init__()
        self.table = QTableWidget()
        # 列表显示
        self.url = url
        self.title = title
        self.layout = QHBoxLayout()
        self.data = []
        self.lines = []
        self.xk_name = ''
        self.submit = QPushButton("提交数据")
        self.log = QTextBrowser()

    def setupUi(self):
        self.setWindowTitle(self.title)
        self.resize(800, 500)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)  # 仅首列可以拉伸
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)  # 禁止修改

        head = ['课程名', '老师', '上课时间', '学分', '选择']
        if self.data and self.data[0].get('fzmc'):
            head.insert(1, '分组名')

        self.table.setColumnCount(len(head))  # 要先设置多少列 后面才能设置列文字
        self.table.setHorizontalHeaderLabels(head)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)  # 自适应列宽

        for i in range(len(self.data)):
            # 初始化没设置多少行则需要手动插入行
            self.table.insertRow(i)
            j = 0
            course = QTableWidgetItem(self.data[i]['kcmc'])
            course.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
            self.table.setItem(i, j, course)
            j += 1

            if '分组名' in head:
                group = QTableWidgetItem(self.data[i]['fzmc'])
                group.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
                self.table.setItem(i, j, group)
                j += 1

            teacher = QTableWidgetItem(self.data[i]['skls'])
            teacher.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
            self.table.setItem(i, j, teacher)
            j += 1

            class_time = QTableWidgetItem(self.data[i]['sksj'])
            class_time.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
            self.table.setItem(i, j, class_time)
            j += 1

            score = QTableWidgetItem(str(self.data[i]['xf']))
            score.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
            self.table.setItem(i, j, score)
            j += 1
            # checkbox居中使用的方法是将checkbox加入QHboxLayout使QHboxLayout居中，将QHboxLayout加入一个QWidget
            checkbox = QCheckBox()
            # 生成居中的选择框
            h = QHBoxLayout()
            h.setAlignment(Qt.AlignCenter)
            h.addWidget(checkbox)
            w = QWidget()
            w.setLayout(h)
            self.table.setCellWidget(i, j, w)
            self.lines.append({'name': course, 'ck': checkbox, 'sksj': class_time, 'teacher': teacher})

        # self.table.itemSelectionChanged.connect(self.select)
        self.layout.addWidget(self.table)
        self.layout.addWidget(self.submit)
        self.setLayout(self.layout)
        self.submit.clicked.connect(self.submit_data)

    # def select(self):
    #     self.row_idx = self.table.currentRow()
    def generate_optional(self):
        res = requests.get(self.url, headers=headers, verify=False)
        soup = BeautifulSoup(res.text, 'html.parser')
        come_in_uri = soup.select('#topmenu > li:nth-child(2)')[0].a['href']
        url = JW_URL + come_in_uri
        res = requests.get(url, headers=headers, verify=False)
        uri = re.match('.*"sAjaxSource":"(.*?)"', res.text, re.S)[1]
        self.xk_name = re.match(r'.*?var rev = .*?cache:false,.*?url:"(.*?)"', res.text, re.S)[1]
        _json = get_course_json(uri)
        data = _json['aaData']
        online_courses = []
        for course in data:
            if not course.get('ctsm') or course['ctsm'] == '':
                self.data.append(course)
        self.data.sort(key=lambda obj: obj['xf'], reverse=True)

    def submit_data(self):
        selected = []
        for line in self.lines:
            if line['ck'].isChecked():
                selected.append(line)
        j = 0
        for i in range(len(self.data)):
            data = self.data[i]
            if selected[j]['teacher'].text() == data['skls'] and selected[j]['sksj'].text() == data['sksj']:
                _json = self.select_one_course(data['jx0404id'], data['jx02id'])
                if not _json['success']:
                    QMessageBox.information(self, "选课失败", _json['message'], QMessageBox.Yes)
                    break
                j += 1
                QMessageBox.information(self, f"{selected[j]['name']}选课成功", _json['message'], QMessageBox.Yes)

    def select_one_course(self, jx0404id, jx02id):
        url = f'{JW_URL}{self.xk_name}?kcid={jx02id}&cfbs=null&jx0404id={jx0404id}&xkzy=&trjf=&_=' \
              f'{str(int(time.time() * 1000))}'
        print(url)
        res = requests.get(url, headers=headers, verify=False)
        print(res.json())
        return res.json()


if __name__ == '__main__':
    # 调用应用
    app = QApplication(sys.argv)
    win = SelectSource(url, title)
    win.generate_optional()
    win.setupUi()
    win.show()
    app.exec_()  # 执行