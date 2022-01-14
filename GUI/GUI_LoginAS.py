import base64
import sqlite3
from threading import Thread

import wx

from LoginAirlineSim import ServerMap, LoginAirlineSim


class LoginAirlineSimDialog(wx.Dialog):

    def __init__(self, parent, DB_Path: str, callback_TransferSession):
        """
        AS登陆对话框，提供基本的保存密码和转送登陆Session功能\n
        :param parent: 父窗口，一般填None
        :param DB_Path: 保存密码的数据库路径
        :param callback_TransferSession: 登陆成功后，保存Session的回调函数
        """
        if callable(callback_TransferSession):
            self.function_TransferSession = callback_TransferSession
        else:
            raise Exception('callback_TransferSession应定义为函数，且按顺序接收一个requests.Session类型的参数和一个str类型的参数。')
        self.DB_Path = DB_Path
        # 基本参数判断

        wx.Dialog.__init__(self, parent, id=wx.ID_ANY, title=u"登录到AirlineSim", pos=wx.DefaultPosition,
                           size=wx.Size(265, 240), style=wx.DEFAULT_DIALOG_STYLE)

        self.SetSizeHints(wx.DefaultSize, wx.DefaultSize)

        bSizer8 = wx.BoxSizer(wx.VERTICAL)

        gSizer6 = wx.GridSizer(0, 2, 0, 0)

        self.m_staticText39 = wx.StaticText(self, wx.ID_ANY, u"服务器", wx.DefaultPosition, wx.DefaultSize, 0)
        self.m_staticText39.Wrap(-1)

        gSizer6.Add(self.m_staticText39, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL, 5)

        InputServerNameChoices = [Server for Server in ServerMap.keys()]
        self.InputServerName = wx.Choice(self, wx.ID_ANY, wx.DefaultPosition, wx.Size(150, -1), InputServerNameChoices,
                                         wx.CB_SORT)
        self.InputServerName.SetSelection(0)
        gSizer6.Add(self.InputServerName, 0, wx.ALL | wx.ALIGN_RIGHT, 5)

        self.m_staticText40 = wx.StaticText(self, wx.ID_ANY, u"用户名", wx.DefaultPosition, wx.DefaultSize, 0)
        self.m_staticText40.Wrap(-1)

        gSizer6.Add(self.m_staticText40, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL, 5)

        self.InputUserName = wx.TextCtrl(self, wx.ID_ANY, wx.EmptyString, wx.Point(-1, -1), wx.Size(150, -1), 0)
        gSizer6.Add(self.InputUserName, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT, 5)

        self.m_staticText41 = wx.StaticText(self, wx.ID_ANY, u"密码", wx.DefaultPosition, wx.DefaultSize, 0)
        self.m_staticText41.Wrap(-1)

        gSizer6.Add(self.m_staticText41, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL | wx.ALIGN_CENTER_VERTICAL, 5)

        self.InputPassword = wx.TextCtrl(self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size(150, -1),
                                         wx.TE_PASSWORD)
        gSizer6.Add(self.InputPassword, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT, 5)

        self.IsSavePwd = wx.CheckBox(self, wx.ID_ANY, u"记住密码", wx.DefaultPosition, wx.DefaultSize, 0)
        gSizer6.Add(self.IsSavePwd, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 5)

        bSizer8.Add(gSizer6, 1, wx.EXPAND, 5)

        gSizer7 = wx.GridSizer(1, 3, 0, 0)

        self.LoginButton = wx.Button(self, wx.ID_ANY, u"登录", wx.DefaultPosition, wx.DefaultSize, 0)

        gSizer7.Add(self.LoginButton, 0, wx.ALL | wx.ALIGN_BOTTOM, 5)

        self.ClearTextButton = wx.Button(self, wx.ID_ANY, u"清空", wx.DefaultPosition, wx.DefaultSize, 0)
        gSizer7.Add(self.ClearTextButton, 0, wx.ALL | wx.ALIGN_BOTTOM, 5)

        self.ExitButton = wx.Button(self, wx.ID_ANY, u"退出", wx.DefaultPosition, wx.DefaultSize, 0)
        gSizer7.Add(self.ExitButton, 0, wx.ALL | wx.ALIGN_BOTTOM, 5)

        bSizer8.Add(gSizer7, 1, wx.EXPAND, 5)

        self.LoginProgressTextEntry = wx.TextCtrl(self, wx.ID_ANY, u"请登录。。。", wx.DefaultPosition, wx.Size(250, -1),
                                                  wx.TE_CENTER | wx.TE_READONLY)
        bSizer8.Add(self.LoginProgressTextEntry, 0, wx.ALL, 5)

        self.SetSizer(bSizer8)
        self.Layout()

        self.Centre(wx.BOTH)

        # Connect Events
        self.LoginButton.Bind(wx.EVT_BUTTON, self.LoginButtonOnButtonClick)
        self.ClearTextButton.Bind(wx.EVT_BUTTON, self.ClearTextButtonOnButtonClick)
        self.ExitButton.Bind(wx.EVT_BUTTON, self.ExitButtonOnButtonClick)

        self.LoadPwdFromDB()

    def __del__(self):
        pass

    # Virtual event handlers, override them in your derived class
    def LoginButtonOnButtonClick(self, event):
        if len(self.InputUserName.GetValue()) * len(self.InputPassword.GetValue()) == 0:
            wx.MessageDialog(self, '用户名或密码不能为空！', '登陆前检查').ShowModal()
            return
        elif self.InputServerName.GetSelection() == -1:
            wx.MessageDialog(self, '请选择要登陆的服务器！', '登陆前检查').ShowModal()
            return
        # 锁定界面防止重复操作
        self.LoginButton.Disable()
        self.ClearTextButton.Disable()
        self.InputServerName.Disable()
        self.InputUserName.Disable()
        self.InputPassword.Disable()
        Thread(target=self.thread_LoginAS).start()

    def ClearTextButtonOnButtonClick(self, event):
        self.InputUserName.Clear()
        self.InputPassword.Clear()

    def ExitButtonOnButtonClick(self, event):
        self.Close(True)
        import sys
        sys.exit(0)

    # 内部规程函数
    def thread_LoginAS(self):
        ServerName = self.InputServerName.GetStringSelection()
        self.LoginProgressTextEntry.SetValue('正在登陆，请稍等。。。')
        try:
            LoginSession = LoginAirlineSim(ServerName, self.InputUserName.GetValue(), self.InputPassword.GetValue())
            self.LoginProgressTextEntry.SetValue('登陆成功，请稍等。。。')
            # 保存密码
            if self.IsSavePwd.GetValue():
                self.SavePwdToDB()
            wx.CallAfter(self.function_TransferSession, LoginSession, ServerName)
            self.Close(True)
        except Exception as LoginException:
            wx.MessageDialog(self, str(LoginException), '登陆失败').ShowModal()
            self.LoginButton.Enable()
            self.ClearTextButton.Enable()
            self.InputServerName.Enable()
            self.InputUserName.Enable()
            self.InputPassword.Enable()
            self.InputPassword.Clear()

    def SavePwdToDB(self):
        create_sql = """
        CREATE TABLE IF NOT EXISTS LoginAirlineSim(
            ServerName TEXT,
            UserName TEXT,
            Passwd TEXT
        );
        """
        cache_UserName = base64.b64encode(base64.b85encode(self.InputUserName.GetValue().encode())).decode()
        cache_Passwd = base64.b64encode(base64.b32encode(self.InputPassword.GetValue().encode())).decode()
        cache_ServerName = self.InputServerName.GetItems()[self.InputServerName.GetSelection()]
        # 打开数据库
        insert_sql = "INSERT INTO LoginAirlineSim VALUES(?,?,?);"
        t_sql = sqlite3.connect(self.DB_Path)
        t_sql.execute(create_sql)
        t_sql.execute("DELETE FROM LoginAirlineSim;")
        t_sql.execute(insert_sql, (cache_ServerName, cache_UserName, cache_Passwd))
        t_sql.commit()
        t_sql.close()

    def LoadPwdFromDB(self):
        create_sql = """
        CREATE TABLE IF NOT EXISTS LoginAirlineSim(
            ServerName TEXT,
            UserName TEXT,
            Passwd TEXT
        );
        """
        select_sql = "SELECT ServerName,UserName,Passwd FROM LoginAirlineSim;"
        t_sql = sqlite3.connect(self.DB_Path)
        t_sql.execute(create_sql)
        t1 = t_sql.execute(select_sql).fetchall()
        t_sql.close()
        try:
            if len(t1) == 1:
                ServerName, UserName, Passwd = t1[0]
                UserName = base64.b85decode(base64.b64decode(UserName.encode())).decode()
                Passwd = base64.b32decode(base64.b64decode(Passwd.encode())).decode()
                self.InputServerName.SetSelection(self.InputServerName.GetItems().index(ServerName))
                self.InputUserName.SetValue(UserName)
                self.InputPassword.SetValue(Passwd)
                self.IsSavePwd.SetValue(True)
        finally:
            # 数据库字段读写失败不影响程序运行
            pass

    # 外部接口调用
    def ShowLoginProgress(self, HintText: str):
        self.LoginProgressTextEntry.SetValue(HintText)
