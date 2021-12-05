import openpyxl

from NewFlightPlanningSystem import NewFlightPlanningSystem
from PublicCode import TranslateCHTtoCHS as Translate
from PublicCode import openpyxl_ConfigAlignment


class FlightPlanningSystemBaseOnExcel(NewFlightPlanningSystem):

    def GenerateExcelTemplateAndOutput(self, SavePath: str):
        """
        导出排班模板数据并生成Excel文档。
        :param SavePath: 模板文件的保存路径
        """
        if len(self.cache_info) < 1:
            self.basic_ReportError('没有收集任何信息，无需导出。')
            return
        outputWorkbook = openpyxl.Workbook()
        self.InitHelpTextInExcel(outputWorkbook)
        self.InitStationsInfoInExcel(outputWorkbook)
        self.InitFlightTemplateInExcel(outputWorkbook)
        try:
            outputWorkbook.save(SavePath)
        except:
            from datetime import datetime
            SavePath = datetime.now().strftime('%Y%m%d_%H%M%S.xlsx')
            outputWorkbook.save(SavePath)
        finally:
            self.basic_ShowProgress('排班模板已保存到%s中。' % SavePath)
            outputWorkbook.close()

    def InitHelpTextInExcel(self, newWorkbook: openpyxl.Workbook):
        """初始化帮助信息，并将服务方案示例写入当前表格"""
        help_Text = [('列名', '帮助说明'), ('所属公司', '此航机所属的企业的名称。'), ('航机型号', '此航机的航机型号。'), ('航机编号', '此航机在游戏中的唯一注册编号。'),
                     ('航机健康度', '此航机的当前健康度。'), ('航机维护比', '此航机在排程之前的预期维护比。'), ('航机机龄', '此航机的服役年龄。'),
                     ('航机任务', '航机当前的任务，停放或处于飞行中。'), ('位置', '此航机目前的机场。'), ('排程状态', '当前航机的排程状态，正常或未执行或出现错误。'), ('', ''),
                     ('出发时间', '航机的出发时间，一般只需要指定第一班航班的出发时间即可。'),
                     ('出发机场', '航机的出发机场，第一班不填则默认为到达机场（若航班正在飞行）或当前待机机场。后续不填则视为前一班的目的机场。'),
                     ('出发航站楼', '出发的航站楼，请根据实际情况处理，不填或填错默认为T1。'), ('目的机场', '航机的目的机场。'),
                     ('目的航站楼', '到达的航站楼，请根据实际情况处理，不填或填错默认为T1。'), ('价格系数', '价格系数，请填写数字[50, 200]。'),
                     ('服务方案', '服务方案，请在下面的表单里寻找内容并确定填写一致，否则程序无法识别。'),
                     ('加速/减速', '仅支持最高速和最低速，不填则为游戏推荐的最佳巡航速度。'),
                     ('周计划排班', '请根据实际需要填写，使用1234567来区分周一到周日。例如1237代表飞周一周二周三周日，不飞周四周五周六。'),
                     ('备注', '可以随意填写，程序不会处理这部分的内容。')]
        first_sheet = newWorkbook.active
        first_sheet.title = '帮助文档'
        first_sheet.column_dimensions['A'].width = (max([len(i[0]) for i in help_Text]) + 1) * 2
        first_sheet.column_dimensions['B'].width = (max([len(i[1]) for i in help_Text]) + 1) * 2
        for line in help_Text:
            first_sheet.append(line)
        # 初始化帮助文档后，初始化服务方案
        first_sheet.append(('',))  # 空一行
        service_list = []
        for subCompany in self.cache_info.keys():
            if 'Service' in self.cache_info.get(subCompany).keys():
                service_list.append(['', '', subCompany] + self.cache_info.get(subCompany).get('Service'))
        first_sheet.append(('', '', '企业名', '服务方案参考（每格为一个方案名）'))
        merge_width = max([len(i) - 3 for i in service_list])
        if merge_width > 1:
            first_sheet.merge_cells('D23:%s23' % chr(67 + merge_width))
        for columnID in range(merge_width + 1):
            cache_column = []
            for sub_service_list in service_list:
                if columnID + 2 < len(sub_service_list):
                    cache_column.append(len(sub_service_list[columnID + 2]))
            first_sheet.column_dimensions[chr(67 + columnID)].width = max(cache_column) + 2
        for line in service_list:
            first_sheet.append(line)

    def InitStationsInfoInExcel(self, newWorkBook: openpyxl.Workbook):
        """在排班模板中插入子公司的航站信息表"""
        for SubCompany_name in self.cache_info.keys():
            if 'StationsInfo' not in self.cache_info.get(SubCompany_name).keys():
                continue
            station_table = newWorkBook.create_sheet(SubCompany_name)
            tableHead1 = [''] * 5 + ['客运'] + [''] * 3 + ['货运']
            station_table.append(tableHead1)
            station_table.merge_cells('F1:I1')
            station_table.merge_cells('J1:M1')
            # 顶部表头处理
            tableHead2 = ('IATA代码', '机场名称', '机场所在地', '有无噪音管制', '有无宵禁',
                          '客运需求条（Bar）', '客运航厦容量', '自有设施处理量', '酬载统计',
                          '货运需求条（Bar）', '货运航厦容量', '自有设施处理量', '酬载统计',
                          '额外可用客运航站楼')
            station_table.append(tableHead2)
            # 细分表头处理
            readonly_StationsInfo: dict = self.cache_info.get(SubCompany_name).get('StationsInfo')
            all_line = []
            for IATA_Code in readonly_StationsInfo.keys():
                readonly_Station: dict = readonly_StationsInfo.get(IATA_Code)
                lineData = [IATA_Code, readonly_Station.get('Name'), Translate(readonly_Station.get('Country')),
                            ('有', '无')[(True, False).index(readonly_Station.get('IsNoiseControl'))],
                            ('有', '无')[(True, False).index(readonly_Station.get('IsCurfew'))]]
                lineData += readonly_Station.get('Passengers') + readonly_Station.get('Cargo') + ['、'.join(
                    readonly_Station.get('ExtraTerminal', []))]
                all_line.append(lineData)
            # 缓存建立完成
            column_Length = [10, max([len(i[1]) for i in all_line]), max(12, max([len(i[2]) for i in all_line])), 14,
                             10, 20, max(14, max([len(i[6]) for i in all_line])),
                             max(16, max([len(i[7]) for i in all_line])), 10, 20,
                             max(14, max([len(i[10]) for i in all_line])), max(16, max([len(i[11]) for i in all_line])),
                             max(20, max([len(i[12]) for i in all_line]))]
            for columnID in range(len(column_Length)):
                station_table.column_dimensions[chr(65 + columnID)].width = column_Length[columnID]
            # 调整列宽
            for line in all_line:
                station_table.append(line)
            openpyxl_ConfigAlignment(station_table, 'A1:N%d' % (len(all_line) + 2), 'center')
        # 完成对航站信息的序列化建表

    def InitFlightTemplateInExcel(self, newWorkBook: openpyxl.Workbook):
        """按公司填写待排班的航机信息"""
        pre_table_head_1 = ('所属公司', '航机型号', '航机健康度', '航机维护比', '航机机龄', '航机任务', '位置', 'Y/C/F', '排程状态')
        pre_table_head_2 = ('出发时间', '出发机场', '出发航站楼', '目的机场', '目的航站楼', '价格系数', '服务方案', '加速/减速', '周计划排班', '备注')
        for subCompany in self.cache_info.keys():
            subFleets: dict = self.cache_info.get(subCompany).get('Fleets', {})
            for sheet_name in subFleets.keys():
                airplane_unit: dict = subFleets.get(sheet_name)
                line_data = [subCompany, airplane_unit.get('AirType'), str(airplane_unit.get('Health')) + '%',
                             str(airplane_unit.get('MaintenanceRadio')) + '%', str(airplane_unit.get('Age')) + '年',
                             airplane_unit.get('CurrentTask'), airplane_unit.get('Location'),
                             '/'.join([str(i) for i in airplane_unit.get('Y/C/F')])]
                if isinstance(airplane_unit.get('Location'), tuple):
                    line_data[6] = airplane_unit.get('Location')[0]
                else:
                    line_data[6] = airplane_unit.get('Location')
                if not airplane_unit.get('IsNeedInit'):
                    line_data.append('正常（待排班）')
                elif airplane_unit.get('Yellow/Red'):
                    line_data.append('已排程（未执行）')
                else:
                    line_data.append('已排程（错误）')
                new_table = newWorkBook.create_sheet(sheet_name)
                new_table.append(pre_table_head_1)
                new_table.append(line_data)
                new_table['I2'].hyperlink = airplane_unit.get('url')
                new_table.append(pre_table_head_2)
                # 调整列宽
                openpyxl_ConfigAlignment(new_table, 'A1:J100', 'center')
                column_length = [max(10, len(line_data[0])) + 2, max(10, len(line_data[1])) + 2, 12, 12, 12, 10, 10, 13,
                                 20, 40]
                column_range = list("ABCDEFGHIJ")
                for columnID in range(len(column_range)):
                    new_table.column_dimensions[column_range[columnID]].width = column_length[columnID]
