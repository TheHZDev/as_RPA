from urllib.request import getproxies

from bs4.element import Tag as bs4_Tag
from requests import Session, Response

from PublicCode import GetClearHTML, CommonHTMLParser

LocalProxier = {'http': '', 'https': ''}
LocalProxier.update(getproxies())
try:
    from local_debug import flag_Debug

    Debug_Allow_TLS_Verify = not flag_Debug
except ModuleNotFoundError:
    Debug_Allow_TLS_Verify = True


class NewFlightPlanningSystem:
    cache_info = {}  # 全局信息池
    flag_no_sub_company = True  # 无子公司
    # 运行时数据
    runtime_cache_service = {}  # 运行时服务方案信息及其对应ID
    runtime_cache_stations = {}  # 运行时机场信息及其对应ID

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

    def Close(self):
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
        MainPage = self.retryGET(self.baseURL)
        if 'as-no-enterprise' in MainPage.text:
            # 这个class出现说明这个账号在该服务器没有开设企业
            self.basic_ReportError('没有设立企业！')
            return

        def parseHTML_ParseSubCompany(root: bs4_Tag, dataDict: dict):
            if root.name == 'a':
                if 'name' in root.attrs.get('class', []) and \
                        root.attrs.get('href', '').endswith('/app/enterprise/dashboard'):
                    parent_company = root.getText().strip()
                    dataDict[parent_company] = {}
                elif '/app/enterprise/dashboard?select=' in root.attrs.get('href', ''):
                    self.flag_no_sub_company = False
                    sub_company = root.getText().strip()  # 子公司名称
                    sub_company_id = root.attrs.get('href').split('dashboard?select=')[1]  # 子公司的唯一ID
                    dataDict[sub_company] = {'ID': sub_company_id}

        self.cache_info.update(CommonHTMLParser(GetClearHTML(MainPage), parseHTML_ParseSubCompany))

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
        DashboardPage = self.retryGET(self.baseURL + '/app/enterprise/dashboard')
        CurrentCompany = self.GetCurrentCompanyName(DashboardPage)
        if len(self.cache_info.get(CurrentCompany).get('Fleets', {})) == 0:
            return
        for fleet in self.cache_info.get(CurrentCompany).get('Fleets').values():
            url = fleet.get('url')
            AirlinePage = self.retryGET(url)

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
                current_random = self.getCurrentRandom(AirlinePage)
                t_url = 'IBehaviorListener.0-tabs-panel-newFlight-flightNumber-toggle~new-link'
                t_header = {'Wicket-Ajax': 'true', 'X-Requested-With': 'XMLHttpRequest',
                            'Wicket-Ajax-BaseURL': AirlinePage.url.split('/app/')[1],
                            'Wicket-FocusedElementId':
                                AirlinePage.text.split(t_url + '"')[1].split('"c":"')[1].split('"')[0]}
                t_url = current_random + t_url + '&_=%d' % self.getTimestamp()
                NewAirlinePage = self.retryGET(t_url, headers=t_header)

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
        first_result = self.retryGET(target_url)
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
            self.retryGET(station[1])
            self.cache_info.get(CurrentCompany).get('StationsInfo').get(station[0])['ExtraTerminal'] = \
                CommonHTMLParser(GetClearHTML(self.retryGET(station[1] + '?tabs=4')), ParseHTML_GetTerminalInfo, [])
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
        FleetsManager = self.retryGET(fleets_url)
        CurrentCompany = self.GetCurrentCompanyName(FleetsManager)
        if 'Fleets' not in self.cache_info.get(CurrentCompany).keys():
            self.cache_info.get(CurrentCompany)['Fleets'] = {}

        def parseHTML_GetFleetsInfo(root: bs4_Tag, dataDict: dict):
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
                    dataDict[RegisterID] = line_info
                return True

        self.cache_info.get(CurrentCompany).get('Fleets').update(
            CommonHTMLParser(GetClearHTML(FleetsManager), parseHTML_GetFleetsInfo))

    # 系统执行区
    """
    自动排班管理流程：
    1、首先确定需要排班的企业，使用SwitchToSubCompany函数切换到指定企业。
    2、（可选）分析全部待排班的航机的排程，确保里面的航站都是已经开设的。
    3、重新加载航线数据，包括需要使用的航站ID、服务方案ID。
    4、以航机注册号为索引，进入航班管理界面，使用任意可用新航班号码建立新航班。
    5、根据情况，使得航机减速或加速，然后有针对性地调节航班的各天起飞时刻（如果所有起飞时间都错误，先调总体的，否则调个体）。
    6、连同航机的服务方案和航站楼选择一起提交到服务端。
    7、根据选择执行或延后或锁定航班计划。
    -----------
    基类实现：
    重载信息收集（初始化功能）
    建立新航班+处理错误时刻+维护比报告
    根据参数执行航班计划
    开设新航站
    清空无用航班号码
    ---------------
    子类实现：
    切换公司+调用重载信息收集
    航站航线分析+检查开设新航站
    手动清空无用航线号码
    从子类结构化数据构建新航班
    管理航机维护比例
    """

    def EstablishNewAirline(self, SrcAirport: str, DstAirport: str, Price: int, Service: str, WeekPlan: list,
                            SrcTerminal: str = None, DstTerminal: str = None, DepartureHour: int = -1,
                            DepartureMinute: int = -1, SimpleSpeedConfig: int = 0):
        """
        根据参数建立新航班，航班号为自动获取（效率优先），可处理错误时刻问题。
        :param SrcAirport: 出发机场，可以是IATA代号
        :param DstAirport: 目的机场，可以是IATA代号
        :param Price: 价格系数，50 ~ 200
        :param Service: 服务方案
        :param WeekPlan: 周计划排班，同时影响了错误时刻处理的判断
        :param SrcTerminal: 出发航站楼
        :param DstTerminal: 目的航站楼
        :param DepartureHour: 出发时间，小时，不填使用系统推荐时间
        :param DepartureMinute: 出发时间，分钟，不填使用系统推荐时间
        :param SimpleSpeedConfig: 简单速度设置，-1表示全减速，1表示全加速，0表示常速
        :return:
        """
        pass

    def ClearUnusableAirlineNumber(self):
        """清理掉不再被任意航机所使用的航班号码，从而为新的航班创建释放空间（自动排班需要建立新航班）"""
        airlinePage_url = self.baseURL + '/app/com/numbers'
        airlinePage = self.retryGET(airlinePage_url)

        def parseHTML_GetHiddenPara(root: bs4_Tag, dataDict: dict):
            if root.name == 'form' and root.attrs.get('action', '').endswith('IFormSubmitListener-deleteUnusedForm'):
                dataDict.update(CommonHTMLParser(root, self.parseNode_GetHiddenPara))
                return True

        self.retryPOST(self.getCurrentRandom(airlinePage) + 'IFormSubmitListener-deleteUnusedForm',
                       data=CommonHTMLParser(GetClearHTML(airlinePage), parseHTML_GetHiddenPara))

    def PreCollectRuntimeAirlineBasicInfo(self, airlinePlanURL: str, lastResponse: Response = None):
        """收集航班的基础性前置信息，即航站对应表和服务方案对应表"""
        self.runtime_cache_service.clear()
        self.runtime_cache_stations.clear()
        if not isinstance(lastResponse, Response):
            lastResponse = self.retryGET(airlinePlanURL)

        def parseHTML_GetServiceInfo(root: bs4_Tag, dataDict: dict):
            if root.name == 'select' and root.attrs.get('name', '') == 'origin':
                for node in root.children:
                    if isinstance(node, bs4_Tag) and node.attrs.get('value', '') != '':
                        dataDict[node.getText().strip()] = node.attrs.get('value')
                return True

        def parseHTML_GetStationsInfo(root: bs4_Tag, dataDict: dict):
            if root.name == 'select' and root.attrs.get('name', '') == 'service':
                for node in root.children:
                    if isinstance(node, bs4_Tag) and node.attrs.get('value', '') != '':
                        dataDict[node.getText().strip()] = node.attrs.get('value')
                return True

        public_response = GetClearHTML(lastResponse)
        self.runtime_cache_service.update(CommonHTMLParser(public_response, parseHTML_GetServiceInfo))
        self.runtime_cache_stations.update(CommonHTMLParser(public_response, parseHTML_GetStationsInfo))

    def SetUpNewStation(self, NewStationNames: list):
        """
        获取信息并开设新航站，新航站名称推荐使用IATA名称
        :param NewStationNames: 新航站名称（一个或多个）
        """
        if isinstance(NewStationNames, str):
            NewStationNames = [NewStationNames]
        stationPage_url = self.baseURL + '/app/ops/stations'
        stationPage = self.retryGET(stationPage_url)
        # 循环开设新航站
        ask_url_suffix = 'IBehaviorListener.0-stations-stations.open.form-airport~group-airport~group_body-airport'
        post_url_suffix = 'IFormSubmitListener-stations-stations.open.form'

        def parseHTML_Get_Ajax_http_Header(root: bs4_Tag, dataDict: dict):
            if root.name == 'form' and root.attrs.get('action', '').endswith(post_url_suffix):
                dataDict['Wicket-Ajax'] = 'true'
                dataDict['Wicket-Ajax-BaseURL'] = 'ops' + root.attrs.get('action')[1:].split('-')[0]

                def parseNode_GetIDOfInput(node: bs4_Tag, dataDict1: dict):
                    if node.name == 'input' and node.attrs.get('name',
                                                               '') == 'airport-group:airport-group_body:airport':
                        dataDict1['Wicket-FocusedElementId'] = node.attrs.get('id')
                        return True

                dataDict.update(CommonHTMLParser(root, parseNode_GetIDOfInput))
                return True

        def parseHTML_GetHiddenPara(root: bs4_Tag, dataDict: dict):
            if root.name == 'form' and root.attrs.get('action', '').endswith(post_url_suffix):
                dataDict.update(CommonHTMLParser(root, self.parseNode_GetHiddenPara))
                return True

        def parseXML_CompareAndSelectStation(root: bs4_Tag, dataDict: dict):
            if 'airport-group:airport-group_body:airport' not in dataDict.keys() and root.name == 'li':
                if dataDict.get('name') in root.getText().strip():
                    dataDict.pop('name')
                    dataDict['airport-group:airport-group_body:airport'] = root.attrs.get('textvalue')
                    return True

        for newStation in NewStationNames:
            currentPageBS = GetClearHTML(stationPage)
            http_ajax_header = {}
            http_ajax_header.update(self.LogonSession.headers.copy())
            http_ajax_header['Referer'] = stationPage.url
            http_ajax_header['X-Requested-With'] = 'XMLHttpRequest'
            http_ajax_header.update(CommonHTMLParser(currentPageBS, parseHTML_Get_Ajax_http_Header))
            # 构建异步AJAX交互
            ask_url = self.getCurrentRandom(stationPage) + ask_url_suffix + '&q=%s&_=%d' % (
                newStation, self.getTimestamp())
            ask_result = self.retryGET(ask_url, headers=http_ajax_header)
            # 在服务器上执行模糊查找
            post_data = CommonHTMLParser(GetClearHTML(ask_result), parseXML_CompareAndSelectStation,
                                         {'name': str(newStation)})
            if 'airport-group:airport-group_body:airport' in post_data.keys():
                # 没有就是无法识别航站名称
                post_data.update(CommonHTMLParser(currentPageBS, parseHTML_GetHiddenPara))
                post_http_header = {}
                post_http_header.update(self.LogonSession.headers.copy())
                post_http_header['Referer'] = stationPage.url
                stationPage = self.retryPOST(self.getCurrentRandom(stationPage) + post_url_suffix,
                                             data=post_data, headers=post_http_header)
                self.basic_ShowProgress('新航站 %s 已成功开设。' % newStation)
            else:
                self.basic_ReportError('找不到航站 %s ，因此没有任何操作。' % newStation)

    def ExecuteAirlinePlan(self, UserSelect: int, AirplaneURL: str, LastResponse: Response = None):
        """
        执行航班计划，航班计划共有4个可选选项：
        1 - 立即执行航班计划
        2 - 延迟三天执行航班计划
        3 - 锁定航班计划
        4 - 清空航班计划
        :param UserSelect: 执行的用户选择
        :param AirplaneURL: 航机排班界面的URL
        :param LastResponse: 上次使用的响应包，通常是建立新航线后留下的
        """
        if not (1 <= UserSelect <= 4 and isinstance(UserSelect, int)):
            raise ValueError('参数UserSelect必须是1~4之间的正整数！')
        if not isinstance(LastResponse, Response):
            LastResponse = self.retryGET(AirplaneURL)
        post_data = {'select': str(UserSelect)}

        def parseHTML_GetHiddenPara(root: bs4_Tag, dataDict: dict):
            if root.name == 'form' and root.attrs.get('action', '').endswith(
                    'IFormSubmitListener-tabs-panel-visualFlightPlan-action'):
                dataDict.update(CommonHTMLParser(root, self.parseNode_GetHiddenPara))
                return True

        post_data.update(CommonHTMLParser(GetClearHTML(LastResponse), parseHTML_GetHiddenPara))
        self.retryPOST(self.getCurrentRandom(LastResponse) + 'IFormSubmitListener-tabs-panel-visualFlightPlan-action',
                       data=post_data)
        self.basic_ShowProgress('航班计划已提交。')

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
        self.retryGET(self.baseURL + '/app/enterprise/dashboard', tSession=theSession)
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
    def getCurrentRandom(CurrentPage: Response) -> str:
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
            t1 = set()
            for company in self.cache_info.keys():
                t1.update(self.cache_info.get(company).get('StationsInfo', {}).keys())
            for airportName in t1:
                if SimpleName in airportName:
                    t1.clear()
                    return airportName
        except:
            return ''

    # 基础辅助函数区
    def retryGET(self, url: str, headers: dict = None, RetryTimes: int = 3, tSession: Session = None):
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

    def retryPOST(self, url: str, data=None, json=None, headers: dict = None, RetryTimes: int = 3,
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
    def parseNode_GetHiddenPara(node: bs4_Tag, dataDict: dict):
        """当解析对象是一个Form节点的时候，可以直接用此函数获取内部特定隐藏节点值（应该是防机器人吧）"""
        if node.name == 'input' and node.attrs.get('type', '') == 'hidden' and \
                node.attrs.get('name', '').startswith('id_') and node.parent.name == 'div':
            dataDict.update({node.attrs.get('name'): ''})
            return True

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
        finally:
            pass

    def basic_ShowProgress(self, ProgressInfo: str):
        try:
            if callable(self.function_ShowProgressText):
                self.function_ShowProgressText(ProgressInfo)
        finally:
            pass