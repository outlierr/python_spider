# coding=utf-8
import base64
import json
import logging
import math
import re
import time
from hashlib import md5
from urllib import parse

import ddddocr
import pika
from PIL import UnidentifiedImageError
from bs4 import BeautifulSoup
from fontTools.ttLib import TTFont
from lxml import etree
from requests import utils

from util import *

ocr = ddddocr.DdddOcr(old=True, show_ad=False)
# requests库是会识别302并自动跟随跳转的

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'

RATE = 1

# 连接amqp
credentials = pika.PlainCredentials(username='root', password='qq123321')
conn = pika.BlockingConnection(pika.ConnectionParameters(host="172.20.45.222", credentials=credentials))
if not conn.is_open:
    raise RuntimeError("连接 RabbitMQ 失败")

channel = conn.channel()
exchange = "video.exchange"
queue = "video.queue"
# 绑定接收交换机
channel.exchange_declare(exchange=exchange, durable=True)
queue_res = channel.queue_declare(queue=queue)
channel.queue_bind(exchange=exchange, queue=queue)

dead_exchange = "video.delay.exchange"
dead_queue = "video.delay.queue"
# 延迟队列参数
arguments = {
    "x-message-ttl": int((60 / RATE) * 1000),  # 延迟(保留)时间（毫秒）
    "x-dead-letter-exchange": exchange,  # 没被消费直至延迟结束后指向的交换机（死信收容交换机）
    "x-dead-letter-routing-key": queue,  # 创建的队列的 routing_key 如果没有指定就以队列名命名
}
# 绑定死信队列
channel.exchange_declare(exchange=dead_exchange, durable=True)
dead_queue_res = channel.queue_declare(queue=dead_queue, durable=True, arguments=arguments)
channel.queue_bind(exchange=dead_exchange, queue=dead_queue)

account_list = [
    {
        "username": "17336072110",
        "password": "qq888888",
        "target_courses": ['软件测试']
    }
]


class ConsumerCallback:
    def __init__(self, count=0):
        self.count = count

    def __call__(self, *args, **kwargs):
        ch, m, props, body = args[0: 4]
        data = json.loads(body.decode())
        data['params']['enc'] = encode_enc(data['params']['clazzId'], data['params']['playingTime'],
                                           data['params']['duration'], data['params']['objectId'],
                                           data['params']['jobid'], data['params']['userid'])

        def add_log_request(sess):
            res = sess.get(data['url'], params=data["params"])
            print(check_and_get_text(res, sess))

        with requests.session() as ss:
            ss.trust_env = False
            ss.headers['User-Agent'] = USER_AGENT
            utils.add_dict_to_cookiejar(ss.cookies, data['cookies'])

            if data['params']['playingTime'] < data['params']['duration']:
                print(
                    f"{data['name']} --> 添加一分钟的视频进度, 当前视频进度:{data['params']['playingTime']}, 视频总进度:{data['params']['duration']}")
                add_log_request(ss)
                data['params']['playingTime'] += 60
                if data['params']['playingTime'] + 60 > data['params']['duration']:
                    data['params']['playingTime'] = data['params']['duration']
                # 生产下一条消息
                ch.basic_publish(exchange=dead_exchange, routing_key=dead_queue, body=json.dumps(data).encode(),
                                 properties=pika.BasicProperties(delivery_mode=2))
            else:
                add_log_request(ss)
                self.count -= 1
                print(f"{data['name']}已完成, 当前还剩下{self.count}个视频未完成")
                if self.count == 0:
                    ch.basic_ack(delivery_tag=m.delivery_tag)
                    channel.stop_consuming()
                    return

        # 确认消息被消费
        ch.basic_ack(delivery_tag=m.delivery_tag)


def check_and_get_text(res, sess):
    while res.status_code == 202:  # 需要验证码
        res = sess.get(
            f"https://mooc1.chaoxing.com/processVerifyPng.ac?t={math.floor(2147483647 * random.random())}")  # 获取验证码图片
        try:
            code = ocr.classification(res.content)
        except UnidentifiedImageError:
            res.status_code = 202
            continue
        res = sess.get("https://mooc1.chaoxing.com/html/processVerify.ac", params={"app": 0, "ucode": code})
        print("操作异常，输入验证码:" + code)
        if res.status_code != 200:
            print("验证码错误")
    return res.text


cb = ConsumerCallback(dead_queue_res.method.message_count + queue_res.method.message_count)

channel.basic_consume(queue, cb)


def encode_enc(clazzid: str, play_time: int, duration: int, objectId: str, jobid: str, userid: str):
    # duration * 1000 将当前秒数直接定位到结束 秒刷
    import hashlib
    data = "[{0}][{1}][{2}][{3}][{4}][{5}][{6}][0_{7}]".format(clazzid, userid, jobid, objectId, play_time * 1000,
                                                               "d_yHJ!$pdA~5", duration * 1000, duration)
    return hashlib.md5(data.encode()).hexdigest()


class XuexiTong:
    def __init__(self, username, password, target_courses=None, rate=2):
        self.ss = requests.session()
        self.ss.trust_env = False
        self.ss.headers['User-Agent'] = USER_AGENT
        self.username = username
        self.password = password
        self.target_courses = target_courses
        self.rate = rate

    def login(self):
        url = 'https://passport2.chaoxing.com/fanyalogin'

        global cookies  # 更新超参数
        data = {
            'uname': '5KvJ0EsTnYb7trsLdnWbNg==',
            'password': 'A6sOc5hc/UFJsGsYP3iuFA==',
            'fid': -1,
            'refer': 'http%3A%2F%2Fi.chaoxing.com',
            't': 'true',
            'validate': '',
            'forbidother': 0,
        }
        res = self.ss.request('POST', url, data=data)
        print(res.json())
        print('当前是否登录:', res.json()['status'])

    def get_courses_html(self):
        url = 'https://mooc2-ans.chaoxing.com/visit/courses/list'
        res = self.ss.get(url)
        return res.text

    # 二版本人脸识别
    def upload_info(self, clazz_id, course_id, knowledge_id, uuid, qrcenc):
        url = 'https://mooc1-api.chaoxing.com/knowledge/uploadInfo'
        data = {
            'clazzId': clazz_id,
            'courseId': course_id,
            'knowledgeId': knowledge_id,
            'objectId': md5(str(time.time()).encode()).hexdigest(),
            'uuid': uuid,
            'qrcEnc': qrcenc
        }
        res = self.ss.post(url, data=data)
        return res.json()['status']

    def get_all_course(self):
        html_txt = self.get_courses_html()
        # print(html_txt)
        course_list = {}
        soup = BeautifulSoup(html_txt, 'lxml')
        li_list = soup.select('.course')
        # print(len(li_list))  课程数量
        # 当前课程有
        for li in li_list:
            not_open_course = li.select(".not-open-tip")
            if len(not_open_course) > 0:
                continue
            # class_name = class_item.xpath("./div[2]/h3/a/@title")[0]
            class_name = li.select('.course-name')[0]['title']
            # 等待开课的课程由于尚未对应链接，所以缺少a标签。
            href = li.select('.color1')[0]['href']
            gs = re.findall('.*?=(.*?)&', href)
            # course_list[class_name] = course_url_redirect(href).replace("pageHeader=-1", "pageHeader=1")
            # 章节页面url
            course_list[
                class_name] = f'https://mooc2-ans.chaoxing.com/mycourse/studentcourse?courseid={gs[0]}&clazzid={gs[1]}&cpi={gs[2]}&ut=s'
        print(course_list)
        return course_list

    def course_url_redirect(self, url: str):  # 限定返回值
        # 这里判断出重定向方法是:打开一个新窗口 复制url到浏览器 然后在network里看
        res = self.ss.request("GET", url, allow_redirects=False)
        # print(res.history)  # [<Response [302]>, <Response [302]>] 这里进行了两次重定向 第一次跑向了目标url
        # 但是后面服务器又将请求重定向到登录页面 所以只能进行手动重定向
        real_url = res.headers['Location']
        return real_url

    def resolve_course(self, url: str, _cpi: str):
        global name
        print(url)
        res = self.ss.request('GET', url)
        base = 'https://mooc1.chaoxing.com'
        soup = BeautifulSoup(res.text, 'lxml')
        old_enc = re.findall(r'var enc = "(.*?)"', res.text)[0]
        # print(res.text)
        units = soup.select('.chapter_unit')
        _list = []
        flag = False
        for unit in units:
            items = unit.select('.chapter_item')
            # url = 'https://mooc1.chaoxing.com/mycourse/studentstudy?chapterId=492264906&courseId=221291128&clazzid=47768612&enc=4539eb8cbead9b74891d48a66abb4fd3&mooc2=1&cpi=156489596&openc=3c52185419d68210f81ccd47ea151183'
            for item in items:
                try:
                    name = item['title'] if item.has_attr('title') else item.select('.catalog_name')[0].span['title']
                except:
                    print(1)

                if len(item.select('.catalog_task')) == 0:
                    continue
                rank = item.select('.catalog_sbar')[0].text

                to_old_func = item['onclick']
                gs = re.findall(r'(\d+).', to_old_func)
                course_id = gs[0]
                chapter_id = gs[1]
                clazz_id = gs[2]
                # 实测没用enc也可以刷
                href = f'https://mooc1.chaoxing.com/mycourse/studentstudy?chapterId={chapter_id}&courseId={course_id}&clazzid={clazz_id}&enc={old_enc}'

                if 'icon_yiwanc' in item.select('.catalog_task')[0].div['class']:
                    # 已经完成 跳过
                    continue
                if 'catalog_tishi56' in item.select('.catalog_task')[0].div['class']:
                    self.do_mission('blank', {rank + name: href}, _cpi)
                elif 'catalog_jindu' in item.select('.catalog_task')[0].div['class']:
                    self.do_mission('orange', {rank + name: href}, _cpi)

    def access_mission(self, item):
        for key in item:
            print(f'进入章节点: {key} 链接:{item[key]}')
            # 保存后端生成href里面的参数
            query_data = {}
            result = parse.urlparse(item[key])
            params = parse.parse_qs(result.query)
            for p in params:
                query_data[p] = params[p][0]
            try:
                # 没有clazz 则说明该课程已经结课 或者还未开始
                self.click_mission(query_data)
            except KeyError:
                print('-----------clazz_id为空, 该课程已经结课或者还未开课-----------')
                return
            print(f'完成普通章节点: {key}')

    def working_mission(self, item, class_cpi):
        for key in item:
            print(f'进入章节点: {key} 链接:{item[key]}')

            query_data = {}
            result = parse.urlparse(item[key])  # 解析yrl
            params = parse.parse_qs(result.query)  # 取出任务页面参数
            for p in params:
                query_data[p] = params[p][0]
            # print(chapter_data) 分析出标签href内的参数
            data = {
                'courseId': query_data['courseId'],
                'clazzid': query_data['clazzid'],
                'chapterId': query_data['chapterId'],
                'cpi': class_cpi,
                'verificationcode': ''
            }
            res = self.ss.post('https://mooc1.chaoxing.com/mycourse/studentstudyAjax', data=data)
            need_face = False
            try:
                soup = BeautifulSoup(res.text, 'lxml')
                uuid = soup.select('#uuid')[0]['value']
                qrc_enc = soup.select('#qrcEnc')[0]['value']
                need_face = True
            except Exception as e:
                # 进入这里说明不需要人脸识别
                pass
            if need_face:
                if not self.upload_info(query_data['clazzid'], query_data['courseId'], query_data['chapterId'], uuid,
                                        qrc_enc):
                    raise RuntimeError('人脸识别失败')
                print('=' * 30 + '通过人脸识别' + '=' * 30)

            panels = re.findall('changeDisplayContent', res.text)
            num = len(panels) if len(panels) > 0 else 1  # 顶上没有面板情况 只有一个任务
            print(f'该章节点共有{num}个panel')
            for i in range(num):  # 视频右边还有一个章节检查panel
                try:
                    k_token, user_id, report_url, item_json, refer_v = self.mission_attachment_info(query_data,
                                                                                                    class_cpi, i)
                except Exception as e:
                    logging.exception(e)
                # print(item_json)
                try:
                    if not item_json:
                        continue
                except:
                    continue
                self.resolve_mission(item_json, report_url, user_id, query_data, class_cpi, k_token, refer_v)
            print(f'完成任务章节点: {key}')

    def do_mission(self, _type, item, class_cpi):
        print('开始自动完成章节下的任务....')
        # 不需要做任务只需要点进去就算完成

        if _type == 'blank':
            self.access_mission(item)
        elif _type == 'orange':
            self.working_mission(item, class_cpi)

    def resolve_mission(self, item_json, report_url, user_id, query_data, class_cpi, k_token, refer_v):
        print(f"当前这个章节点共有{len(item_json)}个任务")
        for item in item_json:  # 可能有多个任务
            # print(item)  # 打印这个任务点json信息
            media_prop = item['property']  # 保存视频任务的属性json信息
            if item.get('isPassed') and item['isPassed']:
                if item.get('type'):
                    print(f'这个{item["type"]}任务已经完成了')
                else:
                    print('这个exercise任务已经完成了')
                continue

            try:
                item_type = item['type'] if item.get('type') else media_prop['type']
            except KeyError:
                # 都没有type 则不用处理
                continue
            try:
                if item_type == 'video':  # 刷视频
                    # print('跳过视频任务')
                    # continue
                    self.finish_video(item, media_prop, report_url, user_id, query_data, refer_v)
                elif item_type == 'read':  # 阅读
                    job_id = item['jobid']
                    j_token = item['jtoken']
                    print('处理阅读任务')
                    self.finish_reading(job_id, j_token, query_data)
                elif item_type == 'workid':  # 答题
                    self.finish_exercise(query_data, item, class_cpi, k_token)
                elif item_type == '.mp3':
                    print('处理音频任务')
                    self.finish_audio(media_prop['jobid'], media_prop['objectid'], query_data['clazzid'], user_id,
                                      item['otherInfo'])
                elif item_type == 'document':  # pdf
                    print('处理pdf任务')
                    self.finish_document(item, query_data, media_prop)  # 多个任务ppt可以不用管
            except Exception as e:
                logging.exception(e)

    def mission_attachment_info(self, query_data, class_cpi, num):
        # num是第几个panel
        media_url = f'https://mooc1.chaoxing.com/knowledge/cards?knowledgeid={query_data["chapterId"]}&courseid=' \
                    f'{query_data["courseId"]}&clazzid={query_data["clazzid"]}&num={num}&ut=s&cpi={class_cpi}&v' \
                    f'=20160407-1'
        # print(media_url)
        res = self.ss.request('GET', url=media_url)
        text = check_and_get_text(res, self.ss)
        html = etree.HTML(text)
        try:
            video_refer_v = re.match(".*parse.js\?v=(\d+-\d+-\d+)", res.text, re.S).group(1)
        except:
            video_refer_v = "2021-0618-1850"
            pass
        script = html.xpath("//script[1]/text()")[0]
        # 这里的正则表示分组后面是,defaults
        pattern = re.compile(r'attachments":([\s\S]*),"defaults"')
        # 从js文本中取出附件信息
        result = re.findall(pattern, script)  # 任务信息
        # f_script = html.xpath("/html/head/script[3]/text()")[0]
        # _from = re.findall('var _from = \'(.*?)\'', f_script)[0]
        if result:
            result = result[0]
        else:
            return None, None, None, None, None
        # findall和search的区别：search返回一个对象里面包括元组   findall返回数组
        report_url = re.findall(r'reportUrl":([\s\S]*),"chapterCapture"', script)[0]
        # script文本里的json是没有格式化不用考虑字段换行
        user_id = re.findall(r'"userid":"([\s\S]*)","reportTimeInterval"', script)[0]
        k_token = re.findall(r'"ktoken":"([\s\S]*)","mtEnc"', script)[0]

        report_url = report_url.replace("\"", "")  # 更新视频报道地址 文件也一样
        item_json = json.loads(re.findall(r"\[.*]", result)[0])
        return k_token, user_id, report_url, item_json, video_refer_v

    def finish_reading(self, job_id, j_token, query_data):
        url = f'https://mooc1.chaoxing.com/ananas/job/readv2?jobid={job_id}&knowledgeid={query_data["chapterId"]}' \
              f'&courseid={query_data["courseId"]}&clazzid={query_data["clazzid"]}&jtoken={j_token}' \
              f'&_dc={str(int(time.time() * 1000))}'
        res = self.ss.get(url)
        print(res.text)

    def finish_audio(self, jobid, objectid, clazzId, userid, other_info):
        # 获取音频时长
        url = f'https://mooc1.chaoxing.com/ananas/status/{objectid}'
        res = self.ss.get(url)
        _json = res.json()
        dur = _json['duration']
        token = _json['dtoken']
        ff = f'[{clazzId}][{userid}][{jobid}][{objectid}][{dur * 1000}][d_yHJ!$pdA~5][{dur * 1000}][0_{dur}]'
        enc = md5(ff.encode("utf-8")).hexdigest()
        params = (
            ('clazzId', clazzId),
            ('playingTime', dur),  # 1
            ('duration', dur),  # 1
            ('objectId', objectid),
            ('otherInfo', other_info),
            ('jobid', jobid),
            ('userid', userid),
            ('isdrag', '4'),
            ('view', 'pc'),
            ('enc', enc),  # 必须
            ('dtype', 'Audio')
        )
        res = self.ss.get(f'https://mooc1.chaoxing.com/multimedia/log/a/162120043/{token}', params=params)
        print(res.text)

    def finish_exercise(self, chapter, item, class_cpi, k_token):
        # data使用字符串的形式的时候 需要指定Content-Type为application/x-www-form-urlencoded;
        html = self.get_exercise(chapter, item, class_cpi, k_token)
        soup = BeautifulSoup(html, "lxml")
        top_div = soup.select(".ZyTop")[0]
        if "已完成" in top_div.text:
            return
        font_base64 = re.match(".*base64,(.*?)'", html, re.S).group(1)
        font_stream = base64.b64decode(font_base64)
        with open("./enc_font.ttf", 'wb') as f:
            f.write(font_stream)
        font = TTFont("./enc_font.ttf")
        font_json = {}
        for k in font.getBestCmap():
            ch = chr(k)
            img, img_io = uni_2_png_stream(ch, "./enc_font.ttf", 100)
            img_io.seek(0)
            dec_val = ocr.classification(img_io.read())
            font_json[ch] = dec_val

        enc_els = soup.select(".font-cxsecret")
        for el in enc_els:
            text = el.text
            for ch in text:
                if font_json.get(ch):
                    text = text.replace(ch, font_json[ch])
            # 替换 innerText 会使 soup 的结构树被更改 替换 nbsp
            el.string = text.replace(u'\xa0', "")

        # html re.sub(, lambda m: for w in m.group(1): , re.S)
        try:
            form_data = self.generate_form_data(soup)
        except IndexError:
            return

        # print(type(form_data)) 变成了json字符串
        # token未知 url没问题
        url = f'https://mooc1.chaoxing.com/work/addStudentWorkNewWeb?_classId={chapter["clazzid"]}&courseid=' \
              f'{chapter["courseId"]}&token=&totalQuestionNum=' \
              f'{form_data["totalQuestionNum"]}&ua=pc&formType=post&saveStatus=1&pos=&version=1'
        res = self.ss.post(url=url, data=form_data)
        print(res.text)

    def generate_form_data(self, soup):
        params_ips = soup.select('#form1 > input')
        form_data = {}
        for ip in params_ips:
            if ip.has_attr('name'):
                if ip.has_attr('value'):
                    form_data[ip['name']] = ip['value']
                else:
                    form_data[ip['name']] = ''

        questions = soup.select('.TiMu')
        answerwqbid = ''
        # 所有题目的选择题先拿出来
        ul_idx, ul = 0, soup.select('.Zy_ulTop')
        for q in questions:
            q_div = q.select('div[class="Zy_TItle clearfix"]')[0]
            text_type = re.findall(r'【(.+)】', q_div.select('div')[0].next_element)[0]
            rank = re.sub("\s", "", q_div.select('i')[0].text)
            q_desc = q_div.select('div')[0].text.split('】')
            q_title = re.sub("\s", "", q_desc[1])
            print(f'【{text_type}】{rank}. {q_title}')
            # 获取答案类型元素
            div = q.select('div.clearfix')[2]
            # 这个题目是嵌套的 所以要找存在于儿子节点
            ans_type = div.findChildren('input', recursive=False)
            ans_type = ans_type[ans_type.__len__() - 1]
            type_id = int(ans_type['value'])
            # 获取答案参数
            ans_code = ans_type["name"].replace("type", "")
            # 添加答案类型参数
            form_data[ans_type['name']] = type_id  # 数字都会被转成字符串
            code = re.findall(r'\d+', ans_code)[0]
            # 所有答案
            try:
                data = get_answer(q_title, type_id)
            except:
                data = {'code': -1}
            time.sleep(0.5)
            # print(data) 答案请求
            answerwqbid += code + ','
            ans = ''
            if data['code'] == -1:
                print("找不到答案")
                # 这里要跳出 提前加
                form_data[ans_code] = random_ans(type_id)
                continue
            if type_id == 0:
                opts = ul[ul_idx].select('li')
                opt_dict = {}
                for i in range(opts.__len__()):
                    try:
                        p = opts[i].select('a p')[0]
                    except:
                        p = opts[i].select('a')[0]
                    try:
                        try:
                            span = p.select('span')[0].next_element
                            span = re.sub(r'^\s*|\s*$', '', span).replace('，', ',').replace(r'\xa0\xa0', ' ').replace(
                                ' ',
                                ' ')
                            opt_dict[span] = chr(65 + i)
                        except:
                            p = re.sub(r'^\s*|\s*$', '', p.next_element).replace('，', ',').replace(r'\xa0\xa0',
                                                                                                   ' ').replace(' ',
                                                                                                                ' ')
                            opt_dict[p] = chr(65 + i)
                    except:
                        continue
                if opt_dict.get(data['data']):
                    ans = opt_dict[data['data']]
                else:  # 没有就乱选
                    ans = random_ans(type_id)
                print('选项为:', opt_dict)
            elif type_id == 1:  # 多选题
                opts = q.select('.Zy_ulTop > li')
                data = data['data'].split('#')
                opt_dict = {}
                # 将所有选项收集
                for i in range(len(opts)):
                    a = opts[i].select('a')[0]
                    try:
                        try:
                            # next_element不会把后面的文本一起收集了
                            p = re.sub(r'^\s*|\s*$', '', a.select('p')[0].next_element).replace('，', ',').replace(
                                r'\xa0\xa0', ' ').replace(' ', ' ')
                            opt_dict[p] = chr(65 + i)
                        except:
                            a = re.sub(r'^\s*|\s*$', '', a.next_element).replace('，', ',').replace(r'\xa0\xa0',
                                                                                                   ' ').replace(' ',
                                                                                                                ' ')
                            opt_dict[a] = chr(65 + i)
                    except:
                        print(f'找不到选项{chr(65 + i)}')
                        continue
                for a in data:
                    if opt_dict.get(a):
                        ans += opt_dict[a]
                print('选项为:', opt_dict)
            elif type_id == 3:  # 判断题
                ans = 'true' if data['data'] == '正确' else 'false'
            elif type_id in [2, 4, 5, 6]:  # 填空类
                ans = '<p>' + data['data'] + '</p>'  # 编码成中文
            ul_idx += 1
            print('正确答案:', ans)
            form_data[ans_code] = ans
        form_data['answerwqbid'] = answerwqbid
        return form_data

    def get_exercise(self, chapter, item, class_cpi, k_token):
        # 第一次请求
        job_id = item["jobid"]
        knowledge_id = chapter["chapterId"]
        course_id = chapter['courseId']
        clazz_id = chapter["clazzid"]
        enc = item['enc']
        work_id = job_id.replace('work-', '')
        # 这个为常量
        utenc = '9faaf1b9f535d52351975b931f9c0fe8'
        url = f'https://mooc1.chaoxing.com/api/work?api=1&workId={work_id}&jobid={job_id}&needRedirect=true&knowledgeid={knowledge_id}&ktoken={k_token}&cpi={class_cpi}&ut=s&clazzId={clazz_id}&type=&enc={enc}&utenc={utenc}&courseid={course_id}'
        # 不让学习通跳转到登录页面
        res = self.ss.get(url)
        # print('两次重定向后的请求', res.url)
        return res.text

    def finish_document(self, item, chapter, media_prop):  # item为cards里的json信息  chapter为url上面的参数
        job_id = media_prop["_jobid"]  # 没有这个jobid则说明该文档和其他任务一起提交
        jtoken = item['jtoken']
        knowledge_id = chapter["chapterId"]
        course_id = chapter['courseId']
        clazz_id = chapter["clazzid"]
        url = f'https://mooc1.chaoxing.com/ananas/job/document?jobid={job_id}&knowledgeid={knowledge_id}&courseid=' \
              f'{course_id}&clazzid={clazz_id}&jtoken={jtoken}&_dc{int(time.time() * 1000)}'
        self.ss.request('GET', url=url)

    # item为视频任务信息
    def finish_video(self, item, video_prop, report_url, user_id, chapter, refer_v):
        object_id = item["objectId"]
        other_info = item["otherInfo"]
        job_id = video_prop["_jobid"]
        name = video_prop['name']
        #  查看视频数据
        url = f"https://mooc1.chaoxing.com/ananas/status/{object_id}?k=&flag=normal&_dc={int(time.time() * 1000)}"
        referer = f"https://mooc1.chaoxing.com/ananas/modules/video/index.html?v={refer_v}"
        res = self.ss.get(url=url, headers={"Referer": referer})
        print(res.text)
        video_data = res.json()
        duration = video_data.get('duration')
        dtoken = video_data.get('dtoken')
        params = {
            "clazzId": chapter["clazzid"],
            "playingTime": 0,
            "duration": duration,
            "clipTime": "0_" + str(duration),
            "objectId": object_id,
            "otherInfo": other_info,
            "jobid": job_id,
            "userid": user_id,
            "isdrag": 4,
            "view": "pc",
            "rt": "0.9",
            "dtype": "Video",
        }
        url = report_url + "/" + dtoken
        # print('------报道地址', url)
        # res = self.ss.request('GET', url=url)  # 发送视频记录
        body = {
            "url": url,
            "cookies": self.ss.cookies.get_dict(),
            "params": params,
            "name": name,
            "Referer": referer
        }
        print("生产一条视频 log 消息")
        # 生产一条消息 #properties=pika.BasicProperties(delivery_mode=2)  将消息永久化（服务重启后还在）
        channel.basic_publish(exchange=dead_exchange, routing_key=dead_queue, body=json.dumps(body).encode(),
                              properties=pika.BasicProperties(delivery_mode=2))
        cb.count += 1

    # 点进去就算完成任务
    def click_mission(self, chapter_data):
        if not chapter_data['clazzid']:
            raise Exception('clazz_id为空, 该课程已经结课或者还未开课')
        data = {
            'courseId': chapter_data['courseId'],
            'clazzid': chapter_data['clazzid'],
            'chapterId': chapter_data['chapterId'],
            'verificationcode': '',
            'cpi': 0
        }
        url = 'https://mooc1.chaoxing.com/mycourse/studentstudyAjax'
        res = self.ss.request('POST', url, data=data)
        print(res)

    def run(self):
        self.login()
        courses = self.get_all_course()
        for course in courses:
            if self.target_courses and course not in self.target_courses:
                continue
            print(f'进入课程"{course}"')
            cpi = re.search('cpi=(.*)&', courses[course]).group(1)
            self.resolve_course(courses[course], cpi)
            print("——————————————————————————————————————————————————————————")


# script = html.xpath("//script[1]/text()")[0] 就是人脸
if __name__ == '__main__':
    for account in account_list:
        XuexiTong(account['username'], account['password'], account['target_courses']).run()
    channel.start_consuming()
    # 一次性消费所有队列中的消息
