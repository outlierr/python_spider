import asyncio
import os
import re
import aiofiles
import requests

path = 'C:\\Users\\asl\\Desktop\\Note\\'
path = 'E:\\Note\\'
pic_bed_url = 'https://gitee.com/qq33444/typora-images/raw/master/imgs/'
suffixs = ['.jpg', '.png', '.gif']


async def scandir(path):
    for item in os.scandir(path):
        if item.is_dir() and item.name != 'GithubClone':
            await scandir(item.path)
        elif item.is_file() and re.match('[^README].+\.md', item.name):

            async with aiofiles.open(item.path, 'r', encoding='utf-8') as f:
                print(f'修改{item.path}的图片位置')
                # pat = re.compile('!\[.*\]\((.+\\\\(.+?\.(jpg|png|gif|awebp)))\)')
                pat = re.compile('!\[(.*)\]\(([^http].*)\)')
                content = await f.read()
                ret = re.findall(pat, content)
                for r in ret:
                    img_url = pic_bed_url + r[1]
                    content = content.replace(r[1], img_url)
                    print(img_url)
#                for r in ret:

                    # print(img_url)
                # re.sub(pat, pic_bed_url)
                print("=" * 50)
                # 异步要放在读内 不然会产生问题
                async with aiofiles.open(item.path, 'w', encoding='utf-8') as ff:
                    await ff.write(content)


loop = asyncio.get_event_loop()
loop.run_until_complete(scandir(path))
