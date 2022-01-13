from bs4 import BeautifulSoup
from bs4.element import Tag as bs4_Tag
from openpyxl.worksheet.worksheet import Worksheet
from requests import Response

Localization = {'maintenance_ratio': ('Maintenance ratio', '維護比例')}
Countries_UI = {'埃及': 'Egypt', '亚美尼亚': 'Armenia', '马耳他': 'Malta', '摩洛哥': 'Morocco', '马绍尔群岛': 'Marshall Islands',
                '毛里塔尼亚': 'Mauritania', '毛里求斯': 'Mauritius', '北马其顿': 'North Macedonia', '墨西哥': 'Mexico',
                '密克罗尼西亚': 'Micronesia', '摩尔多瓦': 'Moldova', '摩纳哥': 'Monaco', '阿塞拜疆': 'Azerbaijan', '蒙古': 'Mongolia',
                '莫桑比克': 'Mozambique', '缅甸': 'Myanmar', '纳米比亚': 'Namibia', '诺鲁': 'Nauru', '尼泊尔': 'Nepal',
                '新西兰': 'New Zealand', '尼加拉瓜': 'Nicaragua', '荷兰': 'Netherlands', '尼日': 'Niger', '澳大利亚': 'Australia',
                '尼日利亚': 'Nigeria', '北韩': 'North Korea', '挪威': 'Norway', '奥地利': 'Austria', '阿曼': 'Oman',
                '东帝汶': 'Timor Leste', '巴基斯坦': 'Pakistan', '帕劳': 'Palau', '巴拿马': 'Panama', '巴布亚新几内亚': 'Papua New Guinea',
                '巴哈马': 'Bahamas', '巴拉圭': 'Paraguay', '秘鲁': 'Peru', '菲律宾': 'Philippines', '波兰': 'Poland',
                '葡萄牙': 'Portugal', '卡达': 'Qatar', '卢旺达': 'Rwanda', '罗马尼亚': 'Romania', '俄罗斯': 'Russian Federation',
                '所罗门群岛': 'Solomon Islands', '巴林': 'Bahrain', '赞比亚': 'Zambia', '萨摩亚': 'Samoa',
                '圣多美和普林西比': 'Sao Tome and Principe', '沙特阿拉伯': 'Saudi-Arabia', '瑞典': 'Sweden', '瑞士': 'Switzerland',
                '塞内加尔': 'Senegal', '塞尔维亚': 'Serbia', '塞舌尔': 'Seychelles', '狮子山': 'Sierra Leone', '孟加拉': 'Bangladesh',
                '新加坡': 'Singapore', '斯洛伐克': 'Slovakia', '斯洛文尼亚': 'Slovenia', '索马里': 'Somalia', '西班牙': 'Spain',
                '斯里兰卡': 'Sri Lanka', '圣克里斯多福与尼维斯': 'Saint Kitts and Nevis', '圣卢西亚': 'Saint Lucia',
                '圣文森': 'Saint Vincent', '苏丹': 'Sudan', '巴巴多斯': 'Barbados', '南非': 'South Africa', '韩国': 'South Korea',
                '苏里南': 'Suriname', '斯威士兰': 'Eswatini', '叙利亚': 'Syria', '塔吉克': 'Tajikistan', '台湾': 'Taiwan',
                '坦桑尼亚': 'Tanzania', '泰国': 'Thailand', '多哥': 'Togo', '比利时': 'Belgium', '东加': 'Tonga',
                '特立尼达和多巴哥': 'Trinidad and Tobago', '查德': 'Chad', '捷克': 'Czech Republic', '土耳其': 'Turkey',
                '突尼斯': 'Tunisia', '土库曼': 'Turkmenistan', '图瓦卢': 'Tuvalu', '乌干达': 'Uganda', '乌克兰': 'Ukraine',
                '伯利兹': 'Belize', '匈牙利': 'Hungary', '乌拉圭': 'Uruguay', '美国': 'USA', '乌兹别克': 'Uzbekistan',
                '阿拉伯联合酋长国': 'UAE', '瓦努阿图': 'Vanuatu', '委内瑞拉': 'Venezuela', '越南': 'Viet Nam', '白俄罗斯': 'Belarus',
                '中非共和国': 'Central African Republic', '贝南': 'Benin', '津巴布韦': 'Zimbabwe',
                '塞浦路斯共和国': 'Cyprus - Republic of (greek)', '北塞浦路斯土耳其共和国': 'Cyprus - "TRNC" (turkish)',
                '黑山': 'Montenegro', '科索沃': 'Kosovo', '南苏丹': 'South Sudan', '赤道几内亚': 'Equatorial Guinea', '不丹': 'Bhutan',
                '玻利维亚': 'Bolivia', '波斯尼亚和黑塞哥维那': 'Bosnia and Herzegovina', '博茨瓦纳': 'Botswana', '巴西': 'Brazil',
                '文莱': 'Brunei', '保加利亚': 'Bulgaria', '布基纳法索': 'Burkina Faso', '布隆迪': 'Burundi', '智利': 'Chile',
                '埃塞俄比亚': 'Ethiopia', '中国': 'China', '中国 - 香港': 'China - Hong Kong', '中国 - 澳门': 'China - Macao',
                '哥斯达黎加': 'Costa Rica', '丹麦': 'Denmark', '德国': 'Germany', '吉布提': 'Djibouti', '多米尼克': 'Dominica',
                '多米尼加共和国': 'Dominican Republic', '刚果民主共和国': 'DR Congo', '阿富汗': 'Afghanistan', '厄瓜多尔': 'Ecuador',
                '萨尔瓦多': 'El Salvador', '科特迪瓦': 'Ivory Coast', '厄立特里亚': 'Eritrea', '爱沙尼亚': 'Estonia', '斐济': 'Fiji',
                '芬兰': 'Finland', '法国': 'France', '加蓬': 'Gabon', '冈比亚': 'Gambia', '阿尔巴尼亚': 'Albania', '乔治亚': 'Georgia',
                '加纳': 'Ghana', '格林纳达': 'Grenada', '希腊': 'Greece', '英国': 'United Kingdom', '危地马拉': 'Guatemala',
                '几内亚': 'Guinea', '几内亚比绍': 'Guinea-Bissau', '圭亚那': 'Guyana', '海地': 'Haiti', '阿尔及利亚': 'Algeria',
                '洪都拉斯': 'Honduras', '印度': 'India', '印度尼西亚': 'Indonesia', '伊拉克': 'Iraq', '伊朗': 'Iran', '爱尔兰': 'Ireland',
                '冰岛': 'Iceland', '以色列': 'Israel', '意大利': 'Italy', '牙买加': 'Jamaica', '安哥拉': 'Angola', '日本': 'Japan',
                '也门': 'Yemen', '约旦': 'Jordan', '柬埔寨': 'Cambodia', '喀麦隆': 'Cameroon', '加拿大': 'Canada',
                '佛得角': 'Cape Verde', '哈萨克': 'Kazakhstan', '肯亚': 'Kenya', '吉尔吉斯': 'Kyrgyzstan',
                '安提瓜和巴布达': 'Antigua and Barbuda', '基里巴斯': 'Kiribati', '哥伦比亚': 'Colombia', '科摩罗': 'Comoros',
                '刚果': 'Congo', '克罗地亚': 'Croatia', '古巴': 'Cuba', '科威特': 'Kuwait', '老挝': 'Lao', '莱索托': 'Lesotho',
                '拉脱维亚': 'Latvia', '阿根廷': 'Argentina', '黎巴嫩': 'Lebanon', '利比里亚': 'Liberia', '利比亚': 'Libya',
                '立陶宛': 'Lithuania', '卢森堡': 'Luxembourg', '马达加斯加': 'Madagascar', '马拉维': 'Malawi', '马来西亚': 'Malaysia',
                '马尔代夫': 'Maldives', '马利': 'Mali'}
Continent_UI = {'非洲': 'Africa', '欧洲': 'Europe', '中美洲': 'Central America', '北美洲': 'North America',
                '南美洲': 'South America', '东亚': 'East Asia', '中西亚': 'Near East', '大洋洲': 'Oceania'}
Public_ConfigDB_Path = 'config.sqlite'


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
