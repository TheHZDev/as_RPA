from typing import Tuple
from urllib.parse import urlparse

import bs4.element
from bs4 import BeautifulSoup
from requests import Session


class Flight_Planning_Sub_System:
    # logonSession = None
    # baseURL = ''
    cache_SubCompany = {}
    cache_AirportInfo = {}
    cache_ServiceInfo = {}

    def __init__(self, logonSession: Session, ServerName: str):
        self.logonSession = logonSession
        from LoginAirlineSim import getBaseURL
        self.baseURL = getBaseURL(ServerName)
        # 一些初始化
        FirstSearch = self.SearchFleets()
        if len(FirstSearch) == 0:
            raise Exception('没有可以进行正常排班的机队！')
        self.SearchSubCompany()
        for one_url in FirstSearch.keys():
            self.BuildAirlineInfoCache(one_url)
            break

    def SearchFleets(self) -> dict:
        # 搜索需要进行排班的航机，已经在执行飞行任务的（绿色）、已排班但未执行的（黄色）、航班出现了问题的（红色）将会被跳过
        target_url = self.baseURL + '/app/fleets'
        fleetsInfo = {}
        FleetsPage = BeautifulSoup(self.DeleteALLChar(self.logonSession.get(target_url).text), 'html5lib')

        def Recursion_GetFleetsInfo(root: bs4.element.Tag):
            if root.attrs.get('title', '') == 'Flight Planning' and root.attrs.get('class', '') == ['btn',
                                                                                                    'btn-default']:
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
        flag_success = False
        # 第一种方法，进行前缀匹配
        for cookie_name in self.logonSession.cookies.keys():
            if cookie_name.startswith('airlinesim-selectedEnterpriseId-'):
                self.logonSession.cookies[cookie_name] = self.cache_SubCompany.get(CompanyName)
                flag_success = True
                break
        # 第二种方法，直接构造前缀Cookie
        if not flag_success:
            cookie_name = 'airlinesim-selectedEnterpriseId-' + urlparse(self.baseURL).netloc.split('.')[0]
            self.logonSession.cookies[cookie_name] = self.cache_SubCompany.get(CompanyName)
        return True

    # 实际操作部分
    def BuildAirlineInfoCache(self, AirplaneURL: str):
        # 进入排程管理界面，获取有关机队的机场信息、服务信息，经过对比，这些信息似乎是静态的
        FleetsPage = BeautifulSoup(self.DeleteALLChar(self.logonSession.get(AirplaneURL).text), 'html5lib')

        def Recursion_GetBasicInfo(root: bs4.element.Tag):
            if root.name == 'select':
                if root.attrs.get('name', '') == 'origin':
                    for option in root.children:
                        if len(option.attrs.get('value', '')) > 0:
                            self.cache_AirportInfo[option.getText()] = option.attrs.get('value')
                elif root.attrs.get('name', '') == 'service':
                    for option in root.children:
                        if len(option.attrs.get('value', '')) > 0:
                            self.cache_ServiceInfo[option.getText()] = option.attrs.get('value')
                return
            for unit_1 in root.children:
                if isinstance(unit_1, bs4.element.Tag):
                    Recursion_GetBasicInfo(unit_1)

        for unit in FleetsPage.children:
            if isinstance(unit, bs4.element.Tag):
                Recursion_GetBasicInfo(unit)

    def BuildNewAirlinePlan(self, AirplaneURL: str, SrcAirport: str, DstAirport: str, DepartHour: int,
                            DepartMinute: int, Price: int, Service: str,
                            WeekPlan: Tuple[bool, bool, bool, bool, bool, bool, bool] =
                            (True, True, True, True, True, True, True)):
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
        # 函数操作：
        # 1、先获取一个可用的航班号码，有两种方式：随机提交一个观察XML响应，或者获取所有可用的航班号并选择一个。
        # 2、获取表单的第一个随机数据（也许是为了防脚本），然后构造带有出发机场、目标机场、出发时间、价格乘数、服务乘数的表单
        # 3、构造带有航班排程（周计划排程）的表单并提交
        # 参数正确性检查
        if not (AirplaneURL.startswith(self.baseURL) and SrcAirport in self.cache_AirportInfo.keys() and
                DstAirport in self.cache_AirportInfo.keys() and 0 <= DepartHour <= 23 and 0 <= DepartMinute <= 59 and
                Service in self.cache_ServiceInfo.keys() and 50 <= Price <= 200):
            raise Exception('请检查设置参数是否正确！参数异常，已拒绝。')
        AirlineManagerPage = self.logonSession.get(AirplaneURL)
        current_random = self.getCurrentRandom(AirlineManagerPage.url, AirlineManagerPage.text)
        self.logonSession.headers['Referer'] = AirlineManagerPage.url
        # 获取可用航班号
        t_url = 'IBehaviorListener.0-tabs-panel-newFlight-flightNumber-newNumber-aircraft.newflight.number-number-number_body-number~find'
        t_header = {'Wicket-Ajax': 'true', 'X-Requested-With': 'XMLHttpRequest',
                    'Wicket-Ajax-BaseURL': AirlineManagerPage.url.split('/app/')[1],
                    'Wicket-FocusedElementId':
                        AirlineManagerPage.text.split(t_url + '"')[1].split('"c":"')[1].split('"')[0]}
        t_header.update(self.logonSession.headers)
        t_url = current_random + t_url + '&_=%d' % self.getTimestamp()
        t_page = self.logonSession.get(t_url, headers=t_header)
        # 返回页面是XML里夹了个html，先把HTML搞出来
        t_page_text = self.DeleteALLChar(t_page.text.split(']]></component>')[0].split('><![CDATA[')[1])
        AirlineNumber = [-1]

        def Recursion_GetUsableAirlineNumber(root: bs4.element.Tag):
            if root.attrs.get('class', '') == ['good', 'found']:
                AirlineNumber[0] = int(root.parent.contents[1].contents[0].contents[0].getText())
                return
            for t_unit in root.children:
                if AirlineNumber[0] > 0:
                    return
                if isinstance(t_unit, bs4.element.Tag):
                    Recursion_GetUsableAirlineNumber(t_unit)

        for unit in BeautifulSoup(t_page_text, 'html5lib'):
            if AirlineNumber[0] > 0:
                break
            if isinstance(unit, bs4.element.Tag):
                Recursion_GetUsableAirlineNumber(unit)
        # 获取了一个可用的航班号码
        t_url = 'IFormSubmitListener-tabs-panel-newFlight-flightNumber-newNumber-aircraft.newflight.number'
        first_post_data = {'number:number_body:input': str(AirlineNumber[0]),
                           'origin': self.cache_AirportInfo.get(SrcAirport),
                           'departure:hours': DepartHour, 'departure:minutes': DepartMinute, 'price': Price,
                           'service': self.cache_ServiceInfo.get(Service)}

        def Recursion_GetSpecialID_A(root: bs4.element.Tag):
            # 获取令人厌烦的隐藏ID参数，它长这样"idXX_XX_X"
            try:
                if root.attrs.get('action', '').endswith(t_url):
                    t_name = root.contents[0].contents[0].attrs.get('name')
                    first_post_data[t_name] = ''
                    return
            finally:
                for t_unit in root.children:
                    if len(first_post_data) >= 8:
                        return
                    if isinstance(t_unit, bs4.element.Tag):
                        Recursion_GetSpecialID_A(t_unit)

        for unit in BeautifulSoup(self.DeleteALLChar(AirlineManagerPage.text), 'html5lib'):
            if len(first_post_data) >= 8:
                break
            if isinstance(unit, bs4.element.Tag):
                Recursion_GetSpecialID_A(unit)
        # 填充数据成功
        t_url = current_random + t_url
        WeekPlanPage = self.logonSession.post(t_url, data=first_post_data)
        current_random = self.getCurrentRandom(WeekPlanPage.url, WeekPlanPage.text)
        # TODO:填充排班数据
        second_post_data = {}
        t_url = 'IFormSubmitListener-tabs-panel-newFlight-flightPlanning-flight.planning.form'

        def Recursion_GetSpecialID_B(root: bs4.element.Tag):
            # 获取令人厌烦的隐藏ID参数，它长这样"idXX_XX_X"
            try:
                if root.attrs.get('action', '').endswith(t_url):
                    t_name = root.contents[0].contents[0].attrs.get('name')
                    second_post_data[t_name] = ''
                    return
                if root.attrs.get('name', '') == 'button-submit':  # 提取特定文字
                    second_post_data['button-submit'] = root.attrs.get('value')
                    return
                if root.attrs.get('name', '') == 'segmentSettings:0:originTerminal':
                    # 出发航站楼
                    for t_unit in root.children:
                        if t_unit.attrs.get('selected', '') == 'selected':
                            second_post_data['segmentSettings:0:originTerminal'] = t_unit.attrs.get('value')
                            return
                if root.attrs.get('name', '') == 'segmentSettings:0:destinationTerminal':
                    # 到达航站楼
                    for t_unit in root.children:
                        if t_unit.attrs.get('selected', '') == 'selected':
                            second_post_data['segmentSettings:0:destinationTerminal'] = t_unit.attrs.get('value')
                            return
            finally:
                for t_unit in root.children:
                    if len(second_post_data) >= 4:
                        return
                    if isinstance(t_unit, bs4.element.Tag):
                        Recursion_GetSpecialID_B(t_unit)

        for unit in BeautifulSoup(self.DeleteALLChar(WeekPlanPage.text), 'html5lib'):
            if len(second_post_data) >= 4:
                break
            if isinstance(unit, bs4.element.Tag):
                Recursion_GetSpecialID_B(unit)
        # 获取了周计划排班页面的特殊ID
        try:
            t_num = 0
            for boolVar in WeekPlan:
                if boolVar:
                    second_post_data['days:daySelection:%d:ticked' % t_num] = 'on'
                else:
                    second_post_data['days:daySelection:%d:ticked' % t_num] = 'off'
                t_num += 1
        except:
            # 如果出现错误，直接套用已经做好的排程
            second_post_data.update({'days:daySelection:0:ticked': 'on', 'days:daySelection:1:ticked': 'on',
                                     'days:daySelection:2:ticked': 'on', 'days:daySelection:3:ticked': 'on',
                                     'days:daySelection:4:ticked': 'on', 'days:daySelection:5:ticked': 'on',
                                     'days:daySelection:6:ticked': 'on'})
        second_post_data.update({'segmentSettings:0:newDeparture:hours': str(DepartHour),
                                 'segmentSettings:0:newDeparture:minutes': str(DepartMinute),
                                 'segmentsContainer:segments:0:departure-offsets:0:departureOffset': '',
                                 'segmentsContainer:segments:0:departure-offsets:1:departureOffset': '',
                                 'segmentsContainer:segments:0:departure-offsets:2:departureOffset': '',
                                 'segmentsContainer:segments:0:departure-offsets:3:departureOffset': '',
                                 'segmentsContainer:segments:0:departure-offsets:4:departureOffset': '',
                                 'segmentsContainer:segments:0:departure-offsets:5:departureOffset': '',
                                 'segmentsContainer:segments:0:departure-offsets:6:departureOffset': '',
                                 'segmentsContainer:segments:0:speed-overrides:0:speedOverride': '',
                                 'segmentsContainer:segments:0:speed-overrides:1:speedOverride': '',
                                 'segmentsContainer:segments:0:speed-overrides:2:speedOverride': '',
                                 'segmentsContainer:segments:0:speed-overrides:3:speedOverride': '',
                                 'segmentsContainer:segments:0:speed-overrides:4:speedOverride': '',
                                 'segmentsContainer:segments:0:speed-overrides:5:speedOverride': '',
                                 'segmentsContainer:segments:0:speed-overrides:6:speedOverride': ''})
        debug_var = self.logonSession.post(current_random + t_url, data=second_post_data)
        # 建立了一条新航线
        # print(debug_var.text)

    # 辅助函数定义区
    @staticmethod
    def getCurrentRandom(urlPath: str, ResponseText: str) -> str:
        # 提取响应的随机数
        url_prefix = './' + urlparse(urlPath).path.split('/')[-1] + '?' + urlparse(urlPath).query
        return urlPath + ResponseText.split('Wicket.Ajax.ajax({"u":"%s' % url_prefix)[1].split('.')[0] + '.'

    @staticmethod
    def DeleteALLChar(html_str: str) -> str:
        # 这仅仅是使得解析器解析时不会再碰到多余的空格
        html_str = html_str.replace('\t', '').replace('\r', '').replace('\n', '')  # 去除常见的大空格和换行
        while '  ' in html_str:  # 双空格合并为一空格
            html_str = html_str.replace('  ', ' ')
        return html_str.replace('> <', '><')  # 去除标签之间的空格

    @staticmethod
    def getTimestamp() -> int:
        from time import time
        return int(time() * 1000)
