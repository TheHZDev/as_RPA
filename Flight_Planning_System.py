from typing import Tuple
from urllib.parse import urlparse

import bs4.element
from bs4 import BeautifulSoup
from requests import Session

local_Network_Debug = True
local_Network_Debug = not local_Network_Debug


class Flight_Planning_Sub_System:
    # logonSession = None
    # baseURL = ''
    cache_SubCompany = {}
    cache_AirportInfo = {}
    cache_ServiceInfo = {}

    def __init__(self, logonSession: Session, ServerName: str, callback_raiseException=None):
        """
        航班计划管理子系统\n
        :param logonSession: 登录后的Session
        :param ServerName: 服务器名称，比如Otto、Junker、Yeager
        :param callback_raiseException: 回调函数，GUI预留接口
        """
        self.logonSession = logonSession
        from LoginAirlineSim import getBaseURL
        self.baseURL = getBaseURL(ServerName)
        self.logonSession.headers['Origin'] = self.baseURL
        # 一些初始化
        self.SearchInfoIntelligently()

    def SearchFleets(self) -> dict:
        # 搜索需要进行排班的航机，已经在执行飞行任务的（绿色）、已排班但未执行的（黄色）、航班出现了问题的（红色）将会被跳过
        target_url = self.baseURL + '/app/fleets'
        fleetsInfo = {}
        FleetsPage = BeautifulSoup(
            self.DeleteALLChar(self.logonSession.get(target_url, verify=local_Network_Debug, timeout=10000).text),
            'html5lib')

        def Recursion_GetFleetsInfo(root: bs4.element.Tag):
            if root.attrs.get('title', '') == 'Flight Planning' and root.attrs.get('class', '') == ['btn',
                                                                                                    'btn-default']:
                # 检测到需要排班的航机
                origin_root: bs4.element.Tag = root.parent.parent.parent.parent  # 定位到该行的Tag
                link_URL = self.baseURL + '/app' + root.attrs.get('href')[1:]  # 为了去除相对的'.'
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
        if len(self.cache_AirportInfo) == 0 or len(self.cache_ServiceInfo) == 0:
            for unit_1 in fleetsInfo.keys():
                self.BuildAirlineInfoCache(unit_1)
                break
        return fleetsInfo

    def SearchSubCompany(self) -> dict:
        # 列出全部子公司列表，并建立缓存
        if len(self.cache_SubCompany) > 0:
            return self.cache_SubCompany
        MainPage = BeautifulSoup(
            self.DeleteALLChar(self.logonSession.get(self.baseURL, verify=local_Network_Debug, timeout=10000).text),
            'html5lib')

        def Recursion_GetCompanyInfo(root: bs4.element.Tag):
            if root.attrs.get('href', '').startswith('../../app/enterprise/dashboard?select='):
                id_sub_company = root.attrs.get('href').replace('../../app/enterprise/dashboard?select=', '')
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
                self.logonSession.cookies.set(cookie_name, None)
                self.logonSession.cookies.set(cookie_name, self.cache_SubCompany.get(CompanyName))
                flag_success = True
                break
        # 第二种方法，直接构造前缀Cookie
        if not flag_success:
            cookie_name = 'airlinesim-selectedEnterpriseId-' + urlparse(self.baseURL).netloc.split('.')[0]
            self.logonSession.cookies.set(cookie_name, self.cache_SubCompany.get(CompanyName))
        return True

    # 实际操作部分
    def BuildAirlineInfoCache(self, AirplaneURL: str):
        # 进入排程管理界面，获取有关机队的机场信息、服务信息，经过对比，这些信息似乎是静态的
        FleetsPage = self.logonSession.get(AirplaneURL, verify=local_Network_Debug, timeout=10000)

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

        for unit in BeautifulSoup(self.DeleteALLChar(FleetsPage.text), 'html5lib'):
            if isinstance(unit, bs4.element.Tag):
                Recursion_GetBasicInfo(unit)
        # 这里加一个判断，适用于那种连现有航班号都没有的情况
        if len(self.cache_ServiceInfo) == 0 or len(self.cache_AirportInfo) == 0:
            current_random = self.getCurrentRandom(FleetsPage.url, FleetsPage.text)
            t_url = 'IBehaviorListener.0-tabs-panel-newFlight-flightNumber-toggle~new-link'
            t_header = {'Wicket-Ajax': 'true', 'X-Requested-With': 'XMLHttpRequest',
                        'Wicket-Ajax-BaseURL': FleetsPage.url.split('/app/')[1],
                        'Wicket-FocusedElementId':
                            FleetsPage.text.split(t_url + '"')[1].split('"c":"')[1].split('"')[0]}
            t_url = current_random + t_url + '&_=%d' % self.getTimestamp()
            NewAirlinePage = self.logonSession.get(t_url, verify=local_Network_Debug, headers=t_header)
            # 这还是XML文档里夹了一个HTML文档
            t_text = self.DeleteALLChar(NewAirlinePage.text.split(']]></component>')[0].split('><![CDATA[')[1])
            for unit in BeautifulSoup(t_text, 'html5lib'):
                if isinstance(unit, bs4.element.Tag):
                    Recursion_GetBasicInfo(unit)

    def BuildNewAirlinePlan(self, AirplaneURL: str, SrcAirport: str, DstAirport: str,
                            Price: int, Service: str, DepartHour: int = -1, DepartMinute: int = -1,
                            WeekPlan: Tuple[bool, bool, bool, bool, bool, bool, bool] =
                            (True, True, True, True, True, True, True)):
        """
        使用给定的参数建立一个新航班，航班号采用随机生成（暂不支持航班中转）\n
        :param AirplaneURL: 要管理的机队的URL
        :param SrcAirport: 源机场，航班的出发地
        :param DstAirport: 目标机场，航班的目的地
        :param DepartHour: 起飞时间，这里是小时（0 ~ 23），如果不填，使用系统推荐时间代替
        :param DepartMinute: 起飞时间，这里是分钟（0 ~ 59），如果不填，使用系统推荐时间代替
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
                DstAirport in self.cache_AirportInfo.keys() and Service in self.cache_ServiceInfo.keys() and
                50 <= Price <= 200):
            raise Exception('请检查设置参数是否正确！参数异常，已拒绝。')
        AirlineManagerPage = self.logonSession.get(AirplaneURL, verify=local_Network_Debug, timeout=10000)
        current_random = self.getCurrentRandom(AirlineManagerPage.url, AirlineManagerPage.text)
        self.logonSession.headers['Referer'] = AirlineManagerPage.url
        # 获取可用航班号
        t_url = 'IBehaviorListener.0-tabs-panel-newFlight-flightNumber-newNumber-aircraft.newflight.number-number-number_body-number~find'
        if t_url not in AirlineManagerPage.text:
            # 应对完全没有新航班界面的特殊情况（是特殊，还是一般呢？）
            t_url_1 = 'IBehaviorListener.0-tabs-panel-newFlight-flightNumber-toggle~new-link'
            t_header = {'Wicket-Ajax': 'true', 'X-Requested-With': 'XMLHttpRequest',
                        'Wicket-Ajax-BaseURL': AirlineManagerPage.url.split('/app/')[1],
                        'Wicket-FocusedElementId':
                            AirlineManagerPage.text.split(t_url_1 + '"')[1].split('"c":"')[1].split('"')[0]}
            t_url_1 = current_random + t_url_1 + '&_=%d' % self.getTimestamp()
            AirlineManagerPage = self.logonSession.get(t_url_1, verify=local_Network_Debug, headers=t_header,
                                                       timeout=10000)
        if '><![CDATA[' in AirlineManagerPage.text:
            AirlineManagerPage_text = AirlineManagerPage.text.split(']]></component>')[0].split('><![CDATA[')[1]
        else:
            AirlineManagerPage_text = AirlineManagerPage.text
        t_header = {'Wicket-Ajax': 'true', 'X-Requested-With': 'XMLHttpRequest',
                    'Wicket-Ajax-BaseURL': AirlineManagerPage.url.split('/app/')[1],
                    'Wicket-FocusedElementId':
                        AirlineManagerPage.text.split(t_url + '"')[1].split('"c":"')[1].split('"')[0]}
        t_header.update(self.logonSession.headers)
        t_url = current_random + t_url + '&_=%d' % self.getTimestamp()
        t_page = self.logonSession.get(t_url, headers=t_header, verify=local_Network_Debug, timeout=10000)
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
                           'service': self.cache_ServiceInfo.get(Service),
                           'destination': self.cache_AirportInfo.get(DstAirport)}

        def Recursion_GetSpecialID_A(root: bs4.element.Tag):
            # 获取令人厌烦的隐藏ID参数，它长这样"idXX_XX_X"
            try:
                if root.attrs.get('action', '').endswith(t_url):
                    t_name = root.contents[0].contents[0].attrs.get('name')
                    first_post_data[t_name] = ''
                    return
                elif root.attrs.get('name', '') == 'departure:hours' and int(
                        first_post_data.get('departure:hours')) == -1:
                    for t_unit in root.children:
                        if t_unit.attrs.get('selected', '') == 'selected':
                            first_post_data['departure:hours'] = t_unit.attrs.get('value')
                            return
                elif root.attrs.get('name', '') == 'departure:minutes' and \
                        int(first_post_data.get('departure:minutes')) == -1:
                    for t_unit in root.children:
                        if t_unit.attrs.get('selected', '') == 'selected':
                            first_post_data['departure:minutes'] = t_unit.attrs.get('value')
                            return
            finally:
                for t_unit in root.children:
                    if len(first_post_data) >= 8 and int(first_post_data.get('departure:hours')) > 0 and \
                            int(first_post_data.get('departure:minutes')) > 0:
                        return
                    if isinstance(t_unit, bs4.element.Tag):
                        Recursion_GetSpecialID_A(t_unit)

        for unit in BeautifulSoup(self.DeleteALLChar(AirlineManagerPage_text), 'html5lib'):
            if len(first_post_data) >= 8 and first_post_data.get('departure:hours') > 0 and \
                    first_post_data.get('departure:minutes') > 0:
                break
            if isinstance(unit, bs4.element.Tag):
                Recursion_GetSpecialID_A(unit)
        # 填充数据成功
        t_url = current_random + t_url
        WeekPlanPage = self.logonSession.post(t_url, data=first_post_data, verify=local_Network_Debug, timeout=10000)
        self.logonSession.headers['Referer'] = WeekPlanPage.url
        current_random = self.getCurrentRandom(WeekPlanPage.url, WeekPlanPage.text)
        second_post_data = {}
        t_url = 'IFormSubmitListener-tabs-panel-newFlight-flightPlanning-flight.planning.form'
        # 迷惑大赏环节，我自己也不知道这bug什么鬼
        if t_url not in WeekPlanPage.text:
            t_url_1 = 'IFormSubmitListener-tabs-panel-newFlight-flightNumber-newNumber-aircraft.newflight.number'
            WeekPlanPage = self.logonSession.post(current_random + t_url_1, data=first_post_data,
                                                  verify=local_Network_Debug, timeout=10000)
            current_random = self.getCurrentRandom(WeekPlanPage.url, WeekPlanPage.text)

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
                    if isinstance(t_unit, bs4.element.Tag):
                        Recursion_GetSpecialID_B(t_unit)

        for unit in BeautifulSoup(self.DeleteALLChar(WeekPlanPage.text), 'html5lib'):
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
        second_post_data.update({'segmentSettings:0:newDeparture:hours': first_post_data['departure:hours'],
                                 'segmentSettings:0:newDeparture:minutes': first_post_data['departure:minutes'],
                                 'segmentsContainer:segments:0:departure-offsets:0:departureOffset': '0',
                                 'segmentsContainer:segments:0:departure-offsets:1:departureOffset': '0',
                                 'segmentsContainer:segments:0:departure-offsets:2:departureOffset': '0',
                                 'segmentsContainer:segments:0:departure-offsets:3:departureOffset': '0',
                                 'segmentsContainer:segments:0:departure-offsets:4:departureOffset': '0',
                                 'segmentsContainer:segments:0:departure-offsets:5:departureOffset': '0',
                                 'segmentsContainer:segments:0:departure-offsets:6:departureOffset': '0',
                                 'segmentsContainer:segments:0:speed-overrides:0:speedOverride': '',
                                 'segmentsContainer:segments:0:speed-overrides:1:speedOverride': '',
                                 'segmentsContainer:segments:0:speed-overrides:2:speedOverride': '',
                                 'segmentsContainer:segments:0:speed-overrides:3:speedOverride': '',
                                 'segmentsContainer:segments:0:speed-overrides:4:speedOverride': '',
                                 'segmentsContainer:segments:0:speed-overrides:5:speedOverride': '',
                                 'segmentsContainer:segments:0:speed-overrides:6:speedOverride': ''})
        last_result = self.logonSession.post(current_random + t_url, data=second_post_data,
                                             verify=local_Network_Debug, timeout=10000)
        # 建立了一条新航线
        return last_result.url  # 好像可以重复调用API建立多航线

    def checkMaintenanceRatio(self, htmlText: str):
        """检查排班后的维护比例是否低于100%，如果低于，就发出提示（返回是否继续进行自动排班的提示）"""
        result_list = []

        def Recursion_GetMaintenanceRatioInfo(root: bs4.element.Tag):
            if root.name == 'th' and root.getText() == 'Maintenance ratio':
                t1: str = root.parent.contents[1].contents[0].getText()
                if int(t1.replace('%', '')) < 100:
                    result_list.append('Warning')
                return
            for t_unit in root:
                if isinstance(t_unit, bs4.element.Tag):
                    Recursion_GetMaintenanceRatioInfo(t_unit)

        for unit in BeautifulSoup(self.DeleteALLChar(htmlText), 'html5lib'):
            if isinstance(unit, bs4.element.Tag):
                Recursion_GetMaintenanceRatioInfo(unit)
        if len(result_list) > 0:
            return False
        return True

    def CommitFlightPlan(self, AirplaneURL: str, UserSelect: int = 1):
        """
        提交航班计划到系统，默认为1，即立即执行\n
        :param AirplaneURL: 排班URL，执行完排班后返回的URL
        :param UserSelect: 用户选择，一般只介于1~4之间
        """
        FlightPlanPage = self.logonSession.get(AirplaneURL, verify=local_Network_Debug, timeout=10000)
        current_random = self.getCurrentRandom(FlightPlanPage.url, FlightPlanPage.text)
        t_url = 'IFormSubmitListener-tabs-panel-visualFlightPlan-action'
        post_data = {'select': str(UserSelect)}

        def Recursion_GetSpecialID(root: bs4.element.Tag):
            if root.name == 'form' and root.attrs.get('action', '').endswith(t_url):
                post_data[root.contents[0].contents[0].attrs.get('name')] = ''
                return
            for t_unit in root:
                if len(post_data) >= 2:
                    return
                if isinstance(t_unit, bs4.element.Tag):
                    Recursion_GetSpecialID(t_unit)

        for unit in BeautifulSoup(self.DeleteALLChar(FlightPlanPage.text), 'html5lib'):
            if len(post_data) >= 2:
                break
            if isinstance(unit, bs4.element.Tag):
                Recursion_GetSpecialID(unit)
        t_url = current_random + t_url
        self.logonSession.post(t_url, data=post_data, verify=local_Network_Debug, timeout=10000)

    # 信息披露函数定义区
    def listServiceInfo(self):
        return self.cache_ServiceInfo.keys()

    def listAirportInfo(self):
        return self.cache_AirportInfo.keys()

    def listSubCompanyInfo(self):
        return self.cache_SubCompany.keys()

    def SearchAirportNameBySimpleName(self, simpleName: str) -> str:
        # 通过搜索三字母简写来获取机场的完整名称
        simpleName = '(%s)' % simpleName
        for unit in self.listAirportInfo():
            if simpleName in unit:
                return unit

    # 辅助函数定义区
    @staticmethod
    def getCurrentRandom(urlPath: str, ResponseText: str) -> str:
        """提取响应的随机数以便访问时不会出错"""
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

    def SearchInfoIntelligently(self):
        # 智能搜索航班信息和服务信息，原理是遍历子公司以获取信息
        self.SearchSubCompany()  # 搜索所有子公司
        if len(self.cache_SubCompany) > 0:
            for subCompany in self.cache_SubCompany.keys():
                self.SwitchSubCompany(subCompany)
                t1 = self.SearchFleets()
                if len(t1) > 0:  # 发现可用航班
                    for AirFleet_URL in t1.keys():
                        self.BuildAirlineInfoCache(AirFleet_URL)  # 尝试建立缓存信息
                        return True
        else:  # 如果只有一家公司，是搜不到子公司的
            t1 = self.SearchFleets()
            if len(t1) > 0:  # 发现可用航班
                for AirFleet_URL in t1.keys():
                    self.BuildAirlineInfoCache(AirFleet_URL)  # 尝试建立缓存信息
                    return True
        return False
