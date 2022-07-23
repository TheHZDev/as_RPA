import urllib.request
from json import loads as json_loads
from urllib.parse import quote

from requests import Session

__all__ = ['ServerMap', 'LoginAirlineSim', 'getBaseURL', 'LogoutAirlineSim']

ServerMap = {'Yeager': 'https://yeager.airlinesim.aero/action/portal/index',
             'Junkers': 'https://junkers.airlinesim.aero/action/portal/index',
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

try:
    from local_debug import flag_Debug

    Debug_Allow_HTTPS_Verify = not flag_Debug
except:
    Debug_Allow_HTTPS_Verify = True


def LoginAirlineSim(ServerName: str, UserName: str, Passwd: str) -> Session:
    """
    登陆AS账户，服务器仅用于伪造正常登陆流程。

    :param ServerName: 服务器名称。
    :param UserName: 用户名
    :param Passwd: 密码
    :return: 登陆成功返回Session，失败抛出错误
    """
    if ServerName not in ServerMap.keys():
        raise Exception('找不到要登录的服务器。')
    login_fin_url = ServerMap.get(ServerName)
    login_session = Session()
    login_session.headers[
        'User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:93.0) Gecko/20100101 Firefox/93.0'
    LocalProxier = {'http': '', 'https': ''}
    LocalProxier.update(urllib.request.getproxies())
    login_session.get(login_fin_url, timeout=10000, verify=Debug_Allow_HTTPS_Verify,
                      proxies=LocalProxier)  # 第一步，直接连接目标URL
    login_session.cookies['_sl_lp'] = quote(login_fin_url)
    login_session.headers['Referer'] = login_fin_url
    login_session.get('https://accounts.airlinesim.aero/auth/login?od=' + login_fin_url,
                      verify=Debug_Allow_HTTPS_Verify, proxies=LocalProxier)
    # 构造提交数据，这里就不OPTIONS了
    post_json = {'login': UserName, 'password': Passwd, 'persistent': False, 'method': 'password', 'brand': 'as',
                 'metadata': {'landingPage': login_fin_url}}
    login_session.headers['Origin'] = 'https://accounts.airlinesim.aero'
    login_result = login_session.post('https://sar.simulogics.games/api/sessions', json=post_json, timeout=10000,
                                      verify=Debug_Allow_HTTPS_Verify, proxies=LocalProxier)
    if login_result.status_code == 201:
        t1: dict = json_loads(login_result.text)
        t_header = login_session.headers.copy()
        t_header['Authorization'] = 'Bearer ' + t1.get('token')
        login_session.get('https://sar.simulogics.games/api/sessions/' + t1.get('id'), headers=t_header,
                          timeout=10000, verify=Debug_Allow_HTTPS_Verify, proxies=LocalProxier)
        login_session.cookies['as-sid'] = t1.get('token')
        login_session.headers['Origin'] = login_fin_url
        login_session.get(login_fin_url)  # 登陆过程结束
        return login_session
    elif login_result.status_code == 400 and 'authentication_failure' in login_result.text:
        raise Exception('认证失败，用户名或密码错误。')
    elif login_result.status_code == 429:
        raise Exception('认证失败，同时存在的会话太多，可能存在封号现象。')
    else:
        raise Exception('用户名或密码错误，请重试。HTTP（%d）状态码异常。' % login_result.status_code)


def LogoutAirlineSim(LogonSession: Session):
    """注销AS会话"""
    target_url = 'https://sar.simulogics.games/api/sessions/' + \
                 LogonSession.cookies.get('as-sid').split('_')[0]
    LogonSession.headers['Authorization'] = 'Bearer ' + LogonSession.cookies.get('as-sid')
    LocalProxier = {'http': '', 'https': ''}
    LocalProxier.update(urllib.request.getproxies())
    LogonSession.delete(target_url, proxies=LocalProxier, verify=Debug_Allow_HTTPS_Verify)  # 自动注销会话
    LogonSession.close()


def getBaseURL(ServerName: str) -> str:
    if ServerName not in ServerMap.keys():
        return ''
    from urllib.parse import urlparse
    return 'https://' + urlparse(ServerMap.get(ServerName)).netloc
