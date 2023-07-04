import time

from bs4 import BeautifulSoup
import genanki
import base64
import urllib
import re
import requests

BR = '<br/>'
API_KEY = "dVQZNRGdoYK513DiVocqa6y1"
SECRET_KEY = "irZtHhM8ELjFzm1w1bOtRQE3v9VORVZj"
file = r"D:\插本资料\计算机模拟卷简答题.html"
d = 'D:/插本资料/'

deck_name = file.split("\\")[-1].split(".")[0]

my_deck = genanki.Deck(
    2059400110,
    deck_name)

with open(file, 'r', encoding='utf8') as f:
    soup = BeautifulSoup(f.read(), 'lxml')

    # anki 的牌model 可以根据自己的想法设置
    my_model = genanki.Model(
        1091735104,
        'Simple Model with Media',
        # 这里是传入fields 的变量代名
        fields=[
            {'name': 'Question'},
            {'name': 'Answer'},
        ],
        # 直接将你传入的 变量 通过代名 写入模版 html还是很好理解的
        templates=[
            {
                'name': 'Card 1',
                'qfmt': '{{Question}}',  # AND THIS
                'afmt': '{{FrontSide}}<hr id="answer">{{Answer}}',
            },
        ],
        css=".card {   "
            "font-family: arial;   font-size: 20px;   text-align: center;   color: black;   background-color: white;}"
    )

img_list = []


def gen_notes(func, reverse=0, options=0, read_mode=0):
    # def has_title_note():

    # 笔记没有标题的，将背面作为正面

    question = ''
    lis = soup.select("li")
    for li in lis:
        if li.h3:  # 有设置标题
            question = li.h3.text
        else:  # 没设置标题
            # 对 pdf 文档的标注会在 blockquote 标签
            # 自己写的文本标注会在 .annot 标签下
            question = li.blockquote.prettify().replace(deck_name + "/", "")
            # 题目的图片保存到 apkg 的图片资源中
            imgs = li.blockquote.select("img")
            for img in imgs:
                # 保存图片资源路径到一个数组中
                img_list.append(d + img['src'])
        try:
            ans, question = func(li, reverse, question)
            my_note = genanki.Note(
                model=my_model,
                fields=[question + BR + ans if read_mode else question, ans])
            my_deck.add_note(my_note)
        except Exception as e:
            print(e.with_traceback())


def img_ans(li, reverse, q):
    # 获取到包括题目和答案的图片
    aa = li.select('.annot')
    # anki 通过判断卡片正面来判断是否重复
    if reverse:
        aa.reverse()
    ans = ''
    for div in aa:
        imgs = div.select("img")
        if not imgs:
            res = re.findall("[ABCDabcd]{2,4}", div.prettify())
            if res:
                q = '<h5>多选题</h5>' + q
        for img in imgs:
            # 保存图片资源路径到一个数组中
            img_list.append(d + img['src'])
        # 写入卡片中的图片 src 只需要名字不需要完整路径，会通过名字去路径数组中找的
        ans += div.prettify().replace(deck_name + "/", "")
    return ans, q


def orc_ans(li, r, q):
    ans = ''
    aa = li.select('.annot')
    for div in aa:
        imgs = div.select("img")
        for img in imgs:
            # 保存图片资源路径到一个数组中
            ans += get_text(d + img['src'])
            time.sleep(.3)
        ans += BR
        # 写入卡片中的图片 src 只需要名字不需要完整路径，会通过名字去路径数组中找的
    return ans


def text_only_front():
    lis = soup.select("li")
    for li in lis:
        my_note = genanki.Note(
            model=my_model,
            fields=[li.prettify(), ''])
        my_deck.add_note(my_note)


def get_text(path):
    url = "https://aip.baidubce.com/rest/2.0/ocr/v1/general_basic?access_token=" + get_access_token()

    payload = "image=" + get_file_content_as_base64(path, True)
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json'
    }
    order = "①②③④⑤⑥⑦⑧⑨⑩"

    response = requests.request("POST", url, headers=headers, data=payload)
    words_result = response.json()['words_result']
    print(words_result)
    ans = ''
    br = ['。']
    for i in range(len(words_result)):
        w = words_result[i]['words']
        if i == 0 and "】" in w:
            if w[-1] == "】":
                continue
            w = w.split("】")[1]
        if len(w) < 43 and w[-1] in br:
            w += BR

        ans += w
    return ans


def get_file_content_as_base64(path, urlencoded=False):
    """
    获取文件base64编码
    :param path: 文件路径
    :param urlencoded: 是否对结果进行urlencoded
    :return: base64编码信息
    """
    with open(path, "rb") as f:
        content = base64.b64encode(f.read()).decode("utf8")
        if urlencoded:
            content = urllib.parse.quote_plus(content)
    return content


def get_access_token():
    """
    使用 AK，SK 生成鉴权签名（Access Token）
    :return: access_token，或是None(如果错误)
    """
    url = "https://aip.baidubce.com/oauth/2.0/token"
    params = {"grant_type": "client_credentials", "client_id": API_KEY, "client_secret": SECRET_KEY}
    return str(requests.post(url, params=params).json().get("access_token"))


if __name__ == '__main__':
    gen_notes(orc_ans, reverse=0, options=0, read_mode=1)
    # text_only_front()
    my_package = genanki.Package(my_deck)
    my_package.media_files = img_list
    print(my_package.media_files)
    my_package.write_to_file(f"{deck_name}1.apkg")
