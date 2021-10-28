from json import loads as json_loads
from urllib.parse import quote

from requests import Session

__all__ = ['ServerMap', 'LoginAirlineSim', 'getBaseURL']

ServerMap = {'Yeager': 'https://yeager.airlinesim.aero/action/portal/index',
             'Junker': 'https://junkers.airlinesim.aero/action/portal/index',
             'Quimby': 'https://quimby.airlinesim.aero/action/portal/index',
             'Bleriot': 'https://bleriot.airlinesim.aero/action/portal/index',
             'Limatambo': 'https://limatambo.airlinesim.aero/action/portal/index',
             'Domination': 'https://domination.airlinesim.aero/action/portal/index',
             'Xiguan': 'https://xiguan.airlinesim.aero/action/portal/index',
             'Hoover': 'https://hoover.airlinesim.aero/action/portal/index',
             'Riem': 'https://riem.airlinesim.aero/action/portal/index',
             'Ellinikon': 'https://ellinikon.airlinesim.aero/action/portal/index',
             'Aspern': 'https://aspern.airlinesim.aero/action/portal/index',
             'Gatow': 'https://gatow.airlinesim.aero/action/portal/index',
             'Pearls': 'https://pearls.airlinesim.aero/action/portal/index',
             'Meigs': 'https://meigs.airlinesim.aero/action/portal/index',
             'Stapleton': 'https://stapleton.airlinesim.aero/action/portal/index',
             'Fornebu': 'https://fornebu.airlinesim.aero/action/portal/index',
             'Tempelhof': 'https://tempelhof.airlinesim.aero/action/portal/index',
             'Croydon': 'https://croydon.airlinesim.aero/action/portal/index',
             'Nicosia': 'https://nicosia.airlinesim.aero/action/portal/index',
             'Devau': 'https://devau.airlinesim.aero/action/portal/index',
             'Idlewild': 'https://idlewild.airlinesim.aero/action/portal/index',
             'Kaitak': 'https://kaitak.airlinesim.aero/action/portal/index',
             'Otto': 'https://otto.airlinesim.aero/action/portal/index'}


def LoginAirlineSim(ServerName: str, UserName: str, Passwd: str) -> Session:
    if ServerName not in ServerMap.keys():
        raise Exception('找不到要登录的服务器。')
    login_fin_url = ServerMap.get(ServerName)
    login_session = Session()
    login_session.headers[
        'User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:93.0) Gecko/20100101 Firefox/93.0'
    login_session.get(login_fin_url, timeout=10000)  # 第一步，直接连接目标URL
    login_session.cookies['_sl_lp'] = quote(login_fin_url)
    login_session.headers['Referer'] = login_fin_url
    login_session.get('https://accounts.airlinesim.aero/auth/login?od=' + login_fin_url)
    # 构造提交数据，这里就不OPTIONS了
    post_json = {'login': UserName, 'password': Passwd, 'persistent': False, 'method': 'password', 'brand': 'as',
                 'metadata': {'landingPage': login_fin_url}}
    login_session.headers['Origin'] = 'https://accounts.airlinesim.aero'
    login_result = login_session.post('https://sar.simulogics.games/api/sessions', json=post_json, timeout=10000)
    if login_result.status_code == 201:
        t1: dict = json_loads(login_result.text)
        t_header = login_session.headers
        t_header['Authorization'] = 'Bearer ' + t1.get('token')
        login_session.get('https://sar.simulogics.games/api/sessions/' + t1.get('id'), headers=t_header,
                          timeout=10000)
        login_session.cookies['as-sid'] = t1.get('token')
        login_session.get(login_fin_url)  # 登陆过程结束
        return login_session
    else:
        raise Exception('用户名或密码错误，请重试。HTTP（%d）状态码异常。' % login_result.status_code)


def getBaseURL(ServerName: str) -> str:
    if ServerName not in ServerMap.keys():
        return ''
    from urllib.parse import urlparse
    return 'https://' + urlparse(ServerMap.get(ServerName)).netloc
