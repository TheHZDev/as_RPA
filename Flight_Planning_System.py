from typing import Tuple

import bs4.element
from bs4 import BeautifulSoup
from requests import Session


class Flight_Planning_Sub_System:
    # logonSession = None
    # baseURL = ''
    cache_SubCompany = {}

    def __init__(self, logonSession: Session, ServerName: str):
        self.logonSession = logonSession
        from LoginAirlineSim import getBaseURL
        self.baseURL = getBaseURL(ServerName)
        self.cookie_sub_company = 'airlinesim-selectedEnterpriseId-' + self.baseURL.split('.')[0].split('//')[1]

    def SearchFleets(self) -> dict:
        # 搜索需要进行排班的航机，已经在执行飞行任务的（绿色）、已排班但未执行的（黄色）、航班出现了问题的（红色）将会被跳过
        target_url = self.baseURL + '/app/fleets'
        fleetsInfo = {}
        FleetsPage = BeautifulSoup(self.DeleteALLChar(self.logonSession.get(target_url).text), 'html5lib')

        def Recursion_GetFleetsInfo(root: bs4.element.Tag):
            if root.attrs.get('title', '') == 'Flight Planning' and root.attrs.get('class', '') == 'btn btn-default':
                # 检测到需要排班的航机
                origin_root: bs4.element.Tag = root.parent.parent.parent.parent  # 定位到该行的Tag
                link_URL = self.baseURL + root.attrs.get('href')[1:]  # 为了去除相对的'.'
                Airplane_NickName = origin_root.contents[1].contents[0].getText()
                Airplane_Type = origin_root.contents[2].contents[0].getText()
                fleetsInfo[link_URL] = {'NickName': Airplane_NickName, 'AirType': Airplane_Type}
                return
            for unit in root.children:
                if isinstance(unit, bs4.element.Tag):
                    Recursion_GetFleetsInfo(unit)

        for unit_1 in FleetsPage.children:
            if isinstance(unit_1, bs4.element.Tag):
                Recursion_GetFleetsInfo(unit_1)
        return fleetsInfo

    def SearchSubCompany(self) -> dict:
        # 列出全部子公司列表，并建立缓存
        if len(self.cache_SubCompany) > 0:
            return self.cache_SubCompany
        MainPage = BeautifulSoup(self.DeleteALLChar(self.logonSession.get(self.baseURL).text), 'html5lib')

        def Recursion_GetCompanyInfo(root: bs4.element.Tag):
            if root.attrs.get('href', '').startswith('./enterprise/dashboard?select='):
                id_sub_company = root.attrs.get('href').replace('./enterprise/dashboard?select=', '')
                self.cache_SubCompany[root.contents[0].getText()] = id_sub_company
                return
            for unit in root.children:
                if isinstance(unit, bs4.element.Tag):
                    Recursion_GetCompanyInfo(unit)

        for unit_1 in MainPage.children:
            if isinstance(unit_1, bs4.element.Tag):
                Recursion_GetCompanyInfo(unit_1)
        return self.cache_SubCompany

    def SwitchSubCompany(self, CompanyName: str) -> bool:
        # 切换公司，这主要是通过直接修改Cookie中的'airlinesim-selectedEnterpriseId-'变量来实现的
        if CompanyName not in self.cache_SubCompany.keys():
            return False
        self.logonSession.cookies[self.cookie_sub_company] = self.cache_SubCompany.get(CompanyName)
        return True

    # 实际操作部分
    def BuildNewAirlinePlan(self, AirplaneURL: str, SrcAirport: int, DstAirport: int, DepartHour: int,
                            DepartMinute: int,
                            WeekPlan: Tuple[bool, bool, bool, bool, bool, bool, bool], Price: int, Service: int):
        """
        使用给定的参数建立一个新航班，航班号采用随机生成（暂不支持航班中转）\n
        :param AirplaneURL: 要管理的机队的URL
        :param SrcAirport: 源机场，航班的出发地
        :param DstAirport: 目标机场，航班的目的地
        :param DepartHour: 起飞时间，这里是小时（0 ~ 23）
        :param DepartMinute: 起飞时间，这里是分钟（0 ~ 59）
        :param WeekPlan: 周计划排班，都选True就是一周全排
        :param Price: 价格系数，实际上是个百分比，如110 <=> 110%
        :param Service: 服务系数，请使用其它函数生成该数值
        """
        AirlineManagerPage = self.logonSession.get(AirplaneURL)
        current_random = self.getCurrentRandom(AirlineManagerPage.url, AirlineManagerPage.text)

    @staticmethod
    def getCurrentRandom(urlPath: str, ResponseText: str) -> str:
        # 提取响应的随机数
        from urllib.parse import urlparse
        url_prefix = './' + urlparse(urlPath).path.split('/')[-1] + '?' + urlparse(urlPath).query
        return urlPath + ResponseText.split('Wicket.Ajax.ajax({"u":"%s' % url_prefix)[1].split('.')[0]

    @staticmethod
    def DeleteALLChar(html_str: str) -> str:
        # 这仅仅是使得解析器解析时不会再碰到多余的空格
        html_str = html_str.replace('\t', '').replace('\r', '').replace('\n', '')  # 去除常见的大空格和换行
        while '  ' in html_str:  # 双空格合并为一空格
            html_str = html_str.replace('  ', ' ')
        return html_str.replace('> <', '><')  # 去除标签之间的空格
