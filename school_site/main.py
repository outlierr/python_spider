import random
import time
from bs4 import BeautifulSoup
import json
import execjs
from api.api import *
from auto_course.school_site.main import login

with open('lib/getCookie.js', 'r', encoding='utf-8') as f:
    JS = execjs.compile(f.read())


def set_https_cookie():
    global cookies
    res = requests.get('https://www.gzpyp.edu.cn/jAQtMuUpIA11/cFFwv92/e1a968', headers=headers, verify=False)
    s = re.findall(r'function R\$aq\(\)\{return\s*"(.*?)"', res.text)[0]
    https = JS.call('getCookie', s)
    cookies = 'QJBmiuCuDvyL717https=' + https + '; '
    # cookies['QJBmiuCuDvyL717https'] = https


def get_session_id():
    global cookies
    headers = {
        'Cookie': cookies
    }
    res = requests.get(BASE_URL + '/jsxsd/', headers=headers, verify=False)
    for item in res.cookies.items():
        cookies += f'{item[0]}={item[1]}; '


def update_config(user_section):
    CONFIG.set(user_section, 'cookies', cookies)
    CONFIG.write(open(CONFIG_PATH, 'w'))  # a追加


def course_select():
    base_url = BASE_URL + '/jsxsd'
    uri = menu['学生选课中心']
    tr_list = []
    res = requests.get(base_url + uri, headers=headers, verify=False)
    soup = BeautifulSoup(res.text, 'html.parser')
    tr_list = soup.select('#tbKxkc > tr')
    if tr_list[1].__contains__("未查询到数据"):
        pass
    time.sleep(0.2)
    print("选课还未开始...")
    for tr in tr_list[1:]:
        uri = tr.select('td')[-1].a['href']  # 只有一个子节点才可以用.属性
        title = tr.select('td')[1].string
        url = BASE_URL + uri
        res = requests.get(url, headers=headers, verify=False)
        soup = BeautifulSoup(res.text, 'html.parser')
        access_btn = soup.select('.el-button[value=" 进入选课 "]')[0]
        access_id = re.match(r'xsxkOpen\(\'(.*)\'\)', access_btn['onclick'])[1]
        script = soup.select('script[language="javascript"]:not([src],[type])')[0]
        access_uri = re.match(r'\s*function xsxkOpen\(.*?\)\{\s*window.open\("(.*?)"', script.string)[1]
        url = BASE_URL + access_uri + access_id


def get_course_json(uri):
    url = BASE_URL + uri
    params = (
        ('skxq_xx0103', ''),  # 上课校区
        ('kcxx', ''),  # 节次 第几节课
        ('skls', ''),  # 上课老师
        ('skxq', ''),  # 星期
        ('skjc', ''),  # 节次 第几节课
        ('sfym', 'false'),  # 过滤满人课程
        ('sfct', 'true'),  # 过滤冲突
        ('sfxx', 'true'),  # 过滤限选
        ('glyx', 'true')  # 过滤已选
    )
    data = {
        'sEcho': '1',
        'iColumns': '0',
        'sColumns': '',
        'iDisplayStart': 0,
        'iDisplayLength': 999
    }
    res = requests.post(url, data=data, params=params, headers=headers, verify=False)
    print(len(res.json()['aaData']))
    return res.json()


def student_evaluation():
    global headers
    base_url = BASE_URL + '/jsxsd'
    uri = menu['学生评价']
    res = requests.get(base_url + uri, headers=headers, verify=False)
    url = re.findall('<a href="(.*?)" title="点击进入评价">进入评价</a>', res.text)[0]
    res = requests.get('https://jiaowu.gzpyp.edu.cn' + url, headers=headers, verify=False)
    soup = BeautifulSoup(res.text, 'html.parser')
    trs = soup.select('#dataList tr')
    # titles = trs[0].select('th')
    tds = []
    for tr in trs[1:]:
        tds.append(tr.select('td'))
    for td in tds:
        if td[-2].text == '是' and td[-3].text == '是':
            continue
        print(f'--正在对{td[2].text}进行评价:')
        uri = td[-1].select('a')[0]['href']
        evaluation(uri)
    print('所有课程评价都已完成')


def evaluation(uri):
    url = BASE_URL + uri
    print(url)
    res = requests.get(url, headers=headers, verify=False)
    # 提取选项
    soup = BeautifulSoup(res.text, 'html.parser')
    need_submit = soup.select('#sfxyt')[0]['value']
    if need_submit == '0':
        print('该课程已经评论过了...')
        return
    table = soup.select('#table1')[0]
    form_ips = soup.select('#Form1 > input[type="hidden"]')
    tds = table.select('td[name="zbtd"]')
    # abc = re.findall()
    rank = re.findall(r'<tr>\s*<td>\s*(.*?)\s*<input type="hidden" name="(.*?)" value="(\d+)">\s*</td>\s*<td '
                      r'name="zbtd">', res.text, re.S)
    # 存在重复键 使用元组存储数据
    data_list = []
    opts = ['A.非常满意', 'B.比较满意', 'C.一般', 'D.不太满意', 'E.非常不满意']
    # print('length', len(rank), len(tds))
    for ip in form_ips:
        if ip['name'] == 'issubmit':
            data_list.append(('issubmit', '1'))  # 请求接口类型为提交
            continue
        if ip['name'] == 'sfxyt':
            data_list.append(('sfxyt', '0'))  # 0为已经提交过了
            continue
        data_list.append((ip['name'], ip['value']))

    for i in range(len(tds)):
        print(f'评价项: {rank[i][0]} 选择: ', end='')
        data_list.append((rank[i][1], rank[i][2]))
        hidden = tds[i].select('input[type="hidden"]')
        radio = tds[i].select('input[type="radio"]')
        _id = radio[0]['name']
        length = len(radio)
        r = random.randint(0, length - 2)
        for j in range(length):
            data_list.append((hidden[j]['name'], hidden[j]['value']))
            if j == r:  # 随机选择
                data_list.append((_id, radio[j]['value']))
                print(opts[r])

    is_xtjg = soup.select('#isxtjg')[0]
    data_list.append((is_xtjg['id'], is_xtjg['value']))
    # 参数改为提交 save保存选择后的分rank数
    url = BASE_URL + '/jsxsd/xspj/xspj_save.do'
    data = tuple(data_list)
    # print(data)
    res = requests.post(url, data=data, headers=headers, verify=False)
    print(res.text)


def initialize(user_section):
    global cookies
    global menu
    if not os.path.exists('archive/menu.json'):
        print('登录初始化菜单...')
        set_https_cookie()
        get_session_id()
        main_html = login(user_section)
        print(main_html)
        ret_list = re.findall('<li.*?data-url="(.*?)">[\S\s]+?</i>(.*?)<', main_html)
        for item in ret_list:
            menu[item[1]] = item[0]
        _json = json.dumps(menu, ensure_ascii=False)
        with open('archive/menu.json', 'w') as wf:
            wf.write(_json)
            menu = json.loads(_json)
    else:
        with open('archive/menu.json', 'r') as rf:
            menu = json.loads(rf.read())

    cookies = CONFIG.get('User-1', 'cookies')
    # print('init', cookies)
    headers['Cookie'] = cookies
    res = requests.get(BASE_URL + '/jsxsd/xspj/xspj_find.do', headers=headers, verify=False)
    if re.match('.*<title>登录</title>', res.text, re.S) or res.status_code == 412:
        print('当前cookie已过期, 正在重新登录')
        return False
    return True


def main(user_section):
    if not initialize(user_section):
        get_session_id()
        login(user_section)
        update_config(user_section)

    # student_evaluation()
    course_select()


def run():
    sections = CONFIG.sections()
    print('正在读取配置文件...')
    for section in sections:
        main(section)
        print('=' * 60)


if __name__ == '__main__':
    cookies = ''
    headers = {
        'Cookie': cookies
    }
    menu = {}
    run()

# 'mDataProp_0': 'kch',  # 课程编号
# 'mDataProp_1': 'kcmc',  # 课程名
# 'mDataProp_2': 'fzmc',  # 分组名
# 'mDataProp_3': 'ktmc',  # 合班名称
# 'mDataProp_4': 'xf',  # 学分
# 'mDataProp_5': 'skls',  # 上课老师
# 'mDataProp_6': 'sksj',  # 上课时间
# 'mDataProp_7': 'skdd',  # 地点
# 'mDataProp_8': 'xqmc',  # 上课校区
# 'mDataProp_9': 'xxrs',  # 限选人数
# 'mDataProp_10': 'ctsm',  # 时间冲突
# 'mDataProp_11': 'czOper',
