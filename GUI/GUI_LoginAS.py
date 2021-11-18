import wx

from LoginAirlineSim import ServerMap


class LoginAirlineSimDialog(wx.Dialog):

    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, id=wx.ID_ANY, title=u"登录到AirlineSim", pos=wx.DefaultPosition,
                           size=wx.Size(265, 229), style=wx.DEFAULT_DIALOG_STYLE)

        self.SetSizeHints(wx.DefaultSize, wx.DefaultSize)

        bSizer8 = wx.BoxSizer(wx.VERTICAL)

        gSizer6 = wx.GridSizer(0, 2, 0, 0)

        self.m_staticText39 = wx.StaticText(self, wx.ID_ANY, u"服务器", wx.DefaultPosition, wx.DefaultSize, 0)
        self.m_staticText39.Wrap(-1)

        gSizer6.Add(self.m_staticText39, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL, 5)

        InputServerNameChoices = [Server for Server in ServerMap.keys()]
        self.InputServerName = wx.Choice(self, wx.ID_ANY, wx.DefaultPosition, wx.Size(150, -1), InputServerNameChoices,
                                         0)
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
        self.LoginButton.Enable(False)

        gSizer7.Add(self.LoginButton, 0, wx.ALL | wx.ALIGN_BOTTOM, 5)

        self.ClearTextButton = wx.Button(self, wx.ID_ANY, u"清空", wx.DefaultPosition, wx.DefaultSize, 0)
        gSizer7.Add(self.ClearTextButton, 0, wx.ALL | wx.ALIGN_BOTTOM, 5)

        self.ExitButton = wx.Button(self, wx.ID_ANY, u"退出", wx.DefaultPosition, wx.DefaultSize, 0)
        gSizer7.Add(self.ExitButton, 0, wx.ALL | wx.ALIGN_BOTTOM, 5)

        bSizer8.Add(gSizer7, 1, wx.EXPAND | wx.ALIGN_CENTER_HORIZONTAL, 5)

        self.LoginProgressTextEntry = wx.TextCtrl(self, wx.ID_ANY, u"请登录。。。", wx.DefaultPosition, wx.Size(250, -1),
                                                  wx.TE_CENTER | wx.TE_READONLY)
        bSizer8.Add(self.LoginProgressTextEntry, 0, wx.ALL, 5)

        self.SetSizer(bSizer8)
        self.Layout()

        self.Centre(wx.BOTH)

        # Connect Events
        self.InputUserName.Bind(wx.EVT_TEXT, self.InputUserNameOnText)
        self.InputPassword.Bind(wx.EVT_TEXT, self.InputPasswordOnText)
        self.LoginButton.Bind(wx.EVT_BUTTON, self.LoginButtonOnButtonClick)
        self.ClearTextButton.Bind(wx.EVT_BUTTON, self.ClearTextButtonOnButtonClick)
        self.ExitButton.Bind(wx.EVT_BUTTON, self.ExitButtonOnButtonClick)

    def __del__(self):
        pass

    # Virtual event handlers, override them in your derived class
    def InputUserNameOnText(self, event):
        pass

    def InputPasswordOnText(self, event):
        pass

    def LoginButtonOnButtonClick(self, event):
        pass

    def ClearTextButtonOnButtonClick(self, event):
        pass

    def ExitButtonOnButtonClick(self, event):
        pass
