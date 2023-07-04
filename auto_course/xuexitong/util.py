import random
from io import BytesIO

import requests
from PIL import ImageFont, Image, ImageDraw


def get_answer(q_title, type_id):
    url = 'http://cx.icodef.com/wyn-nb'
    data = {
        'question': q_title,
        'type': type_id,
        id: "108086857"
    }
    res = requests.request('POST', url=url, data=data)
    return res.json()


# print(get_answer("地理学研究和考察是重要对象光区域。", 0))


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


def random_ans(type_id: int):
    if type_id == 0:
        return chr(65 + random.randint(0, 3))
    if type_id == 1:
        cs = []
        multiple_choice(0, [], 4, cs)
        return cs[random.randint(0, cs.__len__() - 1)]
    if type_id in [2, 4, 5, 6]:
        return ''
    if type_id == 3:
        return str(bool(random.randint(0, 1))).lower()


def uni_2_png_stream(txt: str, font: str, img_size=512):
    """将字形转化为图片流

    Args:
        txt (str): 图片标志信息, 从 TTFont.getBestCmap() 获得
        font (str): 字体文件名
        img_size (int, optional): [description]. Defaults to 512.

    Returns:
        一个 pillow 图片对象.
    """
    img = Image.new('1', (img_size, img_size), 255)  # (1)
    draw = ImageDraw.Draw(img)  # (2)
    font = ImageFont.truetype(font, int(img_size * 0.7))  # (3)

    x, y = draw.textsize(txt, font=font)  # (4)
    draw.text(((img_size - x) // 2, (img_size - y) // 2), txt, font=font, fill=0)  # (5)
    img_io = BytesIO()
    img.save(img_io, "png")
    return img, img_io
