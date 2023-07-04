import math
import random
import execjs
import requests
from url import *
import re


def get_user_info():
    cookies = 'sessionid=3tumihsjyvyjkx2983lru3skd77nn9h6'
    headers = {
        'Cookie': cookies,
        'xtbz': 'cloud'
    }
    res = requests.request('GET', userInfoUrl, headers=headers)


# 用户拥有的课程
def get_courses_info(uvid, session):
    cookies = 'university_id={}; sessionid={}'.format(uvid, session)
    headers = {
        'university-id': uvid,
        'Cookie': cookies,
        'xtbz': 'cloud'
    }
    res = requests.request('GET', userCourseUrl, headers=headers)
    return res.json()['data']


# 获取课程全部章节
def get_course_chapters(cr_id, co_sign, uv_id, session):
    cookies = 'sessionid=' + session
    headers = {
        "university-id": uv_id,
        'Cookie': cookies,
        'xtbz': 'cloud',
    }
    res = requests.request('GET', f'{courseChaptersUrl}?cid={cr_id}&sign={co_sign}', headers=headers)
    return res.json()['data']  # id


# 获取章节完成情况
def get_chapter_schedule(cr_id, co_sign, uv_id, session):
    cookies = 'sessionid=' + session
    headers = {
        'Cookie': cookies,
        'xtbz': 'cloud',
    }
    url = f'{chapterScheduleUrl}?cid={cr_id}&sign={co_sign}&uv_id={uv_id}'
    res = requests.request('GET', url, headers=headers)
    return res.json()['data']


# 获取每个章节点
def chapter_leaf_info(session, co_sign, cr_id, leaf_id, uv_id):  # 练习章节需要lt_id
    cookies = 'sessionid=' + session
    headers = {
        'university-id': uv_id,
        'Cookie': cookies,
        'xtbz': 'cloud'
    }
    res = requests.request('GET', f'{chapterLeafInfoUrl}/{cr_id}/{leaf_id}/?sign={co_sign}', headers=headers)
    return res.json()['data']


# 章节练习
def get_exercise_list(session, leaf_type_id):
    cookies = 'sessionid=' + session
    headers = {
        'Cookie': cookies,
        'xtbz': 'cloud'
    }

    res = requests.request('GET', f'{chapterExerciseUrl}{leaf_type_id}/', headers=headers)  # leaf_type_id
    return res.json()['data']
    # list = {
    #     'p_id': data['ProblemID'],
    #     'opts': data['Options'],
    #
    # }


def answer_problem(session, crf_token, cr_id, pid, opts):
    cookies = 'sessionid={}; csrftoken={}'.format(session, crf_token)

    json = {
        'answer': opts,
        'classroom_id': cr_id,
        'problem_id': pid
    }
    headers = {
        'content-type': 'application/single.json',
        'Cookie': cookies,
        'xtbz': 'cloud',
        'x-csrftoken': crf_token
    }
    res = requests.request('POST', answerProblemUrl, headers=headers, json=json)
    return res.json()
    # try:
    #     return res.single.json()['data']
    # except Exception:
    #     print(res.text)


# 视频 media{ccid}


# 获取视频观看进度信息
def get_video_process_info(session, co_id, uid, cr_id, video_type, leaf_id):
    cookies = 'sessionid=' + session
    headers = {
        'Cookie': cookies,
        'xtbz': 'cloud'
    }
    url = f'{videoProgressInfoUrl}?cid={co_id}&user_id={uid}&classroom_id={cr_id}&video_type={video_type}&vtype=rate&video_id={leaf_id}&snapshot=1'
    res = requests.request('GET', url, headers=headers)
    return res.json()





def heartbeat(session, data):
    cookies = 'sessionid=' + session
    headers = {
        'Cookie': cookies,
        'xtbz': 'cloud'
    }
    # 发送json
    json = {
        'heart_data': data
    }
    res = requests.request('POST', videoHeartBeatUrl, headers=headers, json=json)
    #print(res.single.json())
    return res.json()

