from pynput import keyboard
from io import BytesIO
from pynput import keyboard


test_img = 'C:\\Users\\asl\Desktop\\test.jpg'


def upload_img():
    print("成功添加水印并上传到图床")
    with open(test_img, 'rb') as f:
        f.read()


def for_canonical(f):
    return lambda k: f(l.canonical(k))


hotkey = keyboard.HotKey(
    keyboard.HotKey.parse('<ctrl>+<alt>+p'),
    upload_img  # 回调函数
)
# with keyboard.Listener(
#         on_press=for_canonical(hotkey.press),
#         on_release=for_canonical(hotkey.release)) as l:
#     l.join()
#
# def upload_image_via_picgo():
#     k = PyKeyboard()
#     k.press_keys(['Command', 'shift', 'p'])

import requests
res = requests.get('https://gitee.com/qq33444/typora-images/blob/master/imgs/005118m7fado5aco7ocbhf.jpg')
print(res.status_code)