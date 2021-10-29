import sqlite3
from threading import Thread

import requests
from bs4 import BeautifulSoup
from bs4.element import Tag as bs4_Tag

max_thread_workers = 5


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

        for unit in BeautifulSoup(self.DeleteALLChar(requests.get(first_url).text), 'html5lib'):
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

        for unit in BeautifulSoup(self.DeleteALLChar(requests.get(target_url).text), 'html5lib'):
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

        for unit in BeautifulSoup(self.DeleteALLChar(requests.get(target_url).text), 'html5lib'):
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

            for unit in BeautifulSoup(self.DeleteALLChar(logonSession.get(first_url).text), 'html5lib'):
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
                for unit in BeautifulSoup(self.DeleteALLChar(logonSession.get(second_url_list.get(line)).text),
                                          'html5lib'):
                    if isinstance(unit, bs4_Tag):
                        Recursion_GetSingleFamilyAirplaneInfo(unit)
                t_sql.commit()
                self.callback_outputLog('已完成对航机 %s 家族的爬取。' % line)
            t_sql.close()
        self.flag_price_ok = True

    @staticmethod
    def DeleteALLChar(html_str: str) -> str:
        # 这仅仅是使得解析器解析时不会再碰到多余的空格
        html_str = html_str.replace('\t', '').replace('\r', '').replace('\n', '')  # 去除常见的大空格和换行
        while '  ' in html_str:  # 双空格合并为一个空格
            html_str = html_str.replace('  ', ' ')
        return html_str.replace('> <', '><')  # 去除标签之间的空格

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
        return result_list

# if __name__ == '__main__':
#     from time import sleep
#     calcService = CalcAirplaneProperty('Otto', input('Username of Otto:'), input('Password of Otto'))
#     calcService.getAirplaneInfoIndex()
#     while len(calcService.cache_CountryIndex) > 0:
#         sleep(30)
#     Thread(target=calcService.thread_getAirplanePrice).start()
#     calcService.getAirCompanyInfoIndex()
#     while len(calcService.cache_AirCompanyURL) > 0:
#         sleep(30)
#     while not calcService.flag_price_ok:
#         sleep(30)
#     sleep(10)
#     print('企业\t资产负债表')
#     for line in calcService.CalcBalanceSheet():
#         print('%s\t%.2f K AS$' % (line[0], line[1] / 1000))
