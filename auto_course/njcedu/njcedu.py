import asyncio
import hashlib
import json
import random
import re
import time
from bs4 import BeautifulSoup
import requests
import aiohttp


def login():
    global cookies
    login_id = 'pyp-2140220111'
    password = '123456'
    cookies = {}
    data = {
        'strLoginId': login_id,
        'strPassword': hashlib.md5(password.encode(encoding='UTF-8')).hexdigest(),
        'lEduId': 0,
        'lSchoolId': 0
    }
    res = requests.post('http://passport.njcedu.com/rest/v1/UserService/SSOLogin', data=data)
    for c in res.cookies:
        cookies[c.name] = c.value
    data = res.json()
    headers = {
        'Referer': 'http://passport.njcedu.com/',
    }
    # 需要二次登录获取学校token
    do_login_url = data['response']['arrLoginUrl'][0] + '&jsonpCallback=callback&_=' + str(int(time.time() * 1000))
    print('登录请求地址', do_login_url)
    res = requests.get(do_login_url, cookies=cookies, headers=headers)
    for c in res.cookies:
        cookies[c.name] = c.value


def get_tasks():
    res = requests.get('http://school.njcedu.com/api/student/teachplan/getMyLearningTasks?nPageindex=0&nPageSize=10',
                       cookies=cookies)
    data = res.json()['response']['datas']
    tasks = []
    print('当前共有', len(data), '个任务:')
    for d in data:
        tasks.append({
            'id': d['lId'],
            'plan_id': d['lPlanId'],
            'name': d['strPlanName'],
            'state': d['strState'],
            'score': d['nSumScore'],
            'ScoreState': d['bScoreState']  # 成绩是否公开
        })
        print(f"任务名:{d['strPlanName']},是否结束:{d['strState']},成绩:{d['nSumScore'] if d['bScoreState'] else '未公开'}")
    return tasks


async def resolve_task(tasks):
    # connector = aiohttp.TCPConnector(ssl=False)
    async with aiohttp.ClientSession(cookies=cookies) as session:
        for task in tasks:
            await task_missions(task, session)


async def task_missions(t, session):
    url = 'http://pyp.njcedu.com/student/prese/teachplan/listdetail.htm?id='
    global school_id
    global user_id
    async with session.get(url + str(t['plan_id']), cookies=cookies) as res:
        print(t['name'])
        res = requests.get(url + str(t['plan_id']), cookies=cookies)
        soup = BeautifulSoup(res.text, 'lxml')
        school_id = int(soup.select('#lSchoolId')[0]['value'])
        user_id = int(soup.select('#lUserId')[0]['value'])
        # 视频
        video_tr_list = soup.select('#courseTable tr')

        for tr in video_tr_list[1:]:
            td_list = tr.select('td')

            video_name = str(td_list[0].string)  # .string返回的不是原生str类型

            # 视频链接
            hrefs = td_list[-1].select('a')
            course_id = re.match(r'javaScript:show\((\d+)\)', hrefs[0]['href'])[1]

            # 视频时长
            ret = re.match(r'.*?(\d+) / (\d+)）', td_list[1].string)
            watched_minutes = int(ret[1])
            video_minutes = int(ret[2])
            # 练习
            correct = td_list[2].text
            if watched_minutes >= video_minutes and len(re.findall(r'(/|[1-9]\d+\.0%)', correct)) > 0:
                print(f'视频ID:{course_id}, {video_name}的视频和练习已完成')
                print('=' * 50)
                continue

            if watched_minutes < video_minutes:
                video_minutes -= watched_minutes
                await refresh_video(course_id, video_name, video_minutes, session)
                await do_course_exercise(session, course_id, video_name)

        # 异步做评测和视频练习题
        tr_list = soup.select('#EvaluationTable tr')
        evaluation_tasks = [asyncio.create_task(do_evaluation(tr.a, session)) for tr in tr_list[1:]]
        await asyncio.wait(evaluation_tasks)
        # if len(video_tasks) > 0:
        #     await asyncio.wait(video_tasks) 不能使用一次性执行所有并发任务 视频任务多时 任务内会发送n多个异步请求 导致请求池不够用报错


async def do_course_exercise(session, course_id, name):
    url = f'http://course.njcedu.com/questionRecord.htm?courseId={course_id}&lPanId=0'
    async with session.get(url, cookies=cookies) as res:
        text = await res.text()
    soup = BeautifulSoup(text, 'lxml')

    count = soup.select('#nExerciseAfterCount')[0]['value']
    record = soup.select('#record')[0]
    done = record.select('div[class="xt_wc"]')
    exercises = record.select('.no_xt')

    if len(exercises) > 0:
        print(f'视频{name}没有习题')
        return

    if len(done) > 0:
        print(f'视频{name}的习题已完成')
        return

    tables = record.select('table')
    answer_list = []
    service = 'StudentCourseExerciseService'
    trans_name = 'addExerciseAfterAnswer'

    for table in tables:
        qid = table['index']
        ans = table['stranswer']
        answer_list.append({
            'lQuestionId': int(qid),
            'strAnswer': ans,
            'strStudentAnswer': ans,
            'bTrue': 0
        })

    data = {
        'strServiceName': service,
        'strTransName': trans_name,
        'lUserId': user_id,
        'lSchoolId': school_id,
        'lCoursewareId': int(course_id),
        'bInOrAfter': 1,
        'nExerciseAfterCount': int(count),
        'answerArrayList': answer_list
    }
    cdo_data = {"$$CDORequest$$": generate_cdo_data(data)}
    print(cdo_data)
    code = await handle_trans(cdo_data, session, service, trans_name)
    print(code)


async def refresh_video(course_id, video_name, minutes, session):
    # courseware_url = f'http://course.njcedu.com/newcourse/coursecc.htm?courseId={course_id}'
    courseware_url = f'http://course.njcedu.com/newcourse/course.htm?courseId={course_id}'
    async with session.get(courseware_url, cookies=cookies) as res:
        for cookie in res.cookies:
            cookies[cookie] = res.cookies.get(cookie).value
        text = await res.text()
    # 需要加re.S不然.不能匹配换行 需要用\s

    # 视频名字会发生改变 正则从html中找出更改变后的视频名
    name = re.findall(r"modifyRecentView\(.*?,.*?,'(.*?)',.*?\);", text)[0]

    service = 'ViewDataService'
    trans_name = 'modifyRecentView'
    data = {
        'strServiceName': service,
        'strTransName': trans_name,
        'lSchoolId': school_id,
        'lDestSchoolId': 0,
        'lUserId': user_id,
        'id': int(course_id),
        'name': name,
        'nDestTypeId': 1
    }
    cdo_data = {"$$CDORequest$$": generate_cdo_data(data)}
    code = await handle_trans(cdo_data, session, service, trans_name)
    print('申请添加视频记录成功' if code != '-1' else '申请添加视频记录失败')

    ret = re.findall("player.*?'vid': '(.*?)',\s*'siteid': '(.*?)'", text, re.S)[0]
    vid, app_id = ret[0], ret[1]

    # status = await client_time(session, vid, app_id)
    # print('上传视频进度到服务器成功' if status == 204 else '上传视频进度到服务器失败')
    print(course_id + ': ' + name)
    time.sleep(30)

    url = f'http://course.njcedu.com/Servlet/recordStudy.svl?lCourseId={course_id}&lSchoolId={school_id}&strStartTime=0'
    rounds = int(minutes / 2)
    print(f'发送{rounds}轮视频请求')
    for _ in range(rounds):
        async with session.post(url, cookies=cookies) as res:
            print(res.status, end=': ')
            print(await res.text())
    print(f'{video_name}的视频进度已经拉满')
    print('=' * 50)


async def client_time(session, vid, app_id):
    url = 'http://logger.csslcloud.net/event/vod/v1/client'
    # rid为上一次时间  et为开始时间和当前时间
    headers = {
        'Proxy-Connection': 'keep-alive',
        'Pragma': 'no-cache',
        'Cache-Control': 'no-cache',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': '*/*',
        'Origin': 'http://course.njcedu.com',
        'Referer': 'http://course.njcedu.com/',
        'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
    }
    # 首次方法
    params = {
        "ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36",
        "platform": "h5-pc", "uuid": "14233421", "rid": int(time.time() * 1000), "ver": "v1.0.7", "appver": "2.7.6",
        "business": "1001", "userid": "", "appid": app_id, "event": "play",
        "vid": vid, "nodeip": "", "retry": 0, "et": 716, "code": 200,
        "cdn": "cm15-c110-2.play.bokecc.com"
    }

    _json = json.dumps(params)

    async with session.post(url, data=_json, headers=headers) as res:
        return res.status


async def handle_trans(data, session, service, trans_name):
    url = f'http://pyp.njcedu.com/student/tc/careerPlaning/handleTrans.cdo?strServiceName={service}&strTransName={trans_name}'
    async with session.post(url, cookies=cookies, data=data) as res:
        text = await res.text()
        # print(text)
        soup = BeautifulSoup(text, 'lxml')
        code = soup.select('NF[N="nCode"]')[0]['v']
        return code


async def get_evaluation_html(a, session):
    path = re.findall(r"open\('(.*?)',", a['onclick'])[0]
    operate = a.text

    async with session.get('http://pyp.njcedu.com' + path, cookies=cookies) as res:
        if operate == '重测':
            return await res.text()

        # 不是重测则解析页面
        soup = BeautifulSoup(await res.text(), 'lxml')
        suf = soup.select('.starBtn')[0]['onclick']
        test_path = re.findall(r"open\('(.*?)'\)", suf)[0]
        async with session.get('http://pyp.njcedu.com/student/tc/careerPlaning/' + test_path, cookies=cookies) as res:
            return await res.text()


def generate_evaluation_data(html):
    soup = BeautifulSoup(html, 'lxml')
    ans = soup.select('.answer')
    if not ans:
        ans = soup.select('.picAnswer')

    evaluation_id = int(soup.select('#lEvaluationId')[0]['value'])
    username = soup.select('#strUserName')[0]['value']
    # 不要用字典因为字典中的冒号将无法除去  而请求中的字符参数是要字典中的键和值都没冒号
    answers = '{answers:['
    for ul in ans:

        lis = ul.select('li')
        index = ul['index']
        question_id = ul['questionid']
        tp = ul['type']
        options = []
        answer = []
        check_options = []
        check_answers = []
        # 出现两次的元素都删掉
        hm = {}  # hash
        # 保存下标
        for li in lis:
            options.append(li['option'])  # 填充选项
            answer.append("0")  # 填充答案
            hm[li['value']] = hm.get(li['value'], 0) + 1

        vs = [k for k in hm if hm[k] == 1]
        better_opts = [li for li in lis if li['value'] in vs]

        # 单选题
        if tp == '0':
            try:
                r = int(len(better_opts) * random.random())
                check_options.append(better_opts[r]['option'])
                check_answers.append(better_opts[r]['value'])
                answer[r] = better_opts[r]['value']
            except IndexError:  # 选项分值都相同时 随机一个
                r = int(len(lis) * random.random())
                check_options.append(lis[r]['option'])
                check_answers.append(lis[r]['value'])
                answer[r] = lis[r]['value']

        elif tp == '1':  # 多选题
            opts = []
            multiple_choice(0, [], len(lis), opts)
            check_options = opts[int(random.random() * len(opts))]

        str_dict = "{" + f'index:&quot;{index}&quot;,lQuestionId:&quot;{question_id}&quot;,type:&quot;{tp}&quot;,options:' \
                         f'&quot;{",".join(options)}&quot;,answer:&quot;{",".join(answer)}&quot;,checkOptions:&quot;' \
                         f'{",".join(check_options)}&quot;,checkAnswers:&quot;{",".join(check_answers)}&quot;' + "},"
        answers += str_dict

    answers = answers[:-1] + "]}"

    data = {
        'strServiceName': 'EvalutionService',
        'strTransName': 'addEvaluationResult',
        'lSchoolId': school_id,
        'lUserId': user_id,
        'strUserName': username,
        'lEvaluationId': evaluation_id,
        'strAnswer': answers,
        'startTime': int(time.time() * 1000),
        'strToken': ''
    }
    return {"$$CDORequest$$": generate_cdo_data(data)}


def generate_cdo_data(data):
    xml = '<CDO>'

    def base_type_tag(k, v):
        if kt == str:
            return f'<STRF N="{k}" V="{v}"/>'
        elif kt == int:
            return f'<LF N="{k}" V="{v}"/>'

    for k in data:
        # 字典内会自动加上冒号 所以answers用字符串
        kt = type(data[k])
        # 字典则遍历然后键用"包 值用&quot;
        if kt == list:
            xml += f'<CDOAF N="{k}">'
            for item in data[k]:
                xml += generate_cdo_data(item)
            xml += '</CDOAF>'
        else:
            xml += base_type_tag(k, data[k])
        # xml += f'<{"STRF" if kt == str else "LF"} N="{k}" V="{data[k]}"/>'
    xml += '</CDO>'
    return xml


async def do_evaluation(a, session):
    html = await get_evaluation_html(a, session)
    data = generate_evaluation_data(html)
    code = await handle_trans(data, session, 'EvalutionService', 'addEvaluationResult')
    if code != '-1':
        print("评测提交成功")
    else:
        print('请求出错，请尝试调低并发数重新下载！！')


def multiple_choice(index, cur, size, opts):
    if cur.__len__() > 1:
        # list生成一个数组
        opts.append(list(cur))

    while index < size:
        # chr将数字转成对应ascii字符   ord反之
        cur.append(chr(65 + index))
        multiple_choice(index + 1, cur, size, opts)
        cur.pop(-1)
        index += 1


if __name__ == '__main__':
    cookies = {}
    school_id = ''
    user_id = ''
    login()
    # print(cookies)
    ts = get_tasks()
    asyncio.run(resolve_task(ts))
    # 近期学习任务
    # res = requests.get('http://school.njcedu.com/api/student/teachplan/recentLearningTasks', cookies=cookies)
    # 学习任务

    # 需要携带schoolToken
    # res = requests.get('http://pyp.njcedu.com/student/prese/teachplan/listdetail.htm?id=6970000018', cookies=cookies)
    # print(res.text)
