import json
import sqlite3
from threading import Thread
from time import sleep

import requests
from bs4 import BeautifulSoup
from bs4.element import Tag as bs4_Tag

max_thread_workers = 5
basic_header = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:93.0) Gecko/20100101 Firefox/93.0'}


def retry_request(url: str, timeout: int = 60, retry_cooldown: int = 5, retry_times: int = 3, data=None):
    """
    规范化网络连接尝试规程，以解决HTTPS连接慢及服务器垃圾问题
    :param url: 要连接的目标URL，以GET的方式连接
    :param timeout: 超时时间
    :param retry_cooldown: 重试前的冷却时间
    :param retry_times: 最大尝试次数
    :param data: 要POST到服务端的数据
    """
    if timeout < 1:
        timeout = 60
    retry_cooldown = max(5, retry_cooldown)
    retry_times = max(3, retry_times)
    for i in range(retry_times):
        try:
            if data is None:
                return requests.get(url, timeout=timeout, headers=basic_header)
            else:
                return requests.post(url, data=data, timeout=timeout, headers=basic_header)
        except requests.exceptions.ConnectTimeout:
            print('连接出错，将在 %d 秒后再次重试。' % retry_cooldown)
            sleep(retry_cooldown)
    return requests.Response()


def DeleteALLChar(html_str: str) -> str:
    # 这仅仅是使得解析器解析时不会再碰到多余的空格
    html_str = html_str.replace('\t', '').replace('\r', '').replace('\n', '')  # 去除常见的大空格和换行
    while '  ' in html_str:  # 双空格合并为一个空格
        html_str = html_str.replace('  ', ' ')
    return html_str.replace('> <', '><')  # 去除标签之间的空格


class ConfigManager:

    @staticmethod
    def CreateSQL():
        create_sql = """
        CREATE TABLE IF NOT EXISTS ConfigManager(
            Module TEXT PRIMARY KEY,
            JSON_Config TEXT
        );
        """
        return create_sql

    @staticmethod
    def SaveConfig(DBPath: str, ModuleName: str, Config: dict) -> bool:
        t_sql = sqlite3.connect(DBPath)
        flag_success = True
        create_sql = """
        CREATE TABLE IF NOT EXISTS ConfigManager(
            Module TEXT PRIMARY KEY,
            JSON_Config TEXT
        );
        """
        t_sql.execute(create_sql)  # 出于便携化的要求
        try:
            Config = json.dumps(Config)
            select_sql = "SELECT COUNT(*) FROM ConfigManager WHERE Module = ?;"
            insert_sql = "INSERT INTO ConfigManager VALUES(?, ?);"
            update_sql = "UPDATE ConfigManager SET JSON_Config = ? WHERE Module = ?;"
            if t_sql.execute(select_sql, (ModuleName,)).fetchone()[0] == 1:
                t_sql.execute(update_sql, (Config, ModuleName))
            else:
                t_sql.execute(insert_sql, (ModuleName, Config))
            t_sql.commit()
        except:
            flag_success = False
        finally:
            t_sql.close()
            return flag_success

    @staticmethod
    def LoadConfig(DBPath: str, ModuleName: str) -> dict:
        Config = {}
        t_sql = sqlite3.connect(DBPath)
        try:
            select_sql = "SELECT JSON_Config FROM ConfigManager WHERE Module = ?;"
            Config = json.loads(t_sql.execute(select_sql, (ModuleName,)).fetchone()[0])
        finally:
            t_sql.close()
            return Config


class CalcAirplaneProperty:
    login_UserName = None
    login_Passwd = None
    # 缓存信息块
    cache_CountryIndex = []
    cache_AirCompanyURL = []
    cache_CabinAnalyze = {}
    flag_price_ok = False

    def __init__(self, ServerName: str, UserName: str = '', Passwd: str = ''):
        from LoginAirlineSim import ServerMap, getBaseURL
        if ServerName not in ServerMap.keys():
            raise Exception('无效的服务器名称。')
        self.baseURL = getBaseURL(ServerName)
        self.baseURL_AirCompany = self.baseURL + '/action/info/'
        self.ServerName = ServerName
        self.baseDB = ServerName + '.sqlite'
        if isinstance(UserName, str) and isinstance(Passwd, str) and len(UserName) * len(Passwd) > 1:
            self.login_Passwd = Passwd
            self.login_UserName = UserName
        self.DB_Init()

    def DB_Init(self):
        t1 = sqlite3.connect(self.baseDB)
        create_sql = """
        CREATE TABLE IF NOT EXISTS Fleets(
            AirCompany TEXT,
            AirType TEXT,
            FirstCabin INTEGER,
            BusinessCabin INTEGER,
            EconomyCabin INTEGER,
            IsRented INTEGER,
            IsDelivering INTEGER
        );
        """
        # AirCompany - 航空公司全称
        # AirType - 航机类型，即型号
        # FirstCabin - 头等舱的舱位数量
        # BusinessCabin - 商务舱的舱位数量
        # EconomyCabin - 经济舱的舱位数量
        # IsRented - 是否为租赁的航机
        # IsDelivering - 是否尚未交机
        t1.execute(create_sql)
        clear_sql = "DELETE FROM Fleets;"
        t1.execute(clear_sql)
        create_sql = """
        CREATE TABLE IF NOT EXISTS AirCompanyMap(
            AirCompany TEXT,
            ParentAirCompany TEXT
        );
        """
        # AirCompany - 子公司名称
        # ParentAirCompany - 子公司所属的母公司的名称
        t1.execute(create_sql)
        clear_sql = "DELETE FROM AirCompanyMap;"
        t1.execute(clear_sql)
        create_sql = """
        CREATE TABLE IF NOT EXISTS AirplaneInfo(
            AirType TEXT,
            MaxPassenger INTEGER,
            MaxCargo INTEGER,
            MinFlightLength INTEGER,
            MaxFlightLength INTEGER,
            Speed INTEGER,
            MinDepartureRunway INTEGER,
            MaxDepartureRunway INTEGER,
            MinArriveRunway INTEGER,
            MaxArriveRunway INTEGER,
            Price INTEGER
        );
        """
        # AirType - 航机型号
        # MaxPassenger - 最大乘客量
        # MaxCargo - 最大载货量，单位是千克
        # MinFlightLength - 最小航程，单位是千米
        # MaxFlightLength - 最大航程，单位是千米
        # Speed - 巡航速度，单位是千米每小时
        # MinDepartureRunway - 最短降落跑道长度，单位是米
        # MaxDepartureRunway - 最长降落跑道长度，单位是米
        # MinArriveRunway - 最短起飞跑道长度，单位是米
        # MaxArriveRunway - 最长起飞跑道长度，单位是米
        # Price - 航机的购买价格，租赁保证金取该数值的二十分之一
        t1.execute(create_sql)
        t1.commit()

    def getAirplaneInfoIndex(self):
        """获取所有的机队信息，还包括后面可以使用的各家航空公司的URL和航机的URL"""
        first_url = self.baseURL + '/action/info/fleets'

        def Recursion_GetAllCountryID(root: bs4_Tag):
            if root.name == 'select' and root.attrs.get('id', '') == 'country-select':
                prefix_url = first_url + '?%s=' % root.attrs.get('name')
                for t_unit in root.contents:
                    if isinstance(t_unit, bs4_Tag) and t_unit.name == 'option':
                        self.cache_CountryIndex.append(prefix_url + t_unit.attrs.get('value'))
                return
            for t_unit in root.children:
                if len(self.cache_CountryIndex) > 0:
                    return
                if isinstance(t_unit, bs4_Tag):
                    Recursion_GetAllCountryID(t_unit)

        for unit in BeautifulSoup(DeleteALLChar(retry_request(first_url).text), 'html5lib'):
            if len(self.cache_CountryIndex) > 0:
                break
            if isinstance(unit, bs4_Tag):
                Recursion_GetAllCountryID(unit)
        print('抓取国家索引完成，第一阶段结束。')
        for i in range(max_thread_workers):
            Thread(target=self.thread_getAirplaneInfo).start()

    def getAirCompanyInfoIndex(self):
        """获取所有的航空公司信息，包括该航空公司是否属于任何一家公司的母公司"""
        if len(self.cache_AirCompanyURL) > 0:
            for i in range(max_thread_workers):
                Thread(target=self.thread_getAirCompanyInfo).start()
        else:
            self.callback_outputLog('没有可获取的航空公司信息。')

    def thread_getAirplaneInfo(self):
        if len(self.cache_CountryIndex) == 0:
            return
        target_url = self.cache_CountryIndex.pop()
        result_text = ['']

        def Recursion_GetAirplaneInfo(root: bs4_Tag):
            if root.name == 'table':
                t_sql = sqlite3.connect(self.baseDB)
                insert_sql = "INSERT INTO Fleets VALUES(?,?,?,?,?,?,?);"
                for t_unit in root.children:
                    if isinstance(t_unit, bs4_Tag) and t_unit.name == 'tbody':
                        AirCompanyName: str = t_unit.contents[0].contents[0].getText()  # 解析企业数据
                        pre_AirCompany_URL: str = t_unit.contents[1].contents[0].contents[3].attrs.get('href')
                        self.cache_AirCompanyURL.append(self.baseURL_AirCompany + pre_AirCompany_URL)
                        for line in t_unit.contents[3:len(t_unit.contents) - 1]:
                            isRent = 0
                            isDelivering = 0
                            AirType: str = line.contents[1].contents[0].getText()
                            seatData = line.contents[4].getText()
                            if seatData in self.cache_CabinAnalyze.keys():
                                seatModel = self.cache_CabinAnalyze.get(seatData)  # 取缓存的已解析数据
                            else:
                                seatModel = self.AnalyzeCabinModel(seatData)
                                self.cache_CabinAnalyze[seatData] = seatModel  # 大家都来帮一把
                            comment: str = line.contents[5].getText()
                            if 'lsf' in comment:
                                isRent = 1  # 租用的，非自有
                            if 'not yet delivered' in comment:
                                isDelivering = 1  # 尚未交机
                            t_sql.execute(insert_sql, (AirCompanyName, AirType, seatModel[0], seatModel[1],
                                                       seatModel[2], isRent, isDelivering))
                        t_sql.commit()
                t_sql.close()
                return
            elif root.name == 'h3':
                result_text[0] = root.getText()
                return
            for t_unit in root.children:
                if isinstance(t_unit, bs4_Tag):
                    Recursion_GetAirplaneInfo(t_unit)

        for unit in BeautifulSoup(DeleteALLChar(retry_request(target_url).text), 'html5lib'):
            if isinstance(unit, bs4_Tag):
                Recursion_GetAirplaneInfo(unit)
        self.callback_outputLog('对国家 %s 的信息抓取完成。' % result_text[0])
        Thread(target=self.thread_getAirplaneInfo).start()  # 虚设的线程池

    def thread_getAirCompanyInfo(self):
        if len(self.cache_AirCompanyURL) == 0:
            return
        target_url = self.cache_AirCompanyURL.pop()
        result_text = ['']

        def Recursion_GetAirCompanyInfo(root: bs4_Tag):
            if root.name == 'td' and root.getText() == 'Parent company':
                if root.parent.contents[1].contents[0].getText() != 'Enterprise is a holding':
                    # 企业非控股公司，即，有一个母公司
                    ParentCompany = root.parent.contents[1].contents[0].getText()
                    CompanyName = root.parent.parent.contents[0].contents[1].contents[0].getText()
                    t_sql = sqlite3.connect(self.baseDB)
                    insert_sql = "INSERT INTO AirCompanyMap VALUES(?,?);"
                    try:
                        t_sql.execute(insert_sql, (CompanyName, ParentCompany))
                        t_sql.commit()
                    finally:
                        t_sql.close()
                    return
            elif root.name == 'td' and root.getText() == 'Name':
                result_text[0] = root.parent.contents[1].contents[0].getText()
                return
            for t_unit in root.children:
                if isinstance(t_unit, bs4_Tag):
                    Recursion_GetAirCompanyInfo(t_unit)

        for unit in BeautifulSoup(DeleteALLChar(retry_request(target_url).text), 'html5lib'):
            if isinstance(unit, bs4_Tag):
                Recursion_GetAirCompanyInfo(unit)
        self.callback_outputLog('对公司 %s 的信息抓取完成。' % result_text[0])
        Thread(target=self.thread_getAirCompanyInfo).start()

    def thread_getAirplanePrice(self):
        t_sql = sqlite3.connect(self.baseDB)
        select_sql = "SELECT COUNT(*) FROM AirplaneInfo;"
        if t_sql.execute(select_sql).fetchone()[0] > 1:
            # 不再重复抓取数据
            t_sql.close()
            return
        if isinstance(self.login_Passwd, str) and isinstance(self.login_UserName, str):
            from LoginAirlineSim import LoginAirlineSim
            logonSession = LoginAirlineSim(self.ServerName, self.login_UserName, self.login_Passwd)
            first_url = self.baseURL + '/app/aircraft/manufacturers'  # 从制造商页面爬取数据
            second_url_list = {}

            def Recursion_GetAllAirplaneFamilyInfo(root: bs4_Tag):
                if root.name == 'a' and root.attrs.get('href', '').startswith(
                        '../../action/enterprise/aircraftsFamily?id='):
                    second_url_list[root.getText()] = self.baseURL + root.attrs.get('href').replace('../..', '')
                    return
                for t_unit in root.children:
                    if isinstance(t_unit, bs4_Tag):
                        Recursion_GetAllAirplaneFamilyInfo(t_unit)

            for unit in BeautifulSoup(DeleteALLChar(logonSession.get(first_url).text), 'html5lib'):
                if isinstance(unit, bs4_Tag):
                    Recursion_GetAllAirplaneFamilyInfo(unit)
            # 抓取了所有航班家族的数据
            insert_sql = "INSERT INTO AirplaneInfo VALUES(?,?,?,?,?,?,?,?,?,?,?);"

            def Recursion_GetSingleFamilyAirplaneInfo(root: bs4_Tag):
                if root.name == 'a' and root.attrs.get('href', '').startswith('aircraftsType?id='):
                    AirType = root.getText().strip()
                    row_root = root.parent.parent
                    MaxPassenger = int(row_root.contents[1].getText().strip())
                    MaxCargo = int(row_root.contents[2].getText().replace(',', '').replace('kg', '').strip())
                    AirRange = row_root.contents[3].getText().replace('km', '').replace(',', '').strip().split('-')
                    MinFlightLength = int(AirRange[0])
                    MaxFlightLength = int(AirRange[1])
                    Speed = int(row_root.contents[4].getText().replace('km/h', '').strip())
                    AirRunway = row_root.contents[5].getText().replace('m', '').replace(',', '').strip().split('-')
                    MinDepartRunway = int(AirRunway[0])
                    MaxDepartRunway = int(AirRunway[1])
                    AirRunway = row_root.contents[6].getText().replace('m', '').replace(',', '').strip().split('-')
                    MinArriveRunway = int(AirRunway[0])
                    MaxArriveRunway = int(AirRunway[1])
                    Price = int(row_root.contents[7].getText().replace('AS$', '').replace(',', '').strip())
                    t_sql.execute(insert_sql, (AirType, MaxPassenger, MaxCargo, MinFlightLength, MaxFlightLength,
                                               Speed, MinDepartRunway, MaxDepartRunway, MinArriveRunway,
                                               MaxArriveRunway, Price))
                for t_unit in root.children:
                    if isinstance(t_unit, bs4_Tag):
                        Recursion_GetSingleFamilyAirplaneInfo(t_unit)

            for line in second_url_list.keys():
                for unit in BeautifulSoup(DeleteALLChar(logonSession.get(second_url_list.get(line)).text),
                                          'html5lib'):
                    if isinstance(unit, bs4_Tag):
                        Recursion_GetSingleFamilyAirplaneInfo(unit)
                t_sql.commit()
                self.callback_outputLog('已完成对航机 %s 家族的爬取。' % line)
            t_sql.close()
            target_url = 'https://sar.simulogics.games/api/sessions/' + \
                         logonSession.cookies.get('as-sid').split('_')[0]
            logonSession.delete(target_url)  # 自动注销会话
        self.flag_price_ok = True

    @staticmethod
    def AnalyzeCabinModel(CabinStr: str):
        if len(CabinStr) == 0:
            return 0, 0, 0
        FirstCabin = 0
        BusinessCabin = 0
        EconomyCabin = 0
        if CabinStr.startswith('F'):
            if 'C' in CabinStr and 'Y' in CabinStr:
                t1 = CabinStr[1:].split('C')
                FirstCabin = int(t1[0])
                t1 = t1[1].split('Y')
                BusinessCabin = int(t1[0])
                EconomyCabin = int(t1[1])
            elif 'C' in CabinStr:
                t1 = CabinStr[1:].split('C')
                FirstCabin = int(t1[0])
                BusinessCabin = int(t1[1])
            elif 'Y' in CabinStr:
                t1 = CabinStr[1:].split('Y')
                FirstCabin = int(t1[0])
                EconomyCabin = int(t1[1])
            else:
                FirstCabin = int(CabinStr[1:])
        elif CabinStr.startswith('C'):
            if 'Y' in CabinStr:
                t1 = CabinStr[1:].split('Y')
                BusinessCabin = int(t1[0])
                EconomyCabin = int(t1[1])
            else:
                BusinessCabin = int(CabinStr[1:])
        elif CabinStr.startswith('Y'):
            EconomyCabin = int(CabinStr[1:])
        return FirstCabin, BusinessCabin, EconomyCabin

    def callback_outputLog(self, logStr: str):
        # 预留日志输出接口
        print(logStr)

    def CalcBalanceSheet(self, SeatPrice=(4400, 1900, 500), MergeSubCompany: bool = True,
                         DescSorted: bool = True):
        """
        计算各航空公司的资产负债表\n
        :param SeatPrice: 席位价格表组，从左至右为头等舱、商务舱、经济舱
        :param MergeSubCompany: 是否归并子公司，归并后子公司资产作为母公司的一部分进行计算
        :param DescSorted: 是否降序排列，即总资产最高的将排在前面
        :return: 资产负债表的list
        """
        t_sql = sqlite3.connect(self.baseDB)
        select_sql = "SELECT DISTINCT AirCompany FROM Fleets;"
        result_dict = {}
        for AirCompany in t_sql.execute(select_sql).fetchall():
            result_dict[AirCompany[0]] = 0
        if len(result_dict) == 0:
            return []
        cache_AirPriceMap = {}
        select_sql = "SELECT AirType, Price FROM AirplaneInfo WHERE AirType in (SELECT DISTINCT AirType " \
                     "FROM Fleets);"
        for line in t_sql.execute(select_sql).fetchall():
            cache_AirPriceMap[line[0]] = line[1]
        self.callback_outputLog('计算资产中......数据缓存建立完毕！')
        # 初始化完毕
        select_sql = "SELECT AirType, FirstCabin, BusinessCabin, EconomyCabin, IsRented FROM Fleets " \
                     "WHERE AirCompany = ?;"
        for AirCompany in result_dict.keys():
            for line in t_sql.execute(select_sql, (AirCompany,)).fetchall():
                if line[4] == 1:
                    result_dict[AirCompany] += cache_AirPriceMap.get(line[0]) / 20
                else:
                    result_dict[AirCompany] += cache_AirPriceMap.get(line[0])
                result_dict[AirCompany] += line[1] * SeatPrice[0] + line[2] * SeatPrice[1] + line[3] * SeatPrice[2]
        self.callback_outputLog('计算资产中......所有航机及座位资产计算完成！')
        # 初始计算完成
        if MergeSubCompany:
            select_sql = "SELECT AirCompany, ParentAirCompany FROM AirCompanyMap;"
            cache_SubCompany = {}
            for line in t_sql.execute(select_sql).fetchall():
                cache_SubCompany[line[0]] = line[1]
            # 建立子公司映射表缓存
            t_list = []
            for line in cache_SubCompany.keys():
                if line not in result_dict.keys():
                    t_list.append(line)
            for line in t_list:
                cache_SubCompany.pop(line)
            flag_continue_merge = True
            while flag_continue_merge:
                for line in cache_SubCompany.keys():
                    if result_dict.get(line) > 0:
                        if cache_SubCompany.get(line) not in result_dict.keys():
                            result_dict[cache_SubCompany.get(line)] = 0
                        result_dict[cache_SubCompany[line]] += result_dict.get(line)
                        result_dict[line] = 0
                # 循环归并，相当于冒泡排序
                flag_continue_merge = False
                for line in cache_SubCompany.keys():
                    if result_dict.get(line) > 0:
                        # 当满足所有子公司现金都为0的时候，归并计算结束
                        flag_continue_merge = True
                        break
            for line in cache_SubCompany.keys():
                result_dict.pop(line)  # 删除资产为0的子公司
            self.callback_outputLog('计算资产中......子公司归并计算完毕！')
        result_list = []
        for AirCompany in result_dict.keys():
            result_list.append((AirCompany, result_dict.get(AirCompany)))

        def _cmp(x, y):
            if x[1] > y[1]:
                return 1
            else:
                return -1

        from functools import cmp_to_key
        result_list.sort(key=cmp_to_key(_cmp), reverse=DescSorted)
        self.callback_outputLog('计算资产中......数据已按照资产数额排列完成！')
        return result_list


class GetAirportInfo:
    flag_finish = []

    def __init__(self, ServerName: str):
        """
        一个用来抓取机场信息的小工具，没有任何其他的计算功能
        :param ServerName: 服务器名称
        """
        from LoginAirlineSim import ServerMap, getBaseURL
        from urllib.parse import urlparse
        if ServerName not in ServerMap.keys():
            raise Exception('无效的服务器名称。')
        self.baseURL = 'https://' + urlparse(getBaseURL(ServerName)).netloc + '/app/info/airports/'
        self.errorURL = '/app/wicket/page'  # URL后缀
        self.DBPath = ServerName + '.sqlite'
        self.DB_Init()
        # 判断机场信息以及有无更新
        t_sql = sqlite3.connect(self.DBPath)
        t1 = t_sql.execute('SELECT COUNT(*) FROM AirportInfo;').fetchone()[0]
        t_sql.close()
        if t1 == 0 or self.DetectAirportUpdate_Basic():
            self.DB_TRUNCATE()
            for i in range(1, max_thread_workers + 1):
                Thread(target=self.thread_getAirportInfo, args=(i,)).start()
        else:
            print('未检测到更新，且已爬取数据。若上次未能正常退出，请执行DB_TRUNCATE函数以初始化。')

    def DB_Init(self):
        create_sql = """
        CREATE TABLE IF NOT EXISTS AirportInfo(
            AirportID INTEGER,
            AirportName TEXT,
            Time_Zone INTEGER,
            IATA TEXT,
            ICAO TEXT,
            Country TEXT,
            Continent TEXT,
            Runway INTEGER,
            Airport_Size TEXT,
            Slots_per_five_minutes INTEGER,
            Slot_Availability FLOAT,
            Min_transfer_time INTEGER,
            Nighttime_ban INTEGER,
            Noise_restrictions INTEGER,
            Passengers INTEGER,
            Cargo INTEGER
        );
        """
        # AirportID - 机场的登记ID，这个是为了日后定制更新机场信息而设计
        # Time_Zone - 时区，以UTC时间作为标定
        # IATA - 国际航空运输协会（International Air Transport Association）代码
        # ICAO - 国际民用航空组织（International Civil Aviation Organization）代码
        # Country - 机场所在国名称，可惜是英文的
        # Continent - 国家所在的洲
        # Runway - 跑道长度，单位是米
        # Airport_Size - 机场大小
        # Slots_per_five_minutes - 每5分钟的时间带
        # Slot_Availability - 时间带可用百分比，应该是指示机场的繁忙程度
        # Min_transfer_time - 最小转机时间，如果这个值是-1，则表明机场禁止转机
        # Nighttime_ban - 有无宵禁
        # Noise_restrictions - 有无噪声管制
        # Passengers - 客运需求条
        # Cargo - 货运需求条
        t_sql = sqlite3.connect(self.DBPath)
        t_sql.execute(create_sql)
        t_sql.close()

    def DB_TRUNCATE(self):
        t_sql = sqlite3.connect(self.DBPath)
        t_sql.execute("DELETE FROM AirportInfo;")
        t_sql.commit()
        t_sql.close()

    def thread_getAirportInfo(self, AirportNumber: int):
        """
        实际获取机场信息的线程，没有其他的功能
        :param AirportNumber: 航班号码
        """
        # 机场是自增探索形式，如果失败了后边就不需要做了
        t_response = retry_request(self.baseURL + str(AirportNumber))
        if self.errorURL in t_response.url:
            # 这里进行二次路径探测，换句话说就是看后面还有没有，有，说明是单独误报
            flag_found = -1
            print('id为 %d 的机场不存在。' % AirportNumber)
            for i in range(1, 6):
                t_response = requests.get(self.baseURL + str(AirportNumber + max_thread_workers * i),
                                          allow_redirects=False)
                if self.errorURL not in t_response.headers.get('Location', ''):
                    flag_found = AirportNumber + i * 5
                    break
                else:
                    print('id为 %d 的机场不存在。' % (AirportNumber + max_thread_workers * i))
            if flag_found == -1:
                print('线程已退出。')
                self.flag_finish.append((AirportNumber - 1) % max_thread_workers)
            else:
                self.thread_getAirportInfo(flag_found)  # 节省线程使用量
            return
        # 具体执行
        insert_sql = "INSERT INTO AirportInfo VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?);"
        t_dict = {"Time_Zone": 0, "IATA_Code": '', "ICAO_Code": '', "Country": '', "Continent": '', "Runway": 0,
                  "Airport_Size": '', "Slots_per_five_minutes": 0, "Slot_Availability": 0, "Min_transfer_time": -1,
                  "Nighttime_ban": 0, "Noise_restrictions": 0, "Passengers": 0, "Cargo": 0, "AirportName": ''}

        def Recursion_ParseAirportInfo(root: bs4_Tag):
            if root.name == 'td':
                if root.getText() in ('時區', 'Time zone'):
                    try:
                        t_dict['Time_Zone'] = int(root.parent.contents[1].getText().replace('+', '').replace('UTC', ''). \
                                                  replace(' ', '').split(':')[0])
                    except:  # 可能遇到了格林尼治时期（UTC时间）
                        pass
                elif root.getText() in ('IATA 代號', 'IATA code'):
                    t_dict['IATA_Code'] = root.parent.contents[1].getText()
                elif root.getText() in ('ICAO 代號', 'ICAO code'):
                    t_dict['ICAO_Code'] = root.parent.contents[1].getText()
                elif root.getText() in ('國家', 'Country'):
                    t_dict["Country"] = root.parent.contents[1].contents[0].getText()
                elif root.getText() in ('洲別', 'Continent'):
                    t_dict["Continent"] = root.parent.contents[1].getText()
                elif root.getText() in ('跑道', 'Runway'):
                    t_dict["Runway"] = int(root.parent.contents[1].getText().replace(',', '').replace('m', '').strip())
                elif root.getText() in ('機場大小', 'Airport size'):
                    t_dict["Airport_Size"] = root.parent.contents[1].getText()
                # elif root.getText() in ('時間帶數 (每五分鐘)', 'Slots (per 5 minutes)'):
                elif 'Slots (per 5 minutes)' in root.getText() or '時間帶數 (每五分鐘)' in root.getText():
                    t_dict["Slots_per_five_minutes"] = int(root.parent.contents[1].getText())
                elif root.getText() in ('可用時間帶', 'Slot Availability'):
                    t_dict["Slot_Availability"] = int(root.parent.contents[1].getText().replace('%', '')) / 100
                elif root.getText() in ('最短轉機時間', 'Min. transfer time'):
                    if 'transfer impossible' not in root.parent.contents[1].contents[0].getText():
                        t1: str = root.parent.contents[1].contents[0].getText()
                        t_dict["Min_transfer_time"] = int(t1.split(':')[0]) * 60 + int(t1.split(':')[1])
                elif root.getText() in ('宵禁', 'Nighttime ban'):
                    if root.parent.contents[1].getText() not in ('無宵禁', 'no nighttime ban'):
                        t_dict["Nighttime_ban"] = 1
                elif root.getText() in ('噪音管制', 'Noise restrictions'):
                    if root.parent.contents[1].getText() not in ('無噪音管制', 'no noise restrictions'):
                        t_dict["Noise_restrictions"] = 1
                elif root.getText() in ('旅客', 'Passengers'):
                    t_dict["Passengers"] = int(root.parent.contents[1].contents[0].attrs.get('title'). \
                                               replace('demand:', '').strip())
                elif root.getText() in ('貨物', 'Cargo'):
                    t_dict["Cargo"] = int(root.parent.contents[1].contents[0].attrs.get('title'). \
                                          replace('demand:', '').strip())
            elif root.name == 'h1' and ('Airport:' in root.getText() or '機場: ' in root.getText()):
                t_dict["AirportName"] = root.getText().split(':')[1].split('(')[0].strip()
                return
            for t_unit in root.children:
                if isinstance(t_unit, bs4_Tag):
                    Recursion_ParseAirportInfo(t_unit)

        for unit in BeautifulSoup(DeleteALLChar(t_response.text), 'html5lib').children:
            if isinstance(unit, bs4_Tag):
                Recursion_ParseAirportInfo(unit)
        t_sql = sqlite3.connect(self.DBPath)
        t_sql.execute(insert_sql, (AirportNumber, t_dict["AirportName"], t_dict["Time_Zone"], t_dict["IATA_Code"],
                                   t_dict["ICAO_Code"], t_dict["Country"], t_dict["Continent"], t_dict["Runway"],
                                   t_dict["Airport_Size"], t_dict["Slots_per_five_minutes"],
                                   t_dict["Slot_Availability"],
                                   t_dict["Min_transfer_time"], t_dict["Nighttime_ban"], t_dict["Noise_restrictions"],
                                   t_dict["Passengers"], t_dict["Cargo"]))
        t_sql.commit()
        t_sql.close()
        print('对机场 %s 信息抓取完成。' % t_dict["IATA_Code"])
        Thread(target=self.thread_getAirportInfo, args=(AirportNumber + max_thread_workers,)).start()

    def DetectFinish(self):
        return len(self.flag_finish) == max_thread_workers

    def DetectAirportUpdate_Basic(self) -> bool:
        """检测机场信息是否有更新，目前比较简单，只获取最新的一个文件名。"""
        LatestFile = ['']

        def Recursion_GetLatestChangelogFileName(root: bs4_Tag):
            if root.name == 'a' and 'airport-data-changelog' in root.attrs.get('href', '').lower():
                LatestFile[0] = root.attrs.get('href')  # 有一定风险，如果日期不是按照从上到下的顺序排列时
            for t_unit in root.children:
                if isinstance(t_unit, bs4_Tag):
                    Recursion_GetLatestChangelogFileName(t_unit)

        for unit in BeautifulSoup(retry_request('https://www.airlinesim.aero/blog/files/').text, 'html5lib'):
            if isinstance(unit, bs4_Tag):
                Recursion_GetLatestChangelogFileName(unit)
        t1 = ConfigManager.LoadConfig(self.DBPath, 'GetAirportInfo')
        if t1.get('LatestAirportInfo', '') != LatestFile[0]:
            t1.update({'LatestAirportInfo': LatestFile[0]})
            ConfigManager.SaveConfig(self.DBPath, 'GetAirportInfo', t1)
            return True
        else:
            return False


class IntelligentRecommendation:
    cache_IATA_to_AirportName = {}
    retry_times_CalcAirportDistance = 0

    def __init__(self, ServerName: str, UserName: str, Passwd: str):
        from LoginAirlineSim import LoginAirlineSim, getBaseURL
        self.logonSession = LoginAirlineSim(ServerName, UserName, Passwd)
        self.DBPath = ServerName + '.sqlite'
        self.baseURL = getBaseURL(ServerName)

    def Close(self):
        target_url = 'https://sar.simulogics.games/api/sessions/' + \
                     self.logonSession.cookies.get('as-sid').split('_')[0]
        self.logonSession.delete(target_url)
        self.logonSession = None

    def Customization_CalcAirportDistance(self, SrcAirport_IATA: str):
        """
        定制版的机场距离函数，以所给机场作为中心机场，计算它到每个客运或货运至少有 5 需求的机场之间的距离。
        数据默认写入数据库中，本函数不作返回。
        :param SrcAirport_IATA: 机场的IATA代码，即常见的三字母
        """
        SrcAirport_IATA = SrcAirport_IATA.upper()
        t_sql = sqlite3.connect(self.DBPath)
        select_sql = "SELECT IATA, AirportName FROM AirportInfo WHERE Passengers >= 5 OR Cargo >= 5;"
        cache_result = {}
        t_list = []
        airport_list = []
        t_number = 1
        for airport in t_sql.execute(select_sql).fetchall():
            self.cache_IATA_to_AirportName[airport[0]] = airport[1]
            if airport[0] == SrcAirport_IATA:
                continue
            cache_result[airport[0]] = 0
            # 缓存机场名字池
            t_list.append(airport[0])
            if t_number % 2 == 0:
                airport_list.append(t_list)
                t_list = []
            t_number += 1
        if len(t_list) == 1:
            t_list.append(None)
            airport_list.append(t_list)
        create_sql = """
        CREATE TABLE IF NOT EXISTS AirportDistance(
            Airport_1 TEXT,
            Airport_2 TEXT,
            Distance INTEGER
        );
        """
        t_sql.execute(create_sql)
        t_sql.commit()
        t_sql.close()
        # 开始安排航程计算工具
        t1 = self.CalcAirportDistance(SrcAirport_IATA, airport_list[0][0], airport_list[0][1])
        for i in range(1, len(airport_list) + 1):
            cache_result[airport_list[i - 1][0]] = t1.get('First')
            try:
                cache_result[airport_list[i - 1][1]] = t1.get('Second')
            except KeyError:  # 字典引用None的时候会报出来，这个时候其实流程已经结束了
                break
            if i == len(airport_list):
                break
            t1 = self.CalcAirportDistance(SrcAirport_IATA, airport_list[i][0], airport_list[i][1],
                                          t1.get('LastResponse'))
        # 航程计算完毕，写入数据库
        insert_sql = "INSERT INTO AirportDistance VALUES(?,?,?);"
        t_sql = sqlite3.connect(self.DBPath)
        for airport in cache_result.keys():
            if airport is None or len(airport) == 0:
                continue
            t_sql.execute(insert_sql, (SrcAirport_IATA, airport, cache_result.get(airport)))
        t_sql.commit()
        t_sql.close()

    def CalcAirportDistance(self, SrcAirport_IATA: str, FirstDstAirport_IATA: str, SecondDstAirport_IATA: str = None,
                            LastResponse: requests.Response = None):
        """
        计算一个（或两个）机场到目的机场之间的航程距离
        :param SrcAirport_IATA: 参与计算的中心机场的IATA代码
        :param FirstDstAirport_IATA: 第一目的机场的IATA代码
        :param SecondDstAirport_IATA: 可选，第二目的机场的IATA代码
        :param LastResponse: 上次的响应包，内部使用
        :return: {'First': 第一目的机场到中心机场的航程，'Second': 第二目的机场到中心机场的航程, 'LastResponse': ?}
        """
        if isinstance(LastResponse, requests.Response) and '/app/com/routes/evaluation' in LastResponse.url:
            firstResponse = LastResponse
        else:
            firstResponse = self.logonSession.get(self.baseURL + '/app/com/routes/evaluation')
        post_data = {'url': '',
                     'stops:0:airport': self.cache_IATA_to_AirportName.get(FirstDstAirport_IATA, FirstDstAirport_IATA),
                     'stops:1:airport': self.cache_IATA_to_AirportName.get(SrcAirport_IATA, SrcAirport_IATA)}
        if isinstance(SecondDstAirport_IATA, str):
            post_data.update({'stops:2:airport': self.cache_IATA_to_AirportName.get(SecondDstAirport_IATA,
                                                                                    SecondDstAirport_IATA)})

        def Recursion_GetCurrentRandom(root: bs4_Tag):
            if root.name == 'form' and 'IFormSubmitListener-route~definition~form' in root.attrs.get('action', ''):
                post_data['url'] = self.baseURL + '/app/com/routes' + root.attrs.get('action')[1:]
                post_data[root.contents[0].contents[0].attrs.get('name')] = ''
                return
            for t_unit in root.children:
                if isinstance(t_unit, bs4_Tag):
                    Recursion_GetCurrentRandom(t_unit)

        for unit in BeautifulSoup(DeleteALLChar(firstResponse.text), 'html5lib').children:
            if isinstance(unit, bs4_Tag):
                Recursion_GetCurrentRandom(unit)
        post_url = post_data.pop('url')
        result = self.logonSession.post(post_url, post_data)
        result_dict = {'First': 0, 'Second': 0, 'LastResponse': result}
        first_dist_key = '../scheduling/' + FirstDstAirport_IATA.upper() + SrcAirport_IATA.upper()

        def Recursion_GetAirportDistance(root: bs4_Tag):
            if root.name == 'a' and root.attrs.get('href', '') == first_dist_key:
                result_dict['First'] = int(
                    root.parent.parent.contents[6].getText().replace('km', '').replace(',', '').strip())
                return
            elif isinstance(SecondDstAirport_IATA, str) and root.name == 'a' and \
                    ('../scheduling/' + SrcAirport_IATA.upper() +
                     SecondDstAirport_IATA.upper()) == root.attrs.get('href', ''):
                result_dict['Second'] = int(
                    root.parent.parent.contents[6].getText().replace('km', '').replace(',', '').strip())
                return
            for t_unit in root.children:
                if isinstance(t_unit, bs4_Tag):
                    Recursion_GetAirportDistance(t_unit)

        for unit in BeautifulSoup(DeleteALLChar(result.text), 'html5lib').children:
            if isinstance(unit, bs4_Tag):
                Recursion_GetAirportDistance(unit)
        if result_dict['First'] > 0:
            print('航程%s - %s计算完成，航程为 %d km。' % (SrcAirport_IATA, FirstDstAirport_IATA, result_dict['First']))
            if isinstance(SecondDstAirport_IATA, str):
                print('航程%s - %s计算完成，航程为 %d km。' % (SrcAirport_IATA, SecondDstAirport_IATA,
                                                    result_dict['Second']))
        elif self.retry_times_CalcAirportDistance < 3:
            # 直接进行一个智能回退，以解决AS的错误竞争问题
            self.retry_times_CalcAirportDistance += 1
            result_dict = self.CalcAirportDistance(SrcAirport_IATA, FirstDstAirport_IATA,
                                                   SecondDstAirport_IATA, result_dict['LastResponse'])
        self.retry_times_CalcAirportDistance = 0
        return result_dict
