import aiofiles
import asyncio

path = 't.txt'
path1 = './tt.txt'


async def func():
    content = '666'
    async with aiofiles.open(path, 'r', encoding='utf-8') as f:
        content = await f.read()
        print(content)
        print(2)
    # await f.read() 线程被挂起
    async with aiofiles.open(path1, 'w', encoding='utf-8') as ff:
        await ff.write(content)
        print(3)


loop = asyncio.get_event_loop()
loop.run_until_complete(func())
