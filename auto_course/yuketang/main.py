import math
from threading import Timer
import time
from api import *
from entry import *

# 全局变量
session = '3tumihsjyvyjkx2983lru3skd77nn9h6'  # 14天过期
token = 'ri7ALmktjrIotesdeyEgB524AGSX6HYf'
uv_id = '2741'


def all_courses():
    data = get_courses_info(uv_id, session)
    courses = []

    for course in data['product_list']:
        courses.append(Course(course))
    return courses


leaf_type = {
    0: 'video',
    3: 'ppt',
    6: 'choice'
}


def generate_choice(index, cur, size, opts):
    if cur.__len__() > 1:
        # list生成一个数组
        opts.append(list(cur))

    while index < size:
        # chr将数字转成对应ascii字符   ord反之
        cur.append(chr(65 + index))
        generate_choice(index + 1, cur, size, opts)
        cur.pop(-1)
        index += 1


def initial_heart_data(heart_data, leaf):
    ets = ['loadstart', 'loadeddata']
    heart_data_package = []
    for et in ets:
        pg = execjs.eval('Math.floor(1048576 * (1 + Math.random())).toString(36)')
        heart_data['pg'] = f"{leaf.id}_{pg}"
        heart_data['sq'] += 1
        # heart_data['cp'] += step 初始化进度条为0
        heart_data['et'] = et
        heart_data_package.append(dict(heart_data))
    return heart_data_package


def generate_heart_data(heart_data, leaf, step):
    heart_data_package = []
    for i in range(6):
        # 这个后端的目的应该是拿到字符串 解码后在一定数字范围
        pg = execjs.eval('Math.floor(1048576 * (1 + Math.random())).toString(36)')
        heart_data['pg'] = f"{leaf.id}_{pg}"
        heart_data['sq'] += 1
        heart_data['cp'] += step
        heart_data['ts'] = str(int(time.time() * 1000))
        heart_data_package.append(dict(heart_data))
    return heart_data_package


def do_chapter_homework():
    courses = all_courses()
    now = int(time.time() * 1000)
    for course in courses:
        if now >= course.class_end:
            print(f'"{course.course_name}"已经结课')
            continue
        if now < course.class_start:
            print(f'"{course.course_name}"还未开课')
            continue
        chapters = []  # 保存没问课程的章节
        data = get_course_chapters(course.classroom_id, course.course_sign, uv_id, session)
        course_chapter = data['course_chapter']

        if not course_chapter:
            print('"{}"这门课还没有内容'.format(course.course_name))
            continue
        print('进入"{}"课程...'.format(course.course_name))
        for cc in course_chapter:
            leaves = []
            chapter = Chapter(cc)
            for section in cc['section_leaf_list']:
                # 如果这个章节是个列表
                if section.get('leaf_list'):
                    for l in section['leaf_list']:
                        leaves.append(Leaf(l))
                else:
                    leaves.append(Leaf(section))
            chapter.leaves = leaves
            chapters.append(chapter)
            # 只显示打开过的
        schedule = get_chapter_schedule(course.classroom_id, course.course_sign, uv_id, session)
        # id然后带对象的都是作业 浮点数为完成度 1为完成
        leaf_schedules = schedule['leaf_schedules']
        # print(leaf_schedules)
        for c in chapters:
            print(f'当前的章节为: {c.name}')
            for leaf in c.leaves:
                entered = leaf_schedules.get(str(leaf.id))
                # 将已经完成的任务跳过
                if entered and entered == 1:
                    print(f'\t\t    {leaf.name}已经完成')
                    continue
                    # 完成但不一定答题答对了
                # if type(entered) == dict and if entered['total'] == entered['done']:
                # 最后一门课这里没有
                data = chapter_leaf_info(session, course.course_sign, course.classroom_id, leaf.id, uv_id)
                uid = data['user_id']

                if not data:
                    break
                content = data['content_info']  # 获取章节的内容信息

                if content.get('media'):  # 是视频
                    # print(data)
                    media = content['media']
                    print("video文件名: " + media['name'])

                    data = get_video_process_info(session, course.course_id, uid, course.classroom_id, media['type'],
                                                  leaf.id)
                    # heartbeat(session, [])

                    video_length = 0
                    tp = 0
                    # 倍速
                    sp = 2
                    # 一条数据5秒
                    step = sp * 5
                    heart_data = {
                        "c": str(course.course_id),
                        "cc": media['ccid'],
                        "classroomid": str(course.classroom_id),
                        "cp": tp,
                        "d": video_length,  # 没有观看记录的时候为0
                        "et": "heartbeat",
                        "fp": 0,
                        "i": 5,
                        "lob": "cloud4",
                        "n": "sjy-cdn.xuetangx.com",
                        "p": "web",
                        "pg": "",
                        "skuid": course.sku_id,
                        "sp": sp,  # 视频倍数
                        "sq": 0,
                        "t": media['type'],
                        "tp": tp,
                        "ts": str(int(time.time() * 1000)),
                        "u": uid,
                        "uip": "",
                        "v": leaf.id,
                    }
                    # 检查是否有观看记录 如果没有则先送初始化heartbeat  然后再更新数据
                    if data.get(str(leaf.id)):
                        media_info = data[str(leaf.id)]

                    else:  # 发送初始化
                        print('该视频还没观看记录,发送请求初始化数据')
                        heartbeat(session, initial_heart_data(heart_data, leaf, step))
                        data = get_video_process_info(session, course.course_id, uid, course.classroom_id,
                                                      media['type'], leaf.id)
                        media_info = data[str(leaf.id)]

                    video_length = int(media_info['video_length'])
                    tp = int(media_info['last_point'])
                    # 有记录刷新数据
                    heart_data['tp'] = tp
                    heart_data['cp'] = tp
                    heart_data['d'] = video_length

                    while True:
                        # 发一次
                        heart_data_package = generate_heart_data(heart_data, leaf, step)
                        # print(heart_data_package)
                        heartbeat(session, heart_data_package)
                        data = get_video_process_info(session, course.course_id, uid, course.classroom_id,
                                                      media['type'],
                                                      leaf.id)
                        media_info = data[str(leaf.id)]
                        # 查看是否刷新了
                        print(media_info)
                        if media_info['completed'] == 1:
                            print(f'视频: {media["name"]}已经完成')
                            break
                        time.sleep(30)

                else:  # 有leaf_type_id则是作业
                    exercise = get_exercise_list(session, content['leaf_type_id'])
                    time.sleep(1)
                    problems = exercise['problems']
                    # print(leaf.name) 打印当前章节名字
                    for problem in problems:
                        content = problem['content']
                        body = content['Body']  # 题目内容
                        # 通过发现内容主要是被span所包裹 则正则搜索出span标签的内容
                        pat = r'<span.*?>(.+?)</span>'
                        title = ''.join(re.findall(pat, body))
                        title = re.sub('&nbsp;', ' ', title)
                        TypeText = content['TypeText']
                        options = content['Options']  # 选项
                        user = problem['user']
                        # print(f'题目:{title}')
                        # 已经正确或者没有答题机会 跳过 答题正确的user里才会有is_right
                        is_right = user.get('is_right')
                        # 无限次是-1
                        if is_right or user['count'] == user['my_count']:
                            # print(title)
                            continue
                            # 如果是单选题 # 穷举解答
                        size = options.__len__()
                        # 打印题型
                        print(TypeText, end=': ')
                        # 不管次数 直接蒙
                        if TypeText == '判断题':  # 判断题单独做
                            b = ['false', 'true']
                            for i in range(2):
                                json = answer_problem(session, token, course.classroom_id, problem['problem_id'],
                                                      [b[i]])
                                data = json['data']
                                time.sleep(1)  # 缓冲1秒再请求
                                if data['count'] == data['my_count']:
                                    print(title + ', 答题次数已经用完')
                                    break
                                if data['is_show_answer']:  # 回答正确
                                    print('{}, 正确选项: {}'.format(title, b[i]))
                                    break

                        elif TypeText == '单选题':
                            for i in range(0, size):

                                json = answer_problem(session, token, course.classroom_id,
                                                      problem['problem_id'],
                                                      chr(65 + i))
                                data = json['data']
                                time.sleep(1)  # 缓冲1秒再请求
                                if data['count'] == data['my_count']:
                                    print(title + ', 答题次数已经用完')
                                    break

                                if data['is_show_answer']:  # 回答正确
                                    print('{}, 正确选项: {}'.format(title, chr(65 + i)))
                                    break

                        elif TypeText == '多选题':
                            # 随机多选
                            opts = []
                            generate_choice(0, [], size, opts)
                            cnt = 0
                            my_cnt = 0
                            while cnt != my_cnt:
                                r = random.randint(0, opts.__len__() - 1)
                                opt = opts.pop(r)
                                json = answer_problem(session, token, course.classroom_id, problem['problem_id'], opt)
                                data = json['data']
                                time.sleep(1)
                                if data['is_show_answer']:  # 回答正确
                                    print('{}, 正确选项: {}'.format(title, opt))
                                    break
                                # del opts[r]
                            if cnt == my_cnt:
                                print(title + ', 答题次数已经用完')


do_chapter_homework()

