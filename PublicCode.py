from bs4 import BeautifulSoup
from bs4.element import Tag as bs4_Tag
from openpyxl.worksheet.worksheet import Worksheet
from requests import Response

Localization = {'maintenance_ratio': ('Maintenance ratio', '維護比例')}


def GetClearHTML(HTML: Response, PreFilter=None):
    """
    清除网页中干扰解析的连体空格、Tab缩进和换行，及标签之间的无意义空格
    :param HTML: 原始HTTP响应
    :param PreFilter: 字符串预处理函数，将执行此函数以初始化需要处理的文本
    :return: BeautifulSoup结构体
    """
    # 预过滤器处理
    if callable(PreFilter):
        try:
            html_str = PreFilter(HTML)
        except:
            html_str = HTML.text
    else:
        html_str = HTML.text
    # 这仅仅是使得解析器解析时不会再碰到多余的空格
    html_str = html_str.replace('\t', '').replace('\r', '').replace('\n', '')  # 去除常见的大空格和换行
    while '  ' in html_str:  # 双空格合并为一个空格
        html_str = html_str.replace('  ', ' ')
    html_str = html_str.replace('> <', '><')  # 去除标签之间的空格
    return BeautifulSoup(html_str, 'html5lib')


def CommonHTMLParser(HTML: bs4_Tag, function_Parser, DataVarTemplate=None):
    """通用HTML解析函数"""
    if not callable(function_Parser):
        raise Exception('function_Parser必须是可调用函数！')
    if DataVarTemplate is None:
        DataCache = {}
    elif hasattr(DataVarTemplate, 'copy') and callable(getattr(DataVarTemplate, 'copy')):
        DataCache = DataVarTemplate.copy()
    else:
        DataCache = DataVarTemplate

    def recursion_ParseHTML(root: bs4_Tag):
        result = function_Parser(root, DataCache)
        if isinstance(result, bool) and result:
            return
        for t_unit in root.children:
            if isinstance(t_unit, bs4_Tag):
                recursion_ParseHTML(t_unit)

    for unit in HTML.children:
        if isinstance(unit, bs4_Tag):
            recursion_ParseHTML(unit)
    return DataCache


def TranslateCHTtoCHS(CHT_Str: str):
    """繁体中文转换为简体中文"""
    try:
        import zhconv

        return zhconv.convert(CHT_Str, 'zh-cn')
    except:
        return CHT_Str


def openpyxl_ConfigAlignment(ToConfigWorksheet: Worksheet, CellRange: str, Horizontal: str = "general",
                             Vertical: str = "center"):
    """
    表格格式批量设置函数，仅考虑居中对齐之类的格式。
    :param ToConfigWorksheet: 待设置的表格
    :param CellRange: 单元格范围
    :param Horizontal: 横向对齐方式
    :param Vertical: 纵向对齐方式
    """
    if CellRange.count(':') != 1 or CellRange.count('-') > 0 or CellRange.count('.') > 0:
        raise Exception('单元格范围设置有误！')
    from openpyxl.styles import Alignment
    the_Alignment = Alignment(Horizontal, Vertical)
    x_range, y_range = openpyxl_AnalyzeRange(CellRange)
    for y in y_range:
        for x in x_range:
            ToConfigWorksheet['%s%d' % (x, y)].alignment = the_Alignment


def openpyxl_AnalyzeRange(RangeStr: str):
    """解析openpyxl对于表格范围的字符串，并返回缓存"""
    CellRange = list(RangeStr.upper().replace(':', ''))
    flag_Alpha = True
    cache_Parse = ''
    x_range = []
    y_range = []
    for ID in range(len(CellRange)):
        if (flag_Alpha and CellRange[ID].isalpha()) or (not flag_Alpha and CellRange[ID].isdecimal()):
            cache_Parse += CellRange[ID]
        else:
            # 进行语法分析
            if flag_Alpha:
                flag_Alpha = False
                x_range.append(cache_Parse)
            else:
                flag_Alpha = True
                y_range.append(int(cache_Parse))
            cache_Parse = CellRange[ID]
    if flag_Alpha:
        x_range.append(cache_Parse)
    else:
        y_range.append(int(cache_Parse))
    if y_range[1] < y_range[0]:
        y_range.reverse()
    # 纵向全是整型数，不需要继续进行转换
    new_x_range = []
    for x in x_range:
        x = list(x)
        x_int = 0
        for x_chr_ID in range(len(x)):
            x_int += (ord(x[x_chr_ID]) - 64) * (26 ** (len(x) - 1 - x_chr_ID))
        new_x_range.append(x_int)
    # 把横向的字母组合转换成十进制表示的26进制数（大写字母26个）
    x_temp = list(x_range[0])
    if new_x_range[1] < new_x_range[0]:
        new_x_range.reverse()
        x_temp = list(x_range[1])
    # 正确处理大小关系
    x_range = [''.join(x_temp)]
    x_temp.reverse()
    # 将26进制数重新转换为字母（按自增顺序）
    for i in range(new_x_range[0], new_x_range[1]):
        def SimAdd(index: int):
            # 模拟位自增方法，同时采用递归方法检查下一位
            if index >= len(x_temp):
                # 要进位但找不到，加一位
                x_temp.append('A')
            elif x_temp[index] != 'Z':
                # 正常进位
                x_temp[index] = chr(ord(x_temp[index]) + 1)
            else:
                # 该位重置，下一位进位
                x_temp[index] = 'A'
                SimAdd(index + 1)

        SimAdd(0)
        x_temp.reverse()
        x_range.append(''.join(x_temp))  # 翻转到高位以重新加权
        x_temp.reverse()

    return x_range, range(y_range[0], y_range[1] + 1)
