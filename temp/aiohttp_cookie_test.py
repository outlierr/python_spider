import asyncio
import aiohttp

# from bs4 import BeautifulSoup
# xml = '''
# <?xml version="1.0" encoding="UTF-8"?>
# <CDO>
#     <CDOF N="cdoReturn">
#         <CDO>
#             <NF N="nCode" V="-1"/>
#             <STRF N="strText" V="FieldId nDestTypeId not exists"/>
#             <STRF N="strInfo" V=""/>
#         </CDO>
#     </CDOF>
#     <CDOF N="cdoResponse">
#         <CDO></CDO>
#     </CDOF>
# </CDO>
# '''
# soup = BeautifulSoup(xml, 'lxml')
# a = soup.select('NF[N="nCode"]')[0]
# print(type(a['v']))
# async def test():
#     async with aiohttp.ClientSession() as sess:
#         sess.cookie_jar.filter_cookies('http://www.baidu.com')
#         async with sess.get('http://www.baidu.com') as resp:
#             print(await resp.text())
#
#         print(sess.cookie_jar.filter_cookies('http://www.baidu.com'))
#         # ValueError: Only http proxies are supported
#         async with sess.get('http://www.baidu.com/s?ie=utf-8&f=8&rsv_bp=1&tn=baidu&wd=http%20502&oq=ip&rsv_pq=84b7c26b000d9422&rsv_t=f860tH7mAax1VgSZRejOVRWRIH7cMpn9Rv4xc0EQcsoBPBLh52h%2BjLgRaG8&rqlang=cn&rsv_enter=1&rsv_dl=tb&rsv_btype=t&inputT=2954&rsv_sug3=27&rsv_sug1=2&rsv_sug7=100&rsv_sug2=0&rsv_sug4=2954', proxy='http://127.0.0.1:8888') as resp:
#             print(await resp.text())
#
#
#
# loop = asyncio.get_event_loop()
# loop.run_until_complete(test())

{
    '$$CDORequest$$': '<CDO><STRF N="strServiceName" V="StudentCourseExerciseService"/><STRF N="strTransName" V="addExerciseAfterAnswer"/><LF N="lUserId" V="3070013770"/><LF N="lSchoolId" V="139"/><LF N="lCoursewareId" V="1654"/><NF N="bInOrAfter" V="1"/><NF N="nExerciseAfterCount" V="5"/><CDOAF N="answerArrayList"><CDO><LF N="lQuestionId" V="3935"/><STRF N="strAnswer" V="C"/><STRF N="strStudentAnswer" V="C"/><NF N="bTrue" V="0"/></CDO><CDO><LF N="lQuestionId" V="3936"/><STRF N="strAnswer" V="C"/><STRF N="strStudentAnswer" V="C"/><NF N="bTrue" V="0"/></CDO><CDO><LF N="lQuestionId" V="3937"/><STRF N="strAnswer" V="B"/><STRF N="strStudentAnswer" V="B"/><NF N="bTrue" V="0"/></CDO><CDO><LF N="lQuestionId" V="3938"/><STRF N="strAnswer" V="A"/><STRF N="strStudentAnswer" V="A"/><NF N="bTrue" V="0"/></CDO><CDO><LF N="lQuestionId" V="3939"/><STRF N="strAnswer" V="B"/><STRF N="strStudentAnswer" V="B"/><NF N="bTrue" V="0"/></CDO></CDOAF></CDO>'
}

{
    '$$CDORequest$$': '<CDO><STRF N="strServiceName" V="StudentCourseExerciseService"/><STRF N="strTransName" V="addExerciseAfterAnswer"/><LF N="lUserId" V="3070013770"/><LF N="lSchoolId" V="139"/><LF N="lCoursewareId" V="1649"/><LF N="bInOrAfter" V="1"/><LF N="nExerciseAfterCount" V="5"/><CDOAF><CDO><LF N="lQuestionId" V="3885"/><STRF N="strAnswer" V="B"/><STRF N="strStudentAnswer" V="B"/><LF N="bTrue" V="0"/></CDO><CDO><LF N="lQuestionId" V="3886"/><STRF N="strAnswer" V="C"/><STRF N="strStudentAnswer" V="C"/><LF N="bTrue" V="0"/></CDO><CDO><LF N="lQuestionId" V="3887"/><STRF N="strAnswer" V="D"/><STRF N="strStudentAnswer" V="D"/><LF N="bTrue" V="0"/></CDO><CDO><LF N="lQuestionId" V="3888"/><STRF N="strAnswer" V="A"/><STRF N="strStudentAnswer" V="A"/><LF N="bTrue" V="0"/></CDO><CDO><LF N="lQuestionId" V="3889"/><STRF N="strAnswer" V="A"/><STRF N="strStudentAnswer" V="A"/><LF N="bTrue" V="0"/></CDO></CDOAF></CDO>'
}

{
    '$$CDORequest$$': '<CDO><STRF N="strServiceName" V="ViewDataService"/><STRF N="strTransName" V="modifyRecentView"/><LF N="lSchoolId" V="139"/><LF N="lDestSchoolId" V="0"/><LF N="lUserId" V="3070013770"/><LF N="id" V="70002390"/><STRF N="name" V="职业发展决策（二）"/><LF N="nDestTypeId" V="1"/></CDO>'}
{
    '$$CDORequest$$': '<CDO><STRF N="strServiceName" V="ViewDataService"/><STRF N="strTransName" V="modifyRecentView"/><LF N="lSchoolId" V="139"/><LF N="lDestSchoolId" V="0"/><LF N="lUserId" V="3070013770"/><LF N="id" V="1656"/><STRF N="name" V="习惯的养成（二）"/><NF N="nDestTypeId" V="1"/></CDO>'}

'accessId=629815e0-e617-11e7-9699-ebe89a34abd4; uniqueVisitorId=a97003e0-3f70-d8c4-2da8-0893ebf477ac; luserid=3070013770; token=746c44ba41f07cc32bba6d0df750092463fca5965a0244c3b34e271c75aef23cbd1b44bb272d93c3ea5b0849bc57bc461f25c2025dc28afd6912c8ad313c39ff; lasttime=1636826488147; UM_distinctid=17d1a7b04b3653-0f1d10f734d355-57b1a33-149c48-17d1a7b04b4a59; Courseware_30700137701650=f46fba904e61f68a32ab09c21893cc60; href=http%3A%2F%2Fcourse.njcedu.com%2Fnewcourse%2Fcoursecc.htm%3FcourseId%3D1650; Courseware_30700137701651=a0ba73cf251b1b6b9d756a2a825be7d6b37e223885e4d54f303138d0a73f08da; Courseware_30700137701653=c0b985caf9fc1bc2a09d232aaae971acf46e545379ae71a50ae87a737e9b0079; Courseware_307001377010001289=e99c9362c903b79c16312889a73980e8; Courseware_30700137701676=e99c9362c903b79ce81dea5c929cc439; qimo_xstKeywords_629815e0-e617-11e7-9699-ebe89a34abd4=; qimo_seosource_629815e0-e617-11e7-9699-ebe89a34abd4=%E5%85%B6%E4%BB%96%E7%BD%91%E7%AB%99; qimo_seokeywords_629815e0-e617-11e7-9699-ebe89a34abd4=%E6%9C%AA%E7%9F%A5; JSESSIONID=627A126AEE8E2BFE56AE842069DBE429; Courseware_30700137701656=3fd6429460f4c4635be2ecaa31d50144; pageViewNum=52'



