from urllib.request import getproxies

from bs4.element import Tag as bs4_Tag
from requests import Session, Response

from PublicCode import GetClearHTML, CommonHTMLParser

LocalProxier = {'http': '', 'https': ''}
LocalProxier.update(getproxies())
try:
    from local_debug import flag_Debug

    Debug_Allow_TLS_Verify = not flag_Debug
except:
    Debug_Allow_TLS_Verify = True


class NewFlightPlanningSystem:
    cache_info = {}  # 全局信息池
    flag_no_sub_company = True  # 无子公司

    def __init__(self, LogonSession: Session, ServerName: str, UserName: str = '', Passwd: str = '',
                 callback_ReportError=None, callback_ShowProgressText=None,
                 callback_GetUserCare=None, callback_GetUserAnswer=None):
        """
        航机排班系统（新版），功能更加精细
        :param UserName: 登陆服务器的用户名
        :param Passwd: 登陆服务器的密码
        :param ServerName: 服务器名称
        :param LogonSession: 登陆的Session
        :param callback_ReportError: 回调函数，用于向调用方友好地提交中文错误信息
        :param callback_ShowProgressText: 回调函数，用于向调用方传递友好的提示信息
        """
        from LoginAirlineSim import getBaseURL
        if isinstance(LogonSession, Session):
            self.LogonSession = LogonSession
        elif len(UserName) * len(Passwd) > 0:
            from LoginAirlineSim import LoginAirlineSim
            self.LogonSession = LoginAirlineSim(ServerName, UserName, Passwd)
        else:
            raise Exception('无法启动排班管理器！')
        # 登陆流程，过
        self.baseURL = getBaseURL(ServerName)
        if len(UserName) * len(Passwd) > 0:
            self.enableMultiSession = True
            self.MultiSessionInfo = [UserName, Passwd]
        else:
            self.enableMultiSession = False
        # 是否允许多会话模式
        self.function_ReportError = callback_ReportError  # 错误汇报
        self.function_ShowProgressText = callback_ShowProgressText  # 信息披露

    def close(self):
        """请使用该函数注销AirlineSim会话"""
        target_url = 'https://sar.simulogics.games/api/sessions/' + \
                     self.LogonSession.cookies.get('as-sid').split('_')[0]
        self.LogonSession.headers['Authorization'] = 'Bearer ' + self.LogonSession.cookies.get('as-sid')
        self.LogonSession.delete(target_url, proxies=LocalProxier)
        self.LogonSession.close()

    # 信息函数区
    def SearchInfoIntelligently(self, AutoSearchSubCompany: bool = False, ScanYellowFleet: bool = False,
                                ScanRedFleet: bool = False):
        """智能搜集所需的一切信息，可指定是否一并搜索子公司"""
        self.SearchAllSubCompany()
        if AutoSearchSubCompany:
            for sub_company in self.cache_info.keys():
                self.SwitchToSubCompany(sub_company)
                self.SearchTerminalInfo()
                self.SearchFleets(ScanYellowFleet, ScanRedFleet)
                self.SearchAirlineInfo()
            return
        # 以上是连续搜索，以下为单个搜索
        self.SearchTerminalInfo()
        self.SearchFleets(ScanYellowFleet, ScanRedFleet)
        self.SearchAirlineInfo()

    def SearchAllSubCompany(self):
        """搜索所有的子公司信息，并确认是否有建立公司、只有母公司和多子公司的情况。"""
        MainPage = self.RetryGET(self.baseURL)
        if 'as-no-enterprise' in MainPage.text:
            # 这个class出现说明这个账号在该服务器没有开设企业
            self.basic_ReportError('没有设立企业！')
            return

        def Recursion_ParseSubCompany(root: bs4_Tag):
            if root.name == 'a':
                if 'name' in root.attrs.get('class', []) and \
                        root.attrs.get('href', '').endswith('/app/enterprise/dashboard'):
                    parent_company = root.getText().strip()
                    self.cache_info[parent_company] = {}
                elif '/app/enterprise/dashboard?select=' in root.attrs.get('href', ''):
                    self.flag_no_sub_company = False
                    sub_company = root.getText().strip()  # 子公司名称
                    sub_company_id = root.attrs.get('href').split('dashboard?select=')[1]  # 子公司的唯一ID
                    self.cache_info[sub_company] = {'ID': sub_company_id}
            for t_unit in root.children:
                if isinstance(t_unit, bs4_Tag):
                    Recursion_ParseSubCompany(t_unit)

        for unit in GetClearHTML(MainPage).children:
            if isinstance(unit, bs4_Tag):
                Recursion_ParseSubCompany(unit)

    def SearchAirlineInfo(self, AutoSearchSubCompany: bool = False):
        """
        搜集航线的基本信息，包括往来机场、服务方案
        :param AutoSearchSubCompany:  是否自动扫描所有子公司的基础信息。
        """
        if AutoSearchSubCompany:
            for sub_company in self.cache_info.keys():
                self.SwitchToSubCompany(sub_company)
                self.SearchAirlineInfo()
            return
        DashboardPage = self.RetryGET(self.baseURL + '/app/enterprise/dashboard')
        CurrentCompany = self.GetCurrentCompanyName(DashboardPage)
        if len(self.cache_info.get(CurrentCompany).get('Fleets', {})) == 0:
            return
        for fleet in self.cache_info.get(CurrentCompany).get('Fleets').values():
            url = fleet.get('url')
            AirlinePage = self.RetryGET(url)

            def GetBasicInfo(root: bs4_Tag, DataList: list):
                if root.name == 'select':
                    if root.attrs.get('name', '') == 'origin':
                        for option in root.children:
                            if len(option.attrs.get('value', '')) > 0:
                                DataList[0].append(option.getText())
                    elif root.attrs.get('name', '') == 'service':
                        for option in root.children:
                            if len(option.attrs.get('value', '')) > 0:
                                DataList[1].append(option.getText())
                    return True

            airport_list, service_list = CommonHTMLParser(GetClearHTML(AirlinePage), GetBasicInfo,
                                                          [[], []])
            # 这里加一个判断，适用于那种连现有航班号都没有的情况
            if len(service_list) == 0 or len(airport_list) == 0:
                current_random = self.GetCurrentRandom(AirlinePage)
                t_url = 'IBehaviorListener.0-tabs-panel-newFlight-flightNumber-toggle~new-link'
                t_header = {'Wicket-Ajax': 'true', 'X-Requested-With': 'XMLHttpRequest',
                            'Wicket-Ajax-BaseURL': AirlinePage.url.split('/app/')[1],
                            'Wicket-FocusedElementId':
                                AirlinePage.text.split(t_url + '"')[1].split('"c":"')[1].split('"')[0]}
                t_url = current_random + t_url + '&_=%d' % self.getTimestamp()
                NewAirlinePage = self.RetryGET(t_url, headers=t_header)

                # 这还是XML文档里夹了一个HTML文档

                def StrFilter(tStr: Response):
                    return tStr.text.split(']]></component>')[0].split('><![CDATA[')[1]

                airport_list, service_list = CommonHTMLParser(GetClearHTML(NewAirlinePage, StrFilter),
                                                              GetBasicInfo, [airport_list, service_list])
            self.cache_info.get(CurrentCompany).update({'Airport': airport_list, 'Service': service_list})
            return

    def SearchTerminalInfo(self, AutoSearchSubCompany: bool = False):
        """
        搜集除T1（默认航站楼）以外的可用航站楼信息，以及所有航站的详情信息。
        :param AutoSearchSubCompany: 是否自动搜集子公司航站楼信息
        """
        if AutoSearchSubCompany:
            for sub_company in self.cache_info.keys():
                self.SwitchToSubCompany(sub_company)
                self.SearchTerminalInfo()
            return
        target_url = self.baseURL + '/app/ops/stations'
        first_result = self.RetryGET(target_url)
        CurrentCompany = self.GetCurrentCompanyName(first_result)

        def ParseHTML_GetStationsInfo(root: bs4_Tag, DataDict: dict):
            if root.name == 'tbody':
                for row in root.children:
                    if isinstance(row, bs4_Tag) and row.name == 'tr':
                        IsNoiseControl = False  # 噪音管制
                        for unit in row.contents[0].children:
                            if isinstance(unit, bs4_Tag) and unit.name == 'span':
                                IsNoiseControl = True
                                break
                        IsCurfew = False  # 宵禁
                        for unit in row.contents[1].children:
                            if isinstance(unit, bs4_Tag) and unit.name == 'span':
                                IsCurfew = True
                                break
                        # 检查有无宵禁或噪音管制
                        StationName = ''  # 航站名
                        IATA_Code = ''  # IATA代号
                        AirportURL = self.baseURL + '/app'  # 对应的机场URL
                        for unit in row.contents[2].children:
                            if isinstance(unit, bs4_Tag):
                                if unit.name == 'a':
                                    from html import unescape
                                    StationName = unescape(unit.getText())
                                    AirportURL += unit.attrs.get('href')[2:]
                                elif unit.name == 'span':
                                    IATA_Code = unit.getText()
                        # 解析了航站名称、IATA代号和机场URL
                        Country = row.contents[3].contents[0].contents[0].attrs.get('title', '')  # 国家
                        WeekDeparture = int(row.contents[4].getText().replace(',', ''))  # 周出发
                        Passengers = [row.contents[5].contents[0].attrs.get('title')[8:],
                                      row.contents[6].getText().replace(',', ''),
                                      row.contents[7].contents[0].getText().replace(',', '')]
                        # 4个参数分别代表：需求条（0~10），容量，处理量，酬载率
                        if row.contents[8].getText().strip() in ('n/a', '不適用'):
                            Passengers.append('没有数据')
                        else:
                            Passengers.append(row.contents[8].getText().strip())
                        Cargo = [row.contents[9].contents[0].attrs.get('title')[8:],
                                 row.contents[10].getText().replace(',', ''),
                                 row.contents[11].contents[0].getText().replace(',', '')]
                        if row.contents[12].getText().strip() in ('n/a', '不適用'):
                            Cargo.append('没有数据')
                        else:
                            Cargo.append(row.contents[12].getText().strip())
                        line_dict = {IATA_Code: {'Name': StationName, 'IATA': IATA_Code, 'Airport': AirportURL,
                                                 'Country': Country, 'WeekDeparture': WeekDeparture,
                                                 'Passengers': Passengers, 'Cargo': Cargo,
                                                 'IsNoiseControl': IsNoiseControl, 'IsCurfew': IsCurfew}}
                        DataDict.update(line_dict)
                return True

        cache_stations_info = CommonHTMLParser(GetClearHTML(first_result), ParseHTML_GetStationsInfo)
        self.cache_info.get(CurrentCompany)['StationsInfo'] = cache_stations_info
        ExtraTerminal = []
        for station_code in cache_stations_info.keys():
            if cache_stations_info.get(station_code).get('Passengers')[2] != '0':
                # 有自有处理容量，判定为需要识别航站楼
                ExtraTerminal.append((station_code, cache_stations_info.get(station_code).get('Airport')))

        # 获取了需要抓取航站楼的航站信息（这部分好像做得太UI友好型了）

        def ParseHTML_GetTerminalInfo(root: bs4_Tag, DataList: list):
            if root.name == 'th':
                cache_text = root.getText()
                if ('第' in cache_text and '航廈' in cache_text and cache_text != '第 1 航廈') or \
                        ('Terminal' in cache_text and 'Payload' not in cache_text and cache_text != 'Terminal 1'):
                    DataList.append('T' + cache_text.split()[1])
                return True

        for station in ExtraTerminal:
            self.RetryGET(station[1])
            self.cache_info.get(CurrentCompany).get('StationsInfo').get(station[0])['ExtraTerminal'] = \
                CommonHTMLParser(GetClearHTML(self.RetryGET(station[1] + '?tabs=4')), ParseHTML_GetTerminalInfo, [])
            # 解析额外航站楼信息完成

    def SearchFleets(self, ScanYellowFleet: bool = False, ScanRedFleet: bool = False,
                     AutoSearchSubCompany: bool = False):
        """
        智能搜集企业的待排程航班信息，并汇总。
        :param ScanYellowFleet: 是否将黄色排程钮（排程未结束或已排程但未执行）加入待排班序列
        :param ScanRedFleet: 是否将红色排程钮（排班异常）加入待排班序列
        :param AutoSearchSubCompany:  是否自动扫描所有子公司的航机排程
        """
        if AutoSearchSubCompany and not self.flag_no_sub_company:
            # 循环扫描子公司排程管理
            for sub_company in self.cache_info.keys():
                self.SwitchToSubCompany(sub_company)
                self.SearchFleets(ScanYellowFleet, ScanRedFleet)
            return
        fleets_url = self.baseURL + '/app/fleets'
        FleetsManager = self.RetryGET(fleets_url)
        CurrentCompany = self.GetCurrentCompanyName(FleetsManager)
        if 'Fleets' not in self.cache_info.get(CurrentCompany).keys():
            self.cache_info.get(CurrentCompany)['Fleets'] = {}

        def Recursion_ParseFleetsInfo(root: bs4_Tag):
            if root.name == 'a' and '/fleets/aircraft/' in root.attrs.get('href', '') and \
                    root.attrs.get('href', '').endswith('/0'):
                # 扫描到航机
                tClass = root.attrs.get('class')
                if 'btn-default' in tClass or (ScanRedFleet and 'btn-danger' in tClass) or \
                        (ScanYellowFleet and 'btn-warning' in tClass):
                    if 'btn-warning' in tClass:
                        line_info = {'IsNeedInit': True, 'Yellow/Red': True}  # 排班前需要执行清除策略
                    elif 'btn-danger' in tClass:
                        line_info = {'IsNeedInit': True, 'Yellow/Red': False}  # 排班前需要执行清除策略
                    else:
                        line_info = {'IsNeedInit': False, 'Yellow/Red': False}
                    line_info['url'] = self.baseURL + '/app' + root.attrs.get('href')[1:]
                    airplane_unit = root.parent.parent.parent.parent
                    RegisterID = airplane_unit.contents[1].contents[0].getText()
                    line_info['AirType'] = airplane_unit.contents[2].contents[0].getText()
                    if len(airplane_unit.contents[3].contents) > 1:
                        cache_location = []
                        for line in airplane_unit.contents[3].children:
                            if isinstance(line, bs4_Tag):
                                if line.name == 'a':
                                    cache_location.append(line.getText())
                                elif line.name == 'div':
                                    line_info['CurrentTask'] = line.getText()
                        line_info['Location'] = '->'.join(cache_location)
                    else:
                        line_info['CurrentTask'] = '待机'
                        line_info['Location'] = airplane_unit.contents[3].contents[0].getText()
                    line_info['Age'] = float(airplane_unit.contents[4].contents[0].getText().split()[0])
                    line_info['Health'] = float(
                        airplane_unit.contents[4].contents[1].contents[0].getText().replace('%', ''))
                    line_info['MaintenanceRadio'] = float(
                        airplane_unit.contents[4].contents[1].contents[2].getText().replace('%', '').replace(',', ''))
                    t_list = [0, 0, 0]
                    t2 = 0
                    for t1 in airplane_unit.contents[5].children:
                        if isinstance(t1, bs4_Tag) and t1.name == 'span':
                            t_list[t2] = int(t1.getText())
                            t2 += 1
                    line_info['Y/C/F'] = t_list
                    self.cache_info.get(CurrentCompany).get('Fleets')[RegisterID] = line_info
            for UNIT in root.children:
                if isinstance(UNIT, bs4_Tag):
                    Recursion_ParseFleetsInfo(UNIT)

        for unit in GetClearHTML(FleetsManager).children:
            if isinstance(unit, bs4_Tag):
                Recursion_ParseFleetsInfo(unit)

    # 系统辅助函数区
    def SwitchToSubCompany(self, SubCompanyName: str, tSession: Session = None):
        """
        切换子公司，这主要是通过改写Cookie来实现的。
        :param SubCompanyName: 要切换的子公司名称
        :param tSession: 要切换的子公司的Session，仅使用在多会话模式中
        """
        if self.flag_no_sub_company or SubCompanyName not in self.cache_info.keys():
            self.basic_ReportError('找不到要切换的子公司！')
            return
        if isinstance(tSession, Session):
            theSession = tSession
        else:
            theSession = self.LogonSession
        for cookie in theSession.cookies.keys():
            if cookie.startswith('airlinesim-selectedEnterpriseId-'):
                theSession.cookies.set(cookie, self.cache_info.get(SubCompanyName).get('ID'))
                return
        # 没找到？让对面自己加上来就行了
        self.RetryGET(self.baseURL + '/app/enterprise/dashboard', tSession=theSession)
        self.SwitchToSubCompany(SubCompanyName, theSession)  # 套娃调用

    def GetCurrentCompanyName(self, CurrentPage: Response) -> str:
        """获取当前页面上显示的公司的名称"""
        if 'as-no-enterprise' in CurrentPage.text:
            # 这个class出现说明这个账号在该服务器没有开设企业
            self.basic_ReportError('没有设立企业！')
            return ''

        def GetCurrentCompanyName(root: bs4_Tag, DataList: list):
            if root.name == 'a' and 'name' in root.attrs.get('class', []):
                DataList.append(root.contents[0].getText())
                return True

        CurrentCompany = CommonHTMLParser(GetClearHTML(CurrentPage), GetCurrentCompanyName, [])
        if len(CurrentCompany) > 0:
            return CurrentCompany[0]
        else:
            self.basic_ReportError('获取当前公司名出错！')
            return ''

    @staticmethod
    def GetCurrentRandom(CurrentPage: Response) -> str:
        """提取响应的随机数以便访问时不会出错"""
        from urllib.parse import urlparse
        url_prefix = './' + urlparse(CurrentPage.url).path.split('/')[-1] + '?' + urlparse(CurrentPage.url).query
        return CurrentPage.url + CurrentPage.text.split('Wicket.Ajax.ajax({"u":"%s' % url_prefix)[1].split('.')[0] + '.'

    def GetAirportNameBySimpleName(self, SimpleName: str):
        """
        根据指定的机场简写返回机场全称。
        :param SimpleName: 机场简称
        :return: 机场全称
        """
        try:
            t1 = set([])
            for company in self.cache_info.keys():
                t1.update(self.cache_info.get(company).get('Airport', []))
            for airportName in t1:
                if SimpleName in airportName:
                    t1.clear()
                    return airportName
        except:
            return ''

    # 基础辅助函数区
    def RetryGET(self, url: str, headers: dict = None, RetryTimes: int = 3, tSession: Session = None):
        if isinstance(tSession, Session):
            theSession = tSession
        else:
            theSession = self.LogonSession
        for RetryID in range(RetryTimes):
            try:
                if isinstance(headers, dict) and len(headers) > 0:
                    return theSession.get(url, headers=headers, timeout=120, verify=Debug_Allow_TLS_Verify,
                                          proxies=LocalProxier)
                else:
                    return theSession.get(url, timeout=120, verify=Debug_Allow_TLS_Verify, proxies=LocalProxier)
            except:
                from time import sleep
                sleep(3)
        return Response()

    def RetryPOST(self, url: str, data=None, json=None, headers: dict = None, RetryTimes: int = 3,
                  tSession: Session = None):
        if isinstance(tSession, Session):
            theSession = tSession
        else:
            theSession = self.LogonSession
        for RetryID in range(RetryTimes):
            try:
                if isinstance(headers, dict) and len(headers) > 0:
                    return theSession.post(url, headers=headers, timeout=120, verify=Debug_Allow_TLS_Verify,
                                           proxies=LocalProxier, data=data, json=json)
                else:
                    return theSession.post(url, timeout=120, verify=Debug_Allow_TLS_Verify, proxies=LocalProxier,
                                           data=data, json=json)
            except:
                from time import sleep
                sleep(3)
        return Response()

    @staticmethod
    def getTimestamp() -> int:
        """时间戳集成"""
        from time import time
        return int(time() * 1000)

    def basic_ReportError(self, ErrInfo: str):
        """
        使用可能的错误报告函数进行回调报告。
        :param ErrInfo: 错误信息字符串
        """
        try:
            if callable(self.function_ReportError):
                self.function_ReportError(ErrInfo)
        except:
            pass

    def basic_ShowProgress(self, ProgressInfo: str):
        try:
            if callable(self.function_ShowProgressText):
                self.function_ShowProgressText(ProgressInfo)
        except:
            pass
