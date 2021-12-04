from bs4 import BeautifulSoup
from requests import Response


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


def CommonHTMLParser(HTML: BeautifulSoup, function_Parser, DataVarTemplate=None):
    """通用HTML解析函数"""
    if not callable(function_Parser):
        raise Exception('function_Parser必须是可调用函数！')
    from bs4.element import Tag
    if DataVarTemplate is None:
        DataCache = {}
    elif hasattr(DataVarTemplate, 'copy') and callable(getattr(DataVarTemplate, 'copy')):
        DataCache = DataVarTemplate.copy()
    else:
        DataCache = DataVarTemplate

    def Recursion_ParseHTML(root: Tag):
        result = function_Parser(root, DataCache)
        if isinstance(result, bool) and result:
            return
        for t_unit in root.children:
            if isinstance(t_unit, Tag):
                Recursion_ParseHTML(t_unit)

    for unit in HTML.children:
        if isinstance(unit, Tag):
            Recursion_ParseHTML(unit)
    return DataCache
