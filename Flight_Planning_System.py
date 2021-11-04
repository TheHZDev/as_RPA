from urllib.parse import urlparse

from bs4 import BeautifulSoup
from bs4.element import Tag as bs4_tag
from requests import Session, Response

try:
    from local_debug import flag_Debug

    Debug_Allow_HTTPS_Verify = not flag_Debug
except:
    Debug_Allow_HTTPS_Verify = True

# 系统代理感知
import urllib.request

LocalProxier = urllib.request.getproxies()


class Flight_Planning_Sub_System:
    # logonSession = None
    # baseURL = ''
    cache_SubCompany = {}
    cache_AirportInfo = {}
    cache_ServiceInfo = {}
    cache_search_fleets = {}
    default_service_name = ''
    const_speed_config = {'Min': 0, 'Normal': 1, 'Max': 2}  # 速度常规设置

    def __init__(self, logonSession: Session, ServerName: str, callback_raiseException=None):
        """
        航班计划管理子系统
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

    def close(self):
        """请使用该函数注销AirlineSim会话"""
        target_url = 'https://sar.simulogics.games/api/sessions/' + \
                     self.logonSession.cookies.get('as-sid').split('_')[0]
        self.logonSession.delete(target_url, proxies=LocalProxier)

    def SearchFleets(self) -> dict:
        # 搜索需要进行排班的航机，已经在执行飞行任务的（绿色）、已排班但未执行的（黄色）、航班出现了问题的（红色）将会被跳过
        target_url = self.baseURL + '/app/fleets'
        fleetsInfo = {}
        FleetsPage = BeautifulSoup(
            self.DeleteALLChar(self.logonSession.get(target_url, verify=Debug_Allow_HTTPS_Verify,
                                                     timeout=10000).text, proxies=LocalProxier), 'html5lib')

        def Recursion_GetFleetsInfo(root: bs4_tag):
            if root.attrs.get('title', '') in ('Flight Planning', '排程') and \
                    root.attrs.get('class', '') == ['btn', 'btn-default']:
                # 检测到需要排班的航机
                origin_root: bs4_tag = root.parent.parent.parent.parent  # 定位到该行的Tag
                link_URL = self.baseURL + '/app' + root.attrs.get('href')[1:]  # 为了去除相对的'.'
                Airplane_NickName = origin_root.contents[1].contents[0].getText()
                Airplane_Type = origin_root.contents[2].contents[0].getText()
                fleetsInfo[link_URL] = {'NickName': Airplane_NickName, 'AirType': Airplane_Type}
                return
            for unit in root.children:
                if isinstance(unit, bs4_tag):
                    Recursion_GetFleetsInfo(unit)

        for unit_1 in FleetsPage.children:
            if isinstance(unit_1, bs4_tag):
                Recursion_GetFleetsInfo(unit_1)
        if len(self.cache_AirportInfo) == 0 or len(self.cache_ServiceInfo) == 0:
            for unit_1 in fleetsInfo.keys():
                self.BuildAirlineInfoCache(unit_1)
                break
        self.cache_search_fleets = fleetsInfo.copy()
        return fleetsInfo

    def SearchSubCompany(self) -> dict:
        # 列出全部子公司列表，并建立缓存
        if len(self.cache_SubCompany) > 0:
            return self.cache_SubCompany
        MainPage = BeautifulSoup(
            self.DeleteALLChar(
                self.logonSession.get(self.baseURL, verify=Debug_Allow_HTTPS_Verify, timeout=10000,
                                      proxies=LocalProxier).text), 'html5lib')

        def Recursion_GetCompanyInfo(root: bs4_tag):
            if root.attrs.get('href', '').startswith('../../app/enterprise/dashboard?select='):
                id_sub_company = root.attrs.get('href').replace('../../app/enterprise/dashboard?select=', '')
                self.cache_SubCompany[root.contents[0].getText()] = id_sub_company
                return
            for unit in root.children:
                if isinstance(unit, bs4_tag):
                    Recursion_GetCompanyInfo(unit)

        for unit_1 in MainPage.children:
            if isinstance(unit_1, bs4_tag):
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
        FleetsPage = self.logonSession.get(AirplaneURL, verify=Debug_Allow_HTTPS_Verify, timeout=10000,
                                           proxies=LocalProxier)

        def Recursion_GetBasicInfo(root: bs4_tag):
            if root.name == 'select':
                if root.attrs.get('name', '') == 'origin':
                    for option in root.children:
                        if len(option.attrs.get('value', '')) > 0:
                            self.cache_AirportInfo[option.getText()] = option.attrs.get('value')
                elif root.attrs.get('name', '') == 'service':
                    for option in root.children:
                        if len(option.attrs.get('value', '')) > 0:
                            self.cache_ServiceInfo[option.getText()] = option.attrs.get('value')
                            # 这里安排了一个循环赋值，以使默认服务方案名为最后的
                            self.default_service_name = option.getText()
                return
            for unit_1 in root.children:
                if isinstance(unit_1, bs4_tag):
                    Recursion_GetBasicInfo(unit_1)

        for unit in BeautifulSoup(self.DeleteALLChar(FleetsPage.text), 'html5lib'):
            if isinstance(unit, bs4_tag):
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
            NewAirlinePage = self.logonSession.get(t_url, verify=Debug_Allow_HTTPS_Verify, headers=t_header,
                                                   proxies=LocalProxier)
            # 这还是XML文档里夹了一个HTML文档
            t_text = self.DeleteALLChar(NewAirlinePage.text.split(']]></component>')[0].split('><![CDATA[')[1])
            for unit in BeautifulSoup(t_text, 'html5lib'):
                if isinstance(unit, bs4_tag):
                    Recursion_GetBasicInfo(unit)

    def BuildNewAirlinePlan(self, AirplaneURL: str, SrcAirport: str, DstAirport: str,
                            Price: int, Service: str, DepartHour: int = -1, DepartMinute: int = -1,
                            SrcTerminal: str = 'T1', DstTerminal: str = 'T1', SpeedConfig: int = 1,
                            LastResponse: Response = None):
        """
        使用给定的参数建立一个新航班，航班号采用随机生成（暂不支持航班中转）
        :param AirplaneURL: 要管理的机队的URL
        :param SrcAirport: 源机场，航班的出发地
        :param DstAirport: 目标机场，航班的目的地
        :param DepartHour: 起飞时间，这里是小时（0 ~ 23），如果不填，使用系统推荐时间代替
        :param DepartMinute: 起飞时间，这里是分钟（0 ~ 59），如果不填，使用系统推荐时间代替
        :param Price: 价格系数，实际上是个百分比，如110 <=> 110%
        :param Service: 服务系数，请使用其它函数生成该数值
        :param SrcTerminal: 出发机场航站楼。写T2即代表选中T2
        :param DstTerminal: 目的机场航站楼，写T2即代表选中T2
        :param LastResponse: 上次的响应，这是一个内部调用，请勿使用
        """
        # 函数操作：
        # 1、先获取一个可用的航班号码，有两种方式：随机提交一个观察XML响应，或者获取所有可用的航班号并选择一个。
        # 2、获取表单的第一个随机数据（也许是为了防脚本），然后构造带有出发机场、目标机场、出发时间、价格乘数、服务乘数的表单
        # 3、构造带有航班排程（周计划排程）的表单并提交
        # 参数正确性检查
        if not ((AirplaneURL.startswith(self.baseURL) or isinstance(LastResponse, Response))
                and SrcAirport in self.cache_AirportInfo.keys() and DstAirport in self.cache_AirportInfo.keys() and
                Service in self.cache_ServiceInfo.keys() and 50 <= Price <= 200 and
                SpeedConfig in self.const_speed_config.values()):
            raise Exception('请检查设置参数是否正确！参数异常，已拒绝。')
        if isinstance(LastResponse, Response):
            AirlineManagerPage = LastResponse  # 可重复使用的Response
        else:
            AirlineManagerPage = self.logonSession.get(AirplaneURL, verify=Debug_Allow_HTTPS_Verify, timeout=10000,
                                                       proxies=LocalProxier)
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
            AirlineManagerPage = self.logonSession.get(t_url_1, verify=Debug_Allow_HTTPS_Verify, headers=t_header,
                                                       timeout=10000, proxies=LocalProxier)
        if '><![CDATA[' in AirlineManagerPage.text:
            AirlineManagerPage_text = AirlineManagerPage.text.split(']]></component>')[0].split('><![CDATA[')[1]
        else:
            AirlineManagerPage_text = AirlineManagerPage.text
        t_header = {'Wicket-Ajax': 'true', 'X-Requested-With': 'XMLHttpRequest',
                    'Wicket-Ajax-BaseURL': AirlineManagerPage.url.split('/app/')[1],
                    'Wicket-FocusedElementId':
                        AirlineManagerPage.text.split(t_url + '"')[1].split('"c":"')[1].split('"')[0]}
        t_header.update(self.logonSession.headers.copy())
        t_url = current_random + t_url + '&_=%d' % self.getTimestamp()
        t_page = self.logonSession.get(t_url, headers=t_header, verify=Debug_Allow_HTTPS_Verify, timeout=10000,
                                       proxies=LocalProxier)
        # 返回页面是XML里夹了个html，先把HTML搞出来
        t_page_text = self.DeleteALLChar(t_page.text.split(']]></component>')[0].split('><![CDATA[')[1])
        AirlineNumber = [-1]

        def Recursion_GetUsableAirlineNumber(root: bs4_tag):
            if root.attrs.get('class', '') == ['good', 'found']:
                AirlineNumber[0] = int(root.parent.contents[1].contents[0].contents[0].getText())
                return
            for t_unit in root.children:
                if AirlineNumber[0] > 0:
                    return
                if isinstance(t_unit, bs4_tag):
                    Recursion_GetUsableAirlineNumber(t_unit)

        for unit in BeautifulSoup(t_page_text, 'html5lib'):
            if AirlineNumber[0] > 0:
                break
            if isinstance(unit, bs4_tag):
                Recursion_GetUsableAirlineNumber(unit)
        # 获取了一个可用的航班号码
        t_url = 'IFormSubmitListener-tabs-panel-newFlight-flightNumber-newNumber-aircraft.newflight.number'
        first_post_data = {'number:number_body:input': str(AirlineNumber[0]),
                           'origin': self.cache_AirportInfo.get(SrcAirport),
                           'departure:hours': DepartHour, 'departure:minutes': DepartMinute, 'price': Price,
                           'service': self.cache_ServiceInfo.get(Service),
                           'destination': self.cache_AirportInfo.get(DstAirport)}

        def Recursion_GetSpecialID_A(root: bs4_tag):
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
                    if isinstance(t_unit, bs4_tag):
                        Recursion_GetSpecialID_A(t_unit)

        for unit in BeautifulSoup(self.DeleteALLChar(AirlineManagerPage_text), 'html5lib'):
            if len(first_post_data) >= 8 and first_post_data.get('departure:hours') > 0 and \
                    first_post_data.get('departure:minutes') > 0:
                break
            if isinstance(unit, bs4_tag):
                Recursion_GetSpecialID_A(unit)
        # 填充数据成功
        t_url = current_random + t_url
        WeekPlanPage = self.logonSession.post(t_url, data=first_post_data, verify=Debug_Allow_HTTPS_Verify,
                                              timeout=10000, proxies=LocalProxier)
        self.logonSession.headers['Referer'] = WeekPlanPage.url
        current_random = self.getCurrentRandom(WeekPlanPage.url, WeekPlanPage.text)
        second_post_data = {'segmentSettings:0:originTerminal': '', 'segmentSettings:0:destinationTerminal': '',
                            'segmentsContainer:segments:0:speed-overrides:0:speedOverride': '',
                            'segmentsContainer:segments:0:speed-overrides:1:speedOverride': '',
                            'segmentsContainer:segments:0:speed-overrides:2:speedOverride': '',
                            'segmentsContainer:segments:0:speed-overrides:3:speedOverride': '',
                            'segmentsContainer:segments:0:speed-overrides:4:speedOverride': '',
                            'segmentsContainer:segments:0:speed-overrides:5:speedOverride': '',
                            'segmentsContainer:segments:0:speed-overrides:6:speedOverride': ''}
        t_url = 'IFormSubmitListener-tabs-panel-newFlight-flightPlanning-flight.planning.form'
        # 迷惑大赏环节，我自己也不知道这bug什么鬼
        if t_url not in WeekPlanPage.text:
            t_url_1 = 'IFormSubmitListener-tabs-panel-newFlight-flightNumber-newNumber-aircraft.newflight.number'
            WeekPlanPage = self.logonSession.post(current_random + t_url_1, data=first_post_data,
                                                  verify=Debug_Allow_HTTPS_Verify, timeout=10000)
            current_random = self.getCurrentRandom(WeekPlanPage.url, WeekPlanPage.text)

        # 加速或减速的判断
        if SpeedConfig != 1:
            if SpeedConfig > 1:
                the_url = current_random + 'ILinkListener-tabs-panel-newFlight-flightPlanning-flight.planning.form-segmentsContainer-segments-0-speeds~set~max'
            else:
                the_url = current_random + 'ILinkListener-tabs-panel-newFlight-flightPlanning-flight.planning.form-segmentsContainer-segments-0-speeds~set~min'
            WeekPlanPage = self.logonSession.get(the_url, verify=Debug_Allow_HTTPS_Verify, timeout=10000,
                                                 proxies=LocalProxier)
            current_random = self.getCurrentRandom(WeekPlanPage.url, WeekPlanPage.text)

        def Recursion_GetSpecialID_B(root: bs4_tag):
            # 获取令人厌烦的隐藏ID参数，它长这样"idXX_XX_X"
            try:
                if root.attrs.get('action', '').endswith(t_url):
                    t_name = root.contents[0].contents[0].attrs.get('name')
                    second_post_data[t_name] = ''
                    return
                elif root.attrs.get('name', '') == 'button-submit':  # 提取特定文字
                    second_post_data['button-submit'] = root.attrs.get('value')
                    return
                elif root.attrs.get('name', '') == 'segmentSettings:0:originTerminal' and SrcTerminal not in ('T1', ''):
                    # 出发航站楼
                    for t_unit in root.children:
                        if t_unit.getText().startswith(SrcTerminal.upper()):
                            second_post_data['segmentSettings:0:originTerminal'] = t_unit.attrs.get('value')
                            return
                elif root.attrs.get('name', '') == 'segmentSettings:0:destinationTerminal' and \
                        DstTerminal not in ('T1', ''):
                    # 到达航站楼
                    for t_unit in root.children:
                        if t_unit.getText().startswith(DstTerminal.upper()):
                            second_post_data['segmentSettings:0:destinationTerminal'] = t_unit.attrs.get('value')
                            return
                elif root.name == 'input' and root.attrs.get('name',
                                                             '') == 'segmentsContainer:segments:0:speed-overrides:0:speedOverride' and \
                        SpeedConfig != 1:
                    # 速度获取
                    current_speed = root.attrs.get('value', '')
                    for i in range(7):
                        second_post_data[
                            'segmentsContainer:segments:0:speed-overrides:%d:speedOverride' % i] = current_speed
            finally:
                for t_unit in root.children:
                    if isinstance(t_unit, bs4_tag):
                        Recursion_GetSpecialID_B(t_unit)

        for unit in BeautifulSoup(self.DeleteALLChar(WeekPlanPage.text), 'html5lib'):
            if isinstance(unit, bs4_tag):
                Recursion_GetSpecialID_B(unit)
        # 获取了周计划排班页面的特殊ID
        # 接下来对出发时刻和到达时刻进行检查
        check_slots = self.checkDepartureAndArrivalSlots(WeekPlanPage.text)
        second_post_data.update({'segmentSettings:0:newDeparture:hours': first_post_data['departure:hours'],
                                 'segmentSettings:0:newDeparture:minutes': first_post_data['departure:minutes']})
        if check_slots.get('DepartureSlots') or check_slots.get('ArrivalSlots'):
            # 检测到时刻表异常，启动延迟解决方案
            self.callback_printLogs('检测到航机%s有时刻表异常，正在尝试解决中。' %
                                    self.cache_search_fleets.get(AirplaneURL, {}).get('NickName', ''))
            # 调试信息
            if DepartHour == -1 and DepartMinute == -1:
                self.callback_printLogs('DEBUG: 系统推荐时间为 %d: %.2d。' % (int(first_post_data['departure:hours']),
                                                                      int(first_post_data['departure:minutes'])))
            else:
                self.callback_printLogs('DEBUG: 玩家设定时间为 %d: %.2d。' % (DepartHour, DepartMinute))
            t_hours = int(first_post_data['departure:hours'])
            flag_update_hour = False  # 指示是否更新过小时了
            t_origin_minute = int(first_post_data['departure:minutes'])
            t_minute = (t_origin_minute + 5) % 60
            t_url = 'IBehaviorListener.0-tabs-panel-newFlight-flightPlanning-flight.planning.form-segmentSettings-0-newDeparture-minutes'
            t_header = {'Wicket-Ajax': 'true', 'X-Requested-With': 'XMLHttpRequest',
                        'Wicket-Ajax-BaseURL': WeekPlanPage.url.split('/app/')[1],
                        'Wicket-FocusedElementId':
                            WeekPlanPage.text.split(t_url + '"')[1].split('"c":"')[1].split('"')[0]}
            t_header.update(self.logonSession.headers.copy())
            for i in range(5):  # 尝试5次排班后，如果时刻表仍有问题，就放弃
                self.callback_printLogs('正在进行第 %d 次尝试，尝试时间为 %d: %.2d。' % (i + 1, t_hours, t_minute))
                if t_minute <= t_origin_minute and not flag_update_hour:
                    t_hours = (t_hours + 1) % 24
                    t_hour_url = 'IBehaviorListener.0-tabs-panel-newFlight-flightPlanning-flight.planning.form-segmentSettings-0-newDeparture-hours'
                    t_hour_header = {'Wicket-Ajax': 'true', 'X-Requested-With': 'XMLHttpRequest',
                                     'Wicket-Ajax-BaseURL': WeekPlanPage.url.split('/app/')[1],
                                     'Wicket-FocusedElementId':
                                         WeekPlanPage.text.split(t_hour_url + '"')[1].split('"c":"')[1].split('"')[0]}
                    t_hour_header.update(self.logonSession.headers.copy())
                    self.logonSession.post(current_random + t_hour_url, headers=t_hour_header, proxies=LocalProxier,
                                           data={'segmentSettings:0:newDeparture:hours': str(t_hours)},
                                           verify=Debug_Allow_HTTPS_Verify)
                    flag_update_hour = True
                SlotsResponse = self.logonSession.post(current_random + t_url, headers=t_header,
                                                       verify=Debug_Allow_HTTPS_Verify,
                                                       data={'segmentSettings:0:newDeparture:minutes': str(t_minute)})
                # 得到的结果是XML里夹的HTML表格的一部分，被去掉了<table>标签
                check_slots = self.checkDepartureAndArrivalSlots('<table>%s</table>' %
                                                                 SlotsResponse.text.split(']]></component>')[0].split(
                                                                     '><![CDATA[')[1])
                if not (check_slots.get('DepartureSlots') or check_slots.get('ArrivalSlots')):
                    self.callback_printLogs('航机%s时刻表异常已被解决。' %
                                            self.cache_search_fleets.get(AirplaneURL, {}).get('NickName', ''))
                    second_post_data.update({'segmentSettings:0:newDeparture:hours': str(t_hours),
                                             'segmentSettings:0:newDeparture:minutes': str(t_minute)})
                    break
                t_minute = (t_minute + 5) % 60
        # 无论是否解决，都要继续执行
        # 移除排班计划表，默认一周全排
        second_post_data.update({'days:daySelection:0:ticked': 'on', 'days:daySelection:1:ticked': 'on',
                                 'days:daySelection:2:ticked': 'on', 'days:daySelection:3:ticked': 'on',
                                 'days:daySelection:4:ticked': 'on', 'days:daySelection:5:ticked': 'on',
                                 'days:daySelection:6:ticked': 'on',
                                 'segmentsContainer:segments:0:departure-offsets:0:departureOffset': '0',
                                 'segmentsContainer:segments:0:departure-offsets:1:departureOffset': '0',
                                 'segmentsContainer:segments:0:departure-offsets:2:departureOffset': '0',
                                 'segmentsContainer:segments:0:departure-offsets:3:departureOffset': '0',
                                 'segmentsContainer:segments:0:departure-offsets:4:departureOffset': '0',
                                 'segmentsContainer:segments:0:departure-offsets:5:departureOffset': '0',
                                 'segmentsContainer:segments:0:departure-offsets:6:departureOffset': '0'})
        t_url = 'IFormSubmitListener-tabs-panel-newFlight-flightPlanning-flight.planning.form'
        last_result = self.logonSession.post(current_random + t_url, data=second_post_data, proxies=LocalProxier,
                                             verify=Debug_Allow_HTTPS_Verify, timeout=10000)
        # 建立了一条新航线
        return {'AirplaneURL': last_result.url, 'LastResponse': last_result,
                'AllowAutoFlightPlan': self.checkMaintenanceRatio(last_result.text),
                'UnusableSlots': check_slots.get('DepartureSlots') or check_slots.get(
                    'ArrivalSlots')}  # 好像可以重复调用API建立多航线

    def checkMaintenanceRatio(self, htmlText: str):
        """检查排班后的维护比例是否低于100%，如果低于，就发出提示（返回是否继续进行自动排班的提示）"""
        result_list = []

        def Recursion_GetMaintenanceRatioInfo(root: bs4_tag):
            if root.name == 'th' and root.getText() in ('Maintenance ratio', '維護比例'):
                t1: str = root.parent.contents[1].contents[0].getText()
                if float(t1.replace('%', '').replace(',', '').strip()) < 100:
                    result_list.append('Warning')
                return
            for t_unit in root:
                if isinstance(t_unit, bs4_tag):
                    Recursion_GetMaintenanceRatioInfo(t_unit)

        for unit in BeautifulSoup(self.DeleteALLChar(htmlText), 'html5lib'):
            if isinstance(unit, bs4_tag):
                Recursion_GetMaintenanceRatioInfo(unit)
        if len(result_list) > 0:
            return False
        return True

    def checkDepartureAndArrivalSlots(self, htmlText: str):
        result = {'DepartureSlots': False, 'ArrivalSlots': False}
        flag_departure = []  # 这里考虑到到达时刻排在出发时刻下边（元素顺序），所以可以采用标志判断

        def Recursion_GetSlotsInfo(root: bs4_tag):
            if root.name == 'a' and root.attrs.get('href', '').endswith('/slots'):
                for line in root.parent.parent.contents[1:]:
                    if 'bad' in line.contents[0].attrs.get('class'):
                        if len(flag_departure) == 0:
                            result['DepartureSlots'] = True
                        else:
                            result['ArrivalSlots'] = True
                        break
                flag_departure.append(1)
                return
            for t_unit in root.children:
                if isinstance(t_unit, bs4_tag):
                    Recursion_GetSlotsInfo(t_unit)

        for unit in BeautifulSoup(self.DeleteALLChar(htmlText), 'html5lib'):
            if isinstance(unit, bs4_tag):
                Recursion_GetSlotsInfo(unit)
        return result

    def CommitFlightPlan(self, AirplaneURL: str, UserSelect: int = 1, LastResponse: Response = None):
        """
        提交航班计划到系统，默认为1，即立即执行
        :param AirplaneURL: 排班URL，执行完排班后返回的URL
        :param UserSelect: 用户选择，一般只介于1~4之间
        :param LastResponse: 排班结束后返回的响应块，可重复使用
        """
        # 有四种操作可以选择：
        # 1 - 立即执行航班计划
        # 2 - 延迟三天执行航班计划
        # 3 - 锁定航班计划
        # 4 - 清空航班计划
        if isinstance(LastResponse, Response):
            FlightPlanPage = LastResponse
        else:
            FlightPlanPage = self.logonSession.get(AirplaneURL, verify=Debug_Allow_HTTPS_Verify, timeout=10000,
                                                   proxies=LocalProxier)
        current_random = self.getCurrentRandom(FlightPlanPage.url, FlightPlanPage.text)
        t_url = 'IFormSubmitListener-tabs-panel-visualFlightPlan-action'
        post_data = {'select': str(UserSelect)}

        def Recursion_GetSpecialID(root: bs4_tag):
            if root.name == 'form' and root.attrs.get('action', '').endswith(t_url):
                post_data[root.contents[0].contents[0].attrs.get('name')] = ''
                return
            for t_unit in root:
                if len(post_data) >= 2:
                    return
                if isinstance(t_unit, bs4_tag):
                    Recursion_GetSpecialID(t_unit)

        for unit in BeautifulSoup(self.DeleteALLChar(FlightPlanPage.text), 'html5lib'):
            if len(post_data) >= 2:
                break
            if isinstance(unit, bs4_tag):
                Recursion_GetSpecialID(unit)
        t_url = current_random + t_url
        self.logonSession.post(t_url, data=post_data, verify=Debug_Allow_HTTPS_Verify, timeout=10000,
                               proxies=LocalProxier)

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

    # UI友好函数
    def MakeSingleFlightPlan(self, SrcAirport: str, DstAirport: str, Price: int, Service: str,
                             DepartureTime: str = '', TerminalConfig: tuple = ('T1', 'T1'),
                             speed_config: str = 'Normal', callback_AskQuestion=None):
        """
        根据更通俗易懂的描述转换为程序设置
        :param speed_config: 速度设置
        :param SrcAirport: 出发机场，可以输入机场的三字母简称或全称（全称是AS上的机场全名）
        :param DstAirport: 目的机场，可以输入机场的三字母简称或全称（全称是AS上的机场全名）
        :param Price: 价格系数，如果想使用110%的价格系数，请输入110即可
        :param Service: 服务系数，您应当输入在AS中明确定义的服务方案名称，否则将使用默认值Standard
        :param DepartureTime: 出发时间，当您希望在UTC时间20点35分起飞的时候，请输入20:35，若您想使用系统推荐时间，请放空
        :param callback_AskQuestion: 回调函数，用于输入问题并获得用户响应
        :param TerminalConfig: 航站楼参数，选择出发和目的地的航站楼
        :return: 一个字典，包含了函数的各种信息
        """
        if SrcAirport not in self.cache_AirportInfo.keys():
            for unit in self.cache_AirportInfo.keys():
                if SrcAirport in unit:
                    SrcAirport = unit
                    break
            if SrcAirport not in self.cache_AirportInfo.keys():
                raise Exception('无法确定出发机场的名字，请检查输入是否有误。')
        if DstAirport not in self.cache_AirportInfo.keys():
            for unit in self.cache_AirportInfo.keys():
                if DstAirport in unit:
                    DstAirport = unit
                    break
            if DstAirport not in self.cache_AirportInfo.keys():
                raise Exception('无法确定到达机场的名字，请检查输入是否有误。')
        if not isinstance(Price, int):
            Price = 100
        if not (50 <= Price <= 200):
            try:
                if callable(callback_AskQuestion):
                    Price = int(callback_AskQuestion('价格系数仅限于50到200之间，请输入50到200之间的正整数：'))
                if not (50 <= Price <= 200):
                    Price = 100
            except:
                Price = 100
        if Service not in self.cache_ServiceInfo.keys():
            if callable(callback_AskQuestion):
                for unit in self.cache_ServiceInfo.keys():
                    if Service in unit:
                        if callback_AskQuestion('请确认是否选择该项服务 %s，您填写的是 %s。(Y/N)' % (unit, Service)
                                                ).upper() == 'Y':
                            Service = unit
                            break
                if Service not in self.cache_ServiceInfo.keys():
                    Service = self.default_service_name
            else:
                Service = self.default_service_name
        DepartureHour = -1
        DepartureMinute = -1
        if isinstance(DepartureTime, str) and len(DepartureTime) > 0:
            if DepartureTime.count(':') != 1:
                from datetime import datetime
                raise Exception('请输入正确的时间格式！例如 %s。' % datetime.now().strftime('%M:%S'))
            DepartureTime = DepartureTime.replace(' ', '').split(':')
            try:
                DepartureHour = int(DepartureTime[0])
                DepartureMinute = int(DepartureTime[1])
            except ValueError:
                raise Exception('请输入正确的时间数字，不要夹带字母等非数字！')
        return {'Src': SrcAirport, 'Dst': DstAirport, 'Price': Price, 'Service': Service,
                'Hour': DepartureHour, 'Minute': DepartureMinute, 'SrcTerminal': TerminalConfig[0],
                'DstTerminal': TerminalConfig[1], 'Speed': self.const_speed_config.get(speed_config, 1)}

    def UI_AutoMakeFlightPlan(self, AirplaneURL: str, configList: list, delayExecute: bool = False):
        """
        UI友好型航班自动管理系统的统一服务接口，但目前仍需要提供需排班的飞机对应的排程URL才能排班
        :param AirplaneURL: 需要自动排班的航机的排程URL，由SearchFleets函数提供
        :param configList: 设置列表，请使用MakeSingleFlightPlan生成多个，或使用Experimental_MakeFlightPlanConfig函数
        :param delayExecute: 是否延迟执行排班。若设为True，将在排班正常结束（维护比仍高于100）后三天后执行排班计划
        """
        t1 = self.BuildNewAirlinePlan(AirplaneURL, configList[0].get('Src'), configList[0].get('Dst'),
                                      configList[0].get('Price'), configList[0].get('Service'),
                                      configList[0].get('Hour'), configList[0].get('Minute'),
                                      SrcTerminal=configList[0].get('SrcTerminal'),
                                      DstTerminal=configList[0].get('DstTerminal'),
                                      SpeedConfig=configList[0].get('Speed'))
        flag_UnusableSlots = False
        for line in configList[1:]:
            if not t1.get('AllowAutoFlightPlan'):
                self.callback_printLogs('由于触发了低维护比规则，已对航机%s终止排程。' %
                                        self.cache_search_fleets.get(AirplaneURL, {}).get('NickName', ''))
                break
            if t1.get('UnusableSlots'):
                self.callback_printLogs('航班%s在排程%s到%s遇到了时刻表异常，无法解决。' % (
                    self.cache_search_fleets.get(AirplaneURL, {}).get('NickName', ''),
                    line.get('Src'), line.get('Dst')))
                flag_UnusableSlots = True
            t1 = self.BuildNewAirlinePlan(AirplaneURL, line.get('Src'), line.get('Dst'), line.get('Price'),
                                          line.get('Service'), line.get('Hour'), line.get('Minute'),
                                          SrcTerminal=line.get('SrcTerminal'), DstTerminal=line.get('DstTerminal'),
                                          LastResponse=t1.get('LastResponse'), SpeedConfig=line.get('Speed'))
        if t1.get('UnusableSlots'):
            self.callback_printLogs('航班%s在排程%s到%s遇到了时刻表异常，无法解决。排程已结束，但未执行。' % (
                self.cache_search_fleets.get(AirplaneURL, {}).get('NickName', ''),
                configList[-1].get('Src'), configList[-1].get('Dst')))
        elif flag_UnusableSlots:
            self.callback_printLogs('航班%s由于无法解决的时刻表异常，排程已结束，但未执行。' % (
                self.cache_search_fleets.get(AirplaneURL, {}).get('NickName', '')))
        elif t1.get('AllowAutoFlightPlan'):
            if delayExecute:
                user_commit = 2
            else:
                user_commit = 1
            self.CommitFlightPlan('', user_commit, t1.get('LastResponse'))
            self.callback_printLogs('航机%s排程已正常结束，并提交执行。' %
                                    self.cache_search_fleets.get(AirplaneURL, {}).get('NickName', ''))
        else:
            self.callback_printLogs('低维护比警告！航机%s排程已正常结束，但未被执行。' %
                                    self.cache_search_fleets.get(AirplaneURL, {}).get('NickName', ''))

    def Experimental_MakeFlightPlanConfig(self, FlightPath: str, ServiceList: list, PriceList: list,
                                          FirstDepartureTime: str, TerminalConfig: list = [],
                                          SpeedConfig: tuple = ('Normal')):
        """
        警告：该函数为实验性函数，由此产生的任何非预期结果不对此负任何责任。
        从更通俗易懂的航线，可循环使用的服务列表次序和价格次序中生成设置。
        :param FlightPath: 航班路径，中间用'-'连接，比如“HKG-SIN-CMB”
        :param ServiceList: 服务名称列表，请确保您输入了正确的名称，否则重置为Standard
        :param PriceList: 价格列表，里面必须全都是数字，否则重置为100
        :param FirstDepartureTime: 第一次的起飞时间，若起飞时间为10点36分，请输入10:36
        :param TerminalConfig: 航站楼参数，请使用如下形式[('T2', 'T2')]，可输入航站楼全称或规范化简称
        :param SpeedConfig: 速度设置参数，请在每个格填入'Min'（最小速度）、'Normal'（最佳速度）或'Max'（最大速度）
        :return: 设置块，可直接填入UI_AutoMakeFlightPlan函数
        """

        def getTerminalUnit(id: int):
            if isinstance(TerminalConfig, list) and len(TerminalConfig) > id:
                if isinstance(TerminalConfig[id], tuple) and len(TerminalConfig[id]) == 2:
                    if isinstance(TerminalConfig[id][0], str) and isinstance(TerminalConfig[id][1], str):
                        return TerminalConfig[id]
            return 'T1', 'T1'

        FlightPath = FlightPath.split('-')
        result = [self.MakeSingleFlightPlan(FlightPath[0], FlightPath[1], PriceList[0], ServiceList[0],
                                            DepartureTime=FirstDepartureTime, TerminalConfig=getTerminalUnit(0),
                                            speed_config=SpeedConfig[0])]
        for airportID in range(1, len(FlightPath) - 1):
            result.append(self.MakeSingleFlightPlan(FlightPath[airportID], FlightPath[airportID + 1],
                                                    PriceList[airportID % len(PriceList)],
                                                    ServiceList[airportID % len(ServiceList)],
                                                    TerminalConfig=getTerminalUnit(airportID),
                                                    speed_config=SpeedConfig[airportID % len(SpeedConfig)]))
        return result

    def callback_askQuestion(self, question: str):
        # 一个示例的询问函数
        return input(question)

    def callback_printLogs(self, log: str):
        # 一个示例的日志输出函数
        print(log)
