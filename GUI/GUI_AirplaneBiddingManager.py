import wx


class AirplaneBiddingManager(wx.Frame):

    def __init__(self, parent):
        wx.Frame.__init__(self, parent, id=wx.ID_ANY, title=u"航机竞价管理器", pos=wx.DefaultPosition, size=wx.Size(571, 465),
                          style=wx.CAPTION | wx.CLOSE_BOX | wx.MINIMIZE | wx.MINIMIZE_BOX | wx.TAB_TRAVERSAL)

        self.SetSizeHints(wx.DefaultSize, wx.DefaultSize)

        gSizer1 = wx.GridSizer(0, 3, 0, 0)

        sbSizer1 = wx.StaticBoxSizer(wx.StaticBox(self, wx.ID_ANY, u"航机监控管理"), wx.VERTICAL)

        AirplaneMonitorListChoices = []
        self.AirplaneMonitorList = wx.ListBox(sbSizer1.GetStaticBox(), wx.ID_ANY, wx.DefaultPosition, wx.Size(170, 340),
                                              AirplaneMonitorListChoices,
                                              wx.LB_HSCROLL | wx.LB_NEEDED_SB | wx.LB_SINGLE | wx.LB_SORT)
        sbSizer1.Add(self.AirplaneMonitorList, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 5)

        self.AddNewMonitorAirplaneButton = wx.Button(sbSizer1.GetStaticBox(), wx.ID_ANY, u"添加新航机", wx.DefaultPosition,
                                                     wx.Size(100, -1), 0)
        sbSizer1.Add(self.AddNewMonitorAirplaneButton, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 5)

        gSizer1.Add(sbSizer1, 1, wx.EXPAND, 5)

        sbSizer2 = wx.StaticBoxSizer(wx.StaticBox(self, wx.ID_ANY, u"竞价管理详情"), wx.VERTICAL)

        gSizer2 = wx.GridSizer(0, 2, 0, 0)

        self.m_staticText22 = wx.StaticText(sbSizer2.GetStaticBox(), wx.ID_ANY, u"预算策略", wx.DefaultPosition,
                                            wx.DefaultSize, 0)
        self.m_staticText22.Wrap(-1)

        self.m_staticText22.SetFont(
            wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, wx.EmptyString))

        gSizer2.Add(self.m_staticText22, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL | wx.ALIGN_CENTER_VERTICAL, 5)

        self.ChangeBudgetStrategyButton = wx.Button(sbSizer2.GetStaticBox(), wx.ID_ANY, u"玩家现金", wx.DefaultPosition,
                                                    wx.Size(90, -1), 0)
        self.ChangeBudgetStrategyButton.SetToolTip(u"可选“玩家现金”，“单一价格”，“机型分类价”和“独立定价”。")

        gSizer2.Add(self.ChangeBudgetStrategyButton, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT, 5)

        self.m_staticText23 = wx.StaticText(sbSizer2.GetStaticBox(), wx.ID_ANY, u"竞价方式", wx.DefaultPosition,
                                            wx.DefaultSize, 0)
        self.m_staticText23.Wrap(-1)

        gSizer2.Add(self.m_staticText23, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL, 5)

        self.ChangeBiddingStrategyButton = wx.Button(sbSizer2.GetStaticBox(), wx.ID_ANY, u"租赁竞价", wx.DefaultPosition,
                                                     wx.Size(90, -1), 0)
        self.ChangeBiddingStrategyButton.SetToolTip(u"可选“租赁竞价”或“立即租赁”，租赁竞价开始后不可更改。")

        gSizer2.Add(self.ChangeBiddingStrategyButton, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT, 5)

        self.m_staticText24 = wx.StaticText(sbSizer2.GetStaticBox(), wx.ID_ANY, u"拍卖主体", wx.DefaultPosition,
                                            wx.DefaultSize, 0)
        self.m_staticText24.Wrap(-1)

        gSizer2.Add(self.m_staticText24, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)

        self.ShowOwnerOfAirplane = wx.TextCtrl(sbSizer2.GetStaticBox(), wx.ID_ANY, u"没有数据", wx.DefaultPosition,
                                               wx.DefaultSize, wx.TE_READONLY)
        gSizer2.Add(self.ShowOwnerOfAirplane, 0, wx.ALL | wx.ALIGN_RIGHT, 5)

        self.m_staticText25 = wx.StaticText(sbSizer2.GetStaticBox(), wx.ID_ANY, u"航机编号", wx.DefaultPosition,
                                            wx.DefaultSize, 0)
        self.m_staticText25.Wrap(-1)

        gSizer2.Add(self.m_staticText25, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)

        self.ShowCodeOfAirplane = wx.TextCtrl(sbSizer2.GetStaticBox(), wx.ID_ANY, u"没有数据", wx.DefaultPosition,
                                              wx.DefaultSize, wx.TE_CENTER | wx.TE_READONLY)
        gSizer2.Add(self.ShowCodeOfAirplane, 0, wx.ALL | wx.ALIGN_RIGHT, 5)

        self.m_staticText26 = wx.StaticText(sbSizer2.GetStaticBox(), wx.ID_ANY, u"航机年龄", wx.DefaultPosition,
                                            wx.DefaultSize, 0)
        self.m_staticText26.Wrap(-1)

        gSizer2.Add(self.m_staticText26, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)

        self.ShowAgeOfAirplane = wx.TextCtrl(sbSizer2.GetStaticBox(), wx.ID_ANY, u"没有数据", wx.DefaultPosition,
                                             wx.DefaultSize, wx.TE_CENTER | wx.TE_READONLY)
        gSizer2.Add(self.ShowAgeOfAirplane, 0, wx.ALL | wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 5)

        self.m_staticText27 = wx.StaticText(sbSizer2.GetStaticBox(), wx.ID_ANY, u"当前位置", wx.DefaultPosition,
                                            wx.DefaultSize, 0)
        self.m_staticText27.Wrap(-1)

        gSizer2.Add(self.m_staticText27, 0, wx.ALL, 5)

        self.ShowLocationOfAirplane = wx.TextCtrl(sbSizer2.GetStaticBox(), wx.ID_ANY, u"没有数据", wx.DefaultPosition,
                                                  wx.DefaultSize, wx.TE_CENTER | wx.TE_READONLY)
        gSizer2.Add(self.ShowLocationOfAirplane, 0, wx.ALL | wx.ALIGN_RIGHT, 5)

        self.m_staticText28 = wx.StaticText(sbSizer2.GetStaticBox(), wx.ID_ANY, u"当前出价", wx.DefaultPosition,
                                            wx.DefaultSize, 0)
        self.m_staticText28.Wrap(-1)

        gSizer2.Add(self.m_staticText28, 0, wx.ALL, 5)

        self.ShowCurrentPrice = wx.TextCtrl(sbSizer2.GetStaticBox(), wx.ID_ANY, u"0", wx.DefaultPosition,
                                            wx.DefaultSize, wx.TE_CENTER | wx.TE_READONLY)
        gSizer2.Add(self.ShowCurrentPrice, 0, wx.ALL | wx.ALIGN_RIGHT, 5)

        sbSizer2.Add(gSizer2, 1, 0, 5)

        bSizer4 = wx.BoxSizer(wx.VERTICAL)

        self.m_staticText30 = wx.StaticText(sbSizer2.GetStaticBox(), wx.ID_ANY, u"下一出价为", wx.DefaultPosition,
                                            wx.DefaultSize, 0)
        self.m_staticText30.Wrap(-1)

        bSizer4.Add(self.m_staticText30, 0, wx.ALL, 5)

        self.ShowNextPrice = wx.TextCtrl(sbSizer2.GetStaticBox(), wx.ID_ANY, u"0", wx.DefaultPosition, wx.Size(130, -1),
                                         wx.TE_CENTER | wx.TE_READONLY)
        bSizer4.Add(self.ShowNextPrice, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 5)

        gSizer3 = wx.GridSizer(0, 2, 0, 0)

        self.ContinueIncreaseBidButton = wx.Button(sbSizer2.GetStaticBox(), wx.ID_ANY, u"继续加价", wx.DefaultPosition,
                                                   wx.DefaultSize, 0)
        self.ContinueIncreaseBidButton.Enable(False)
        self.ContinueIncreaseBidButton.SetToolTip(u"加价将无视预算策略限制。")

        gSizer3.Add(self.ContinueIncreaseBidButton, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL | wx.ALIGN_CENTER_VERTICAL,
                    5)

        self.GiveUpPlaceBidButton = wx.Button(sbSizer2.GetStaticBox(), wx.ID_ANY, u"放弃竞价", wx.DefaultPosition,
                                              wx.DefaultSize, 0)
        self.GiveUpPlaceBidButton.Enable(False)
        self.GiveUpPlaceBidButton.SetToolTip(u"放弃此次竞价，注意若取得最高价无法退出。")

        gSizer3.Add(self.GiveUpPlaceBidButton, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL, 5)

        bSizer4.Add(gSizer3, 1, wx.EXPAND | wx.ALIGN_CENTER_HORIZONTAL, 5)

        self.IsAutoIncreasePriceWithoutBudgetStrategy = wx.CheckBox(sbSizer2.GetStaticBox(), wx.ID_ANY,
                                                                    u"无视预算策略直到竞价结束", wx.DefaultPosition,
                                                                    wx.DefaultSize, 0)
        self.IsAutoIncreasePriceWithoutBudgetStrategy.SetToolTip(u"有钱，任性！")

        bSizer4.Add(self.IsAutoIncreasePriceWithoutBudgetStrategy, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 5)

        sbSizer2.Add(bSizer4, 1, wx.ALIGN_CENTER_HORIZONTAL | wx.EXPAND, 5)

        gSizer1.Add(sbSizer2, 1, wx.EXPAND, 5)

        sbSizer4 = wx.StaticBoxSizer(wx.StaticBox(self, wx.ID_ANY, u"其它操作菜单"), wx.VERTICAL)

        ConfigDefaultBudgetStrategyChoices = [u"玩家现金", u"单一预算", u"机型分类价", u"独立预算"]
        self.ConfigDefaultBudgetStrategy = wx.RadioBox(sbSizer4.GetStaticBox(), wx.ID_ANY, u"默认预算策略",
                                                       wx.DefaultPosition, wx.DefaultSize,
                                                       ConfigDefaultBudgetStrategyChoices, 2, wx.RA_SPECIFY_COLS)
        self.ConfigDefaultBudgetStrategy.SetSelection(0)
        self.ConfigDefaultBudgetStrategy.SetToolTip(
            u"“玩家现金”：预算策略将参考玩家的现金，请注意若竞价时现金改变，预算也会调整。\n“单一预算”：为所有航机设定统一的预算上限。\n“机型分类价”：航机根据其所属的机型系列设定预算。\n"
            u"“独立预算”：每架航机都使用其单独的预算。\n提示：若选了策略但未设定具体预算值，其预算值将由上一级预算策略管理。")

        sbSizer4.Add(self.ConfigDefaultBudgetStrategy, 0, wx.ALL, 5)

        ConfigDefaultRentMethodChoices = [u"租赁竞价   ", u"立即租赁"]
        self.ConfigDefaultRentMethod = wx.RadioBox(sbSizer4.GetStaticBox(), wx.ID_ANY, u"默认竞价策略", wx.DefaultPosition,
                                                   wx.DefaultSize, ConfigDefaultRentMethodChoices, 2,
                                                   wx.RA_SPECIFY_COLS)
        self.ConfigDefaultRentMethod.SetSelection(0)
        self.ConfigDefaultRentMethod.SetToolTip(
            u"“租赁竞价”：程序将以投标的方式进行航机租赁操作。\n“立即租赁”：如果允许，程序将立即租赁航机。\n提示：本程序不管理二手航机的购买操作。")

        sbSizer4.Add(self.ConfigDefaultRentMethod, 0, wx.ALL, 5)

        self.ConfigMultiBudgetStrategyButton = wx.Button(sbSizer4.GetStaticBox(), wx.ID_ANY, u"分级预算策略设置",
                                                         wx.DefaultPosition, wx.Size(120, -1), 0)
        self.ConfigMultiBudgetStrategyButton.SetToolTip(u"单击进入分级预算策略选单。")

        sbSizer4.Add(self.ConfigMultiBudgetStrategyButton, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 5)

        self.ConfigCurrentAirplaneAuctionButton = wx.Button(sbSizer4.GetStaticBox(), wx.ID_ANY, u"管理当前航机",
                                                            wx.DefaultPosition, wx.Size(120, -1), 0)
        self.ConfigCurrentAirplaneAuctionButton.Enable(False)

        sbSizer4.Add(self.ConfigCurrentAirplaneAuctionButton, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 5)

        self.SaveALLConfigButton = wx.Button(sbSizer4.GetStaticBox(), wx.ID_ANY, u"保存设置", wx.DefaultPosition,
                                             wx.Size(120, -1), 0)
        sbSizer4.Add(self.SaveALLConfigButton, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 5)

        gSizer1.Add(sbSizer4, 1, wx.EXPAND, 5)

        self.SetSizer(gSizer1)
        self.Layout()
        self.m_statusBar1 = self.CreateStatusBar(1, wx.STB_SIZEGRIP, wx.ID_ANY)

        self.Centre(wx.BOTH)

        # Connect Events
        self.AirplaneMonitorList.Bind(wx.EVT_LISTBOX, self.AirplaneMonitorListOnListBox)
        self.AddNewMonitorAirplaneButton.Bind(wx.EVT_BUTTON, self.AddNewMonitorAirplaneButtonOnButtonClick)
        self.ChangeBiddingStrategyButton.Bind(wx.EVT_BUTTON, self.ChangeBiddingStrategyButtonOnButtonClick)
        self.ContinueIncreaseBidButton.Bind(wx.EVT_BUTTON, self.ContinueIncreaseBidButtonOnButtonClick)
        self.GiveUpPlaceBidButton.Bind(wx.EVT_BUTTON, self.GiveUpPlaceBidButtonOnButtonClick)
        self.IsAutoIncreasePriceWithoutBudgetStrategy.Bind(wx.EVT_CHECKBOX,
                                                           self.IsAutoIncreasePriceWithoutBudgetStrategyOnCheckBox)
        self.ConfigMultiBudgetStrategyButton.Bind(wx.EVT_BUTTON, self.ConfigMultiBudgetStrategyButtonOnButtonClick)
        self.ConfigCurrentAirplaneAuctionButton.Bind(wx.EVT_BUTTON,
                                                     self.ConfigCurrentAirplaneAuctionButtonOnButtonClick)

    def __del__(self):
        pass

    # Virtual event handlers, override them in your derived class
    def AirplaneMonitorListOnListBox(self, event):
        pass

    def AddNewMonitorAirplaneButtonOnButtonClick(self, event):
        pass

    def ChangeBiddingStrategyButtonOnButtonClick(self, event):
        pass

    def ContinueIncreaseBidButtonOnButtonClick(self, event):
        pass

    def GiveUpPlaceBidButtonOnButtonClick(self, event):
        pass

    def IsAutoIncreasePriceWithoutBudgetStrategyOnCheckBox(self, event):
        pass

    def ConfigMultiBudgetStrategyButtonOnButtonClick(self, event):
        pass

    def ConfigCurrentAirplaneAuctionButtonOnButtonClick(self, event):
        pass


class AirplanePurchaseStrategyManager(wx.Frame):

    def __init__(self, parent):
        wx.Frame.__init__(self, parent, id=wx.ID_ANY, title=u"航机租赁策略管理", pos=wx.DefaultPosition, size=wx.Size(598, 445),
                          style=wx.CAPTION | wx.CLOSE_BOX | wx.FRAME_FLOAT_ON_PARENT | wx.MINIMIZE | wx.MINIMIZE_BOX | wx.TAB_TRAVERSAL)

        self.SetSizeHints(wx.DefaultSize, wx.DefaultSize)

        bSizer9 = wx.BoxSizer(wx.VERTICAL)

        gSizer8 = wx.GridSizer(0, 2, 0, 0)

        sbSizer5 = wx.StaticBoxSizer(wx.StaticBox(self, wx.ID_ANY, u"航机选择"), wx.VERTICAL)

        gSizer9 = wx.GridSizer(0, 2, 0, 0)

        self.m_staticText58 = wx.StaticText(sbSizer5.GetStaticBox(), wx.ID_ANY, u"航机家族", wx.DefaultPosition,
                                            wx.DefaultSize, 0)
        self.m_staticText58.Wrap(-1)

        gSizer9.Add(self.m_staticText58, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL | wx.ALIGN_CENTER_VERTICAL, 5)

        SelectAirplaneFamilyChoices = []
        self.SelectAirplaneFamily = wx.Choice(sbSizer5.GetStaticBox(), wx.ID_ANY, wx.DefaultPosition, wx.Size(150, -1),
                                              SelectAirplaneFamilyChoices, 0)
        self.SelectAirplaneFamily.SetSelection(0)
        gSizer9.Add(self.SelectAirplaneFamily, 0, wx.ALL | wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 5)

        self.m_staticText42 = wx.StaticText(sbSizer5.GetStaticBox(), wx.ID_ANY, u"航机品类", wx.DefaultPosition,
                                            wx.DefaultSize, 0)
        self.m_staticText42.Wrap(-1)

        gSizer9.Add(self.m_staticText42, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL | wx.ALIGN_CENTER_VERTICAL, 5)

        SelectAirplaneInFamilyChoices = []
        self.SelectAirplaneInFamily = wx.Choice(sbSizer5.GetStaticBox(), wx.ID_ANY, wx.DefaultPosition,
                                                wx.Size(150, -1), SelectAirplaneInFamilyChoices, wx.CB_SORT)
        self.SelectAirplaneInFamily.SetSelection(0)
        gSizer9.Add(self.SelectAirplaneInFamily, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT, 5)

        self.m_staticText43 = wx.StaticText(sbSizer5.GetStaticBox(), wx.ID_ANY, u"待租赁数量", wx.DefaultPosition,
                                            wx.DefaultSize, 0)
        self.m_staticText43.Wrap(-1)

        gSizer9.Add(self.m_staticText43, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL | wx.ALIGN_CENTER_VERTICAL, 5)

        self.InputRentNumber = wx.TextCtrl(sbSizer5.GetStaticBox(), wx.ID_ANY, wx.EmptyString, wx.DefaultPosition,
                                           wx.Size(150, -1), 0)
        gSizer9.Add(self.InputRentNumber, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT, 5)

        sbSizer5.Add(gSizer9, 1, 0, 5)

        ConfigBudgetStrategyChoices = [u"玩家现金", u"单一预算", u"机型分类价", u"独立预算"]
        self.ConfigBudgetStrategy = wx.RadioBox(sbSizer5.GetStaticBox(), wx.ID_ANY, u"当前预算策略", wx.DefaultPosition,
                                                wx.Size(-1, -1), ConfigBudgetStrategyChoices, 2, wx.RA_SPECIFY_COLS)
        self.ConfigBudgetStrategy.SetSelection(0)
        sbSizer5.Add(self.ConfigBudgetStrategy, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALL, 5)

        ConfigAirplaneAuctionChoices = [u"租赁竞价   ", u"立即租赁"]
        self.ConfigAirplaneAuction = wx.RadioBox(sbSizer5.GetStaticBox(), wx.ID_ANY, u"当前竞价策略", wx.DefaultPosition,
                                                 wx.DefaultSize, ConfigAirplaneAuctionChoices, 2, wx.RA_SPECIFY_COLS)
        self.ConfigAirplaneAuction.SetSelection(0)
        sbSizer5.Add(self.ConfigAirplaneAuction, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALL, 5)

        gSizer8.Add(sbSizer5, 1, wx.EXPAND, 5)

        sbSizer6 = wx.StaticBoxSizer(wx.StaticBox(self, wx.ID_ANY, u"航机选择-条件设计器"), wx.VERTICAL)

        gSizer12 = wx.GridSizer(0, 3, 0, 0)

        self.m_staticText52 = wx.StaticText(sbSizer6.GetStaticBox(), wx.ID_ANY, u"优先级(？)", wx.DefaultPosition,
                                            wx.DefaultSize, 0)
        self.m_staticText52.Wrap(-1)

        self.m_staticText52.SetToolTip(u"当航机型号被比中后，程序将根据这里的设置进一步决策要投标或立即购买的航机。优先级决定决策顺序。\n若优先级被设置为“没有”，则对应的选择器不参与决策过程。")

        gSizer12.Add(self.m_staticText52, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL | wx.ALIGN_CENTER_VERTICAL, 5)

        self.m_staticText53 = wx.StaticText(sbSizer6.GetStaticBox(), wx.ID_ANY, u"条件(？)", wx.DefaultPosition,
                                            wx.DefaultSize, 0)
        self.m_staticText53.Wrap(-1)

        self.m_staticText53.SetToolTip(
            u"设计航机选择器的条件，从上到下分别为：\n起拍价 - 航机在二手市场上的初始租赁价格，或立即购买价格。\n机龄 - 航机已服役的年龄，为大于 0 的实数。\n健康度 - "
            u"航机在租赁时的健康度，百分比。\n租赁来源 - 指示航机来自于AS官方租赁，或者其它玩家。")

        gSizer12.Add(self.m_staticText53, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL | wx.ALIGN_CENTER_VERTICAL, 5)

        self.m_staticText54 = wx.StaticText(sbSizer6.GetStaticBox(), wx.ID_ANY, u"优选(Y)/否决(N)\n      (？)",
                                            wx.DefaultPosition, wx.DefaultSize, 0)
        self.m_staticText54.Wrap(-1)

        self.m_staticText54.SetToolTip(u"下方选择框，选中即为游戏，不选中则为否决。\n“优选”：若有多个选项，选择最合适的那一项。\n“否决”：若条件不满足，不再选择该航机。")

        gSizer12.Add(self.m_staticText54, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT, 5)

        PriorityPriceChoices = [u"1", u"2", u"3", u"4", u"5", u"没有"]
        self.PriorityPrice = wx.Choice(sbSizer6.GetStaticBox(), wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize,
                                       PriorityPriceChoices, 0)
        self.PriorityPrice.SetSelection(5)
        gSizer12.Add(self.PriorityPrice, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL | wx.ALIGN_CENTER_VERTICAL, 5)

        bSizer12 = wx.BoxSizer(wx.VERTICAL)

        self.EditStartPriceButton = wx.Button(sbSizer6.GetStaticBox(), wx.ID_ANY, u"编辑起拍价范围", wx.DefaultPosition,
                                              wx.DefaultSize, 0)
        self.EditStartPriceButton.SetToolTip(u"编辑航机的起拍价范围，指定最小值和最大值。")

        bSizer12.Add(self.EditStartPriceButton, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 5)

        self.ShowPriceTextEntry = wx.TextCtrl(sbSizer6.GetStaticBox(), wx.ID_ANY, u"0 ~+∞ AS$", wx.DefaultPosition,
                                              wx.Size(125, -1), wx.TE_CENTER | wx.TE_READONLY)
        bSizer12.Add(self.ShowPriceTextEntry, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 5)

        gSizer12.Add(bSizer12, 1, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL, 5)

        self.IsPricePrefer = wx.CheckBox(sbSizer6.GetStaticBox(), wx.ID_ANY, wx.EmptyString, wx.DefaultPosition,
                                         wx.DefaultSize, 0)
        gSizer12.Add(self.IsPricePrefer, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL, 5)

        PriorityAirplaneAgeChoices = [u"1", u"2", u"3", u"4", u"5", u"没有"]
        self.PriorityAirplaneAge = wx.Choice(sbSizer6.GetStaticBox(), wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize,
                                             PriorityAirplaneAgeChoices, 0)
        self.PriorityAirplaneAge.SetSelection(5)
        gSizer12.Add(self.PriorityAirplaneAge, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL, 5)

        bSizer13 = wx.BoxSizer(wx.VERTICAL)

        self.EditAirplaneAgeButton = wx.Button(sbSizer6.GetStaticBox(), wx.ID_ANY, u"编辑机龄范围", wx.DefaultPosition,
                                               wx.DefaultSize, 0)
        bSizer13.Add(self.EditAirplaneAgeButton, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 5)

        self.ShowAirplaneAgeTextEntry = wx.TextCtrl(sbSizer6.GetStaticBox(), wx.ID_ANY, u"0 ~ ∞ 年", wx.DefaultPosition,
                                                    wx.DefaultSize, wx.TE_CENTER | wx.TE_READONLY)
        bSizer13.Add(self.ShowAirplaneAgeTextEntry, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 5)

        gSizer12.Add(bSizer13, 1, wx.ALIGN_CENTER_HORIZONTAL | wx.ALIGN_CENTER_VERTICAL, 5)

        self.IsAirplaneAgePrefer = wx.CheckBox(sbSizer6.GetStaticBox(), wx.ID_ANY, wx.EmptyString, wx.DefaultPosition,
                                               wx.DefaultSize, 0)
        gSizer12.Add(self.IsAirplaneAgePrefer, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL, 5)

        PriorityHealthChoices = [u"1", u"2", u"3", u"4", u"5", u"没有"]
        self.PriorityHealth = wx.Choice(sbSizer6.GetStaticBox(), wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize,
                                        PriorityHealthChoices, 0)
        self.PriorityHealth.SetSelection(5)
        gSizer12.Add(self.PriorityHealth, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL | wx.ALIGN_CENTER_VERTICAL, 5)

        bSizer15 = wx.BoxSizer(wx.VERTICAL)

        self.EditAirplaneHealthButton = wx.Button(sbSizer6.GetStaticBox(), wx.ID_ANY, u"编辑健康度范围", wx.DefaultPosition,
                                                  wx.DefaultSize, 0)
        bSizer15.Add(self.EditAirplaneHealthButton, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 5)

        self.ShowAirplaneHealthTextEntry = wx.TextCtrl(sbSizer6.GetStaticBox(), wx.ID_ANY, u"0 ~ 100%",
                                                       wx.DefaultPosition, wx.DefaultSize,
                                                       wx.TE_CENTER | wx.TE_READONLY)
        bSizer15.Add(self.ShowAirplaneHealthTextEntry, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALL, 5)

        gSizer12.Add(bSizer15, 1, wx.ALIGN_CENTER_HORIZONTAL | wx.ALIGN_CENTER_VERTICAL, 5)

        self.IsAirplaneHealthPrefer = wx.CheckBox(sbSizer6.GetStaticBox(), wx.ID_ANY, wx.EmptyString,
                                                  wx.DefaultPosition, wx.DefaultSize, 0)
        gSizer12.Add(self.IsAirplaneHealthPrefer, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL, 5)

        PriorityRentFromChoices = [u"1", u"2", u"3", u"4", u"5", u"没有"]
        self.PriorityRentFrom = wx.Choice(sbSizer6.GetStaticBox(), wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize,
                                          PriorityRentFromChoices, 0)
        self.PriorityRentFrom.SetSelection(5)
        gSizer12.Add(self.PriorityRentFrom, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL, 5)

        RentFromOfficialOrGamerRadiosChoices = [u"官方", u"玩家"]
        self.RentFromOfficialOrGamerRadios = wx.RadioBox(sbSizer6.GetStaticBox(), wx.ID_ANY, u"租赁来源",
                                                         wx.DefaultPosition,
                                                         wx.DefaultSize, RentFromOfficialOrGamerRadiosChoices, 2,
                                                         wx.RA_SPECIFY_COLS)
        self.RentFromOfficialOrGamerRadios.SetSelection(0)
        gSizer12.Add(self.RentFromOfficialOrGamerRadios, 0,
                     wx.ALL | wx.ALIGN_CENTER_HORIZONTAL | wx.ALIGN_CENTER_VERTICAL, 5)

        self.IsRentFromPrefer = wx.CheckBox(sbSizer6.GetStaticBox(), wx.ID_ANY, wx.EmptyString, wx.DefaultPosition,
                                            wx.DefaultSize, 0)
        gSizer12.Add(self.IsRentFromPrefer, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL, 5)

        sbSizer6.Add(gSizer12, 1, wx.EXPAND, 5)

        gSizer8.Add(sbSizer6, 1, wx.EXPAND, 5)

        bSizer9.Add(gSizer8, 1, wx.EXPAND, 5)

        gSizer10 = wx.GridSizer(1, 4, 0, 0)

        self.SaveCurrentAirplaneConfigButton = wx.Button(self, wx.ID_ANY, u"保存", wx.DefaultPosition, wx.DefaultSize, 0)
        gSizer10.Add(self.SaveCurrentAirplaneConfigButton, 0,
                     wx.ALL | wx.ALIGN_CENTER_HORIZONTAL | wx.ALIGN_CENTER_VERTICAL, 5)

        self.ExitWindowButton = wx.Button(self, wx.ID_ANY, u"退出/结束编辑", wx.DefaultPosition, wx.DefaultSize, 0)
        gSizer10.Add(self.ExitWindowButton, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL | wx.ALIGN_CENTER_VERTICAL, 5)

        self.LoadDesignerFromDiskButton = wx.Button(self, wx.ID_ANY, u"载入条件设计器", wx.DefaultPosition, wx.DefaultSize, 0)
        self.LoadDesignerFromDiskButton.SetToolTip(u"从磁盘中载入条件设计器数据。")

        gSizer10.Add(self.LoadDesignerFromDiskButton, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL | wx.ALIGN_CENTER_VERTICAL,
                     5)

        self.SaveDesignerToDiskButton = wx.Button(self, wx.ID_ANY, u"保存条件设计器", wx.DefaultPosition, wx.DefaultSize, 0)
        self.SaveDesignerToDiskButton.SetToolTip(u"将现在的条件设计器保存在磁盘上。")

        gSizer10.Add(self.SaveDesignerToDiskButton, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL | wx.ALIGN_CENTER_VERTICAL,
                     5)

        bSizer9.Add(gSizer10, 1, wx.EXPAND, 5)

        self.SetSizer(bSizer9)
        self.Layout()

        self.Centre(wx.BOTH)

        # Connect Events
        self.SelectAirplaneFamily.Bind(wx.EVT_CHOICE, self.SelectAirplaneFamilyOnChoice)
        self.SelectAirplaneInFamily.Bind(wx.EVT_CHOICE, self.SelectAirplaneInFamilyOnChoice)
        self.InputRentNumber.Bind(wx.EVT_TEXT, self.InputRentNumberOnText)
        self.PriorityPrice.Bind(wx.EVT_CHOICE, self.PriorityPriceOnChoice)
        self.EditStartPriceButton.Bind(wx.EVT_BUTTON, self.EditStartPriceButtonOnButtonClick)
        self.IsPricePrefer.Bind(wx.EVT_CHECKBOX, self.IsPricePreferOnCheckBox)
        self.PriorityAirplaneAge.Bind(wx.EVT_CHOICE, self.PriorityAirplaneAgeOnChoice)
        self.EditAirplaneAgeButton.Bind(wx.EVT_BUTTON, self.EditAirplaneAgeButtonOnButtonClick)
        self.PriorityHealth.Bind(wx.EVT_CHOICE, self.PriorityHealthOnChoice)
        self.EditAirplaneHealthButton.Bind(wx.EVT_BUTTON, self.EditAirplaneHealthButtonOnButtonClick)
        self.PriorityRentFrom.Bind(wx.EVT_CHOICE, self.PriorityRentFromOnChoice)
        self.SaveCurrentAirplaneConfigButton.Bind(wx.EVT_BUTTON, self.SaveCurrentAirplaneConfigButtonOnButtonClick)
        self.ExitWindowButton.Bind(wx.EVT_BUTTON, self.ExitWindowButtonOnButtonClick)
        self.LoadDesignerFromDiskButton.Bind(wx.EVT_BUTTON, self.LoadDesignerFromDiskButtonOnButtonClick)
        self.SaveDesignerToDiskButton.Bind(wx.EVT_BUTTON, self.SaveDesignerToDiskButtonOnButtonClick)

    def __del__(self):
        pass

    # Virtual event handlers, override them in your derived class
    def SelectAirplaneFamilyOnChoice(self, event):
        pass

    def SelectAirplaneInFamilyOnChoice(self, event):
        pass

    def InputRentNumberOnText(self, event):
        pass

    def PriorityPriceOnChoice(self, event):
        pass

    def EditStartPriceButtonOnButtonClick(self, event):
        pass

    def IsPricePreferOnCheckBox(self, event):
        pass

    def PriorityAirplaneAgeOnChoice(self, event):
        pass

    def EditAirplaneAgeButtonOnButtonClick(self, event):
        pass

    def PriorityHealthOnChoice(self, event):
        pass

    def EditAirplaneHealthButtonOnButtonClick(self, event):
        pass

    def PriorityRentFromOnChoice(self, event):
        pass

    def SaveCurrentAirplaneConfigButtonOnButtonClick(self, event):
        pass

    def ExitWindowButtonOnButtonClick(self, event):
        pass

    def LoadDesignerFromDiskButtonOnButtonClick(self, event):
        pass

    def SaveDesignerToDiskButtonOnButtonClick(self, event):
        pass


class MultiLevelBudgetManager(wx.Frame):
    BudgetData = {'Series': {}, 'GamerCashPercentage': 100.0, 'SingleBudget': 0, 'Reference': {}}
    # 数据结构备注：BudgetData:dict -> Series:dict -> {AirplaneFamilyName}:dict -> {AirplaneName}:dict -> Budget:int
    # Series表示系列，存储系列预算和独立预算
    # AirplaneFamilyName表示航机家族，AirplaneName表示航机家族的某一个航机，或者是 'all' 以存储机型家族统一定价
    flag_Modified = False

    def __init__(self, parent, callback_GetBudgetData, callback_UpdateData, selectedAirplaneFamily: str = '',
                 selectedAirplane: str = ''):
        """
        分级预算管理系统界面UI，负责展示对玩家现金、单一预算、系列预算及独立预算的页面并允许编辑。
        :param callback_GetBudgetData: 回调函数，用于取得预算数据，请注意数据是字典类，至少包含4个对应的单元。
        :param callback_UpdateData: 回调函数，用于类实例之间的数据同步。发送和取回的数据格式完全相同。
        :param selectedAirplaneFamily: 被选中的航机的家族，可选项
        :param selectedAirplane: 被选中的航机，可选项
        """
        if not (callable(callback_GetBudgetData) and callable(callback_UpdateData)):
            raise Exception('函数未定义，无法取得或更新数据。')
        self.function_GetBudgetData = callback_GetBudgetData
        self.function_PushBudgetData = callback_UpdateData

        wx.Frame.__init__(self, parent, id=wx.ID_ANY, title=u"分级预算管理系统", pos=wx.DefaultPosition, size=wx.Size(426, 439),
                          style=wx.CAPTION | wx.CLOSE_BOX | wx.MINIMIZE | wx.MINIMIZE_BOX | wx.TAB_TRAVERSAL)

        self.SetSizeHints(wx.DefaultSize, wx.DefaultSize)

        bSizer17 = wx.BoxSizer(wx.VERTICAL)

        gSizer13 = wx.GridSizer(0, 3, 0, 0)

        SelectAirplaneFamilyChoices = []
        self.SelectAirplaneFamily = wx.ListBox(self, wx.ID_ANY, wx.DefaultPosition, wx.Size(130, 300),
                                               SelectAirplaneFamilyChoices,
                                               wx.LB_HSCROLL | wx.LB_NEEDED_SB | wx.LB_SINGLE)
        self.SelectAirplaneFamily.SetToolTip(u"在这里选择航机家族。")

        gSizer13.Add(self.SelectAirplaneFamily, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 5)

        SelectAirplaneInFamilyChoices = []
        self.SelectAirplaneInFamily = wx.ListBox(self, wx.ID_ANY, wx.DefaultPosition, wx.Size(130, 300),
                                                 SelectAirplaneInFamilyChoices,
                                                 wx.LB_HSCROLL | wx.LB_NEEDED_SB | wx.LB_SINGLE)
        self.SelectAirplaneInFamily.SetToolTip(u"在这里选择具体的航机，以分别设置预算。\n或选择“全部”，以为整个航机家族统一预算。")

        gSizer13.Add(self.SelectAirplaneInFamily, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 5)

        bSizer18 = wx.BoxSizer(wx.VERTICAL)

        self.m_staticText59 = wx.StaticText(self, wx.ID_ANY, u"机型分类价\n      /\n独立预算", wx.DefaultPosition,
                                            wx.DefaultSize, 0)
        self.m_staticText59.Wrap(-1)

        bSizer18.Add(self.m_staticText59, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 5)

        self.SeriesOrIndependentBudgetInput = wx.TextCtrl(self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition,
                                                          wx.DefaultSize, 0)
        self.SeriesOrIndependentBudgetInput.SetToolTip(u"在这里输入机型分类预算或单航机预算。")

        bSizer18.Add(self.SeriesOrIndependentBudgetInput, 0, wx.ALL, 5)

        self.UseAirplanePriceButton = wx.Button(self, wx.ID_ANY, u"使用航机价格", wx.DefaultPosition, wx.DefaultSize, 0)
        self.UseAirplanePriceButton.SetToolTip(u"输入一个百分比以决定航机的预算（基于航机售价）。")

        bSizer18.Add(self.UseAirplanePriceButton, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 5)

        gSizer13.Add(bSizer18, 1, wx.ALIGN_CENTER_VERTICAL, 5)

        bSizer17.Add(gSizer13, 1, wx.EXPAND, 5)

        gSizer14 = wx.GridSizer(0, 2, 0, 0)

        self.m_staticText60 = wx.StaticText(self, wx.ID_ANY, u"玩家现金设置(?)", wx.DefaultPosition, wx.DefaultSize, 0)
        self.m_staticText60.Wrap(-1)

        self.m_staticText60.SetToolTip(u"您可以把预算限制在一个适当的大小内。")

        gSizer14.Add(self.m_staticText60, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL | wx.ALIGN_CENTER_VERTICAL, 5)

        self.m_staticText61 = wx.StaticText(self, wx.ID_ANY, u"单一预算设置", wx.DefaultPosition, wx.DefaultSize, 0)
        self.m_staticText61.Wrap(-1)

        gSizer14.Add(self.m_staticText61, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL, 5)

        gSizer15 = wx.GridSizer(0, 2, 0, 0)

        self.m_staticText62 = wx.StaticText(self, wx.ID_ANY, u"可用预算 = 玩家现金 ×             %", wx.DefaultPosition,
                                            wx.Size(-1, -1), 0)
        self.m_staticText62.Wrap(-1)

        gSizer15.Add(self.m_staticText62, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)

        self.PricePercentageInput = wx.TextCtrl(self, wx.ID_ANY, u"100", wx.Point(-1, -1), wx.Size(40, -1),
                                                wx.TE_CENTER)
        self.PricePercentageInput.SetToolTip(u"在这里输入1到100的百分比。")

        gSizer15.Add(self.PricePercentageInput, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL | wx.ALIGN_CENTER_VERTICAL, 5)

        gSizer14.Add(gSizer15, 1, wx.EXPAND, 5)

        self.SingleBudgetInput = wx.TextCtrl(self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0)
        self.SingleBudgetInput.SetToolTip(u"在这里输入单一预算。")

        gSizer14.Add(self.SingleBudgetInput, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL, 5)

        bSizer17.Add(gSizer14, 1, wx.EXPAND, 5)

        self.EndAndExitButton = wx.Button(self, wx.ID_ANY, u"结束编辑", wx.DefaultPosition, wx.DefaultSize, 0)
        self.EndAndExitButton.SetToolTip(u"退出。预算数据会自动保存。")

        bSizer17.Add(self.EndAndExitButton, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 5)

        self.SetSizer(bSizer17)
        self.Layout()

        self.Centre(wx.BOTH)

        # Connect Events
        self.SelectAirplaneFamily.Bind(wx.EVT_LISTBOX, self.SelectAirplaneFamilyOnListBox)
        self.SelectAirplaneInFamily.Bind(wx.EVT_LISTBOX, self.SelectAirplaneInFamilyOnListBox)
        self.SeriesOrIndependentBudgetInput.Bind(wx.EVT_KILL_FOCUS, self.SeriesOrIndependentBudgetInputOnKillFocus)
        self.SeriesOrIndependentBudgetInput.Bind(wx.EVT_TEXT, self.SeriesOrIndependentBudgetInputOnText)
        self.UseAirplanePriceButton.Bind(wx.EVT_BUTTON, self.UseAirplanePriceButtonOnButtonClick)
        self.PricePercentageInput.Bind(wx.EVT_KILL_FOCUS, self.PricePercentageInputOnKillFocus)
        self.PricePercentageInput.Bind(wx.EVT_TEXT, self.PricePercentageInputOnText)
        self.SingleBudgetInput.Bind(wx.EVT_KILL_FOCUS, self.SingleBudgetInputOnKillFocus)
        self.SingleBudgetInput.Bind(wx.EVT_TEXT, self.SingleBudgetInputOnText)
        self.EndAndExitButton.Bind(wx.EVT_BUTTON, self.EndAndExitButtonOnButtonClick)

        self.DataInit(selectedAirplaneFamily, selectedAirplane)

    def __del__(self):
        pass

    # Virtual event handlers, override them in your derived class
    def SelectAirplaneFamilyOnListBox(self, event):
        t1: dict = self.BudgetData.get('Series').get(self.SelectAirplaneFamily.GetStringSelection())
        t2 = [i for i in t1.keys()]
        t2[t2.index('all')] = '全部'
        self.SelectAirplaneInFamily.SetItems(t2)

    def SelectAirplaneInFamilyOnListBox(self, event):
        # 锁定文本框防止触发事件
        self.SeriesOrIndependentBudgetInput.Disable()
        self.SeriesOrIndependentBudgetInput.SetValue(
            str(self.BudgetData.get('Series').get(self.SelectAirplaneFamily.GetStringSelection(), {}).get(
                self.SelectAirplaneInFamily.GetStringSelection(), 0)))
        self.SeriesOrIndependentBudgetInput.Enable()

    def SeriesOrIndependentBudgetInputOnKillFocus(self, event):
        if self.flag_Modified:
            self.function_PushBudgetData(self.BudgetData)
            self.flag_Modified = False

    def SeriesOrIndependentBudgetInputOnText(self, event):
        if not self.SeriesOrIndependentBudgetInput.GetValue().isdigit():
            # 锁定文本框防止触发事件
            self.SeriesOrIndependentBudgetInput.Disable()
            # 重置文本框数据
            self.SeriesOrIndependentBudgetInput.SetValue(
                str(self.BudgetData.get('Series').get(self.SelectAirplaneFamily.GetStringSelection(), {}).get(
                    self.SelectAirplaneInFamily.GetStringSelection(), 0)))
            self.SeriesOrIndependentBudgetInput.Enable()
        else:
            self.BudgetData['Series'][self.SelectAirplaneFamily.GetStringSelection()][
                self.SelectAirplaneInFamily.GetStringSelection()] = int(self.SeriesOrIndependentBudgetInput.GetValue())
            self.flag_Modified = True

    def UseAirplanePriceButtonOnButtonClick(self, event):
        reference_price = self.BudgetData.get('Reference').get(self.SelectAirplaneFamily.GetStringSelection(), {}).get(
            self.SelectAirplaneInFamily.GetStringSelection(), 0)
        QuestionDialog = wx.TextEntryDialog(self, '请输入该航机价格（%d）的百分比：（0 ~ 100）' % reference_price,
                                            '航机价格百分比计算', '-1', wx.OK)
        QuestionDialog.ShowModal()
        t1: str = QuestionDialog.GetValue()
        QuestionDialog.Destroy()
        if t1.isdigit() or (t1.count('.') == 1 and t1.replace('.', '').isdigit()):
            if 0 < float(t1) <= 100:
                self.SeriesOrIndependentBudgetInput.Disable()
                self.SeriesOrIndependentBudgetInput.SetValue(str(int(float(t1) * reference_price)))
                self.SeriesOrIndependentBudgetInput.Enable()
            else:
                wx.MessageDialog(self, '数字应在0到100之间！可以输入小数！', '错误').ShowModal()
        else:
            wx.MessageDialog(self, '输入的不是数字！', '错误').ShowModal()

    def PricePercentageInputOnKillFocus(self, event):
        if self.flag_Modified:
            self.function_PushBudgetData(self.BudgetData)
            self.flag_Modified = False

    def PricePercentageInputOnText(self, event):
        t1: str = self.PricePercentageInput.GetValue()
        if t1.isdigit() or (t1.count('.') == 1 and t1.replace('.', '').isdigit()):
            self.BudgetData['GamerCashPercentage'] = float(self.PricePercentageInput.GetValue())
        else:
            self.PricePercentageInput.Disable()
            self.PricePercentageInput.SetValue(str(self.BudgetData.get('GamerCashPercentage')))
            self.PricePercentageInput.Enable()

    def SingleBudgetInputOnKillFocus(self, event):
        if self.flag_Modified:
            self.function_PushBudgetData(self.BudgetData)
            self.flag_Modified = False

    def SingleBudgetInputOnText(self, event):
        if self.SingleBudgetInput.GetValue().isdigit():
            self.BudgetData['SingleBudget'] = int(self.SingleBudgetInput.GetValue())
        else:
            self.SingleBudgetInput.Disable()
            self.SingleBudgetInput.SetValue(str(self.BudgetData.get('SingleBudget')))
            self.SingleBudgetInput.Enable()

    def EndAndExitButtonOnButtonClick(self, event):
        self.Close(True)

    # 内部规程函数
    def DataInit(self, AirplaneFamily: str = '', AirplaneName: str = ''):
        self.BudgetData.update(self.function_GetBudgetData())
        self.PricePercentageInput.Disable()
        self.PricePercentageInput.SetValue(str(self.BudgetData.get('GamerCashPercentage', 100)))
        self.PricePercentageInput.Enable()
        self.SingleBudgetInput.Disable()
        self.SingleBudgetInput.SetValue(str(self.BudgetData.get('SingleBudget', 0)))
        self.SingleBudgetInput.Enable()
        AirplaneSeries: dict = self.BudgetData.get('Series')
        AirplaneFamilies = [i for i in AirplaneSeries.keys()]
        # 重绘航机家族选择
        self.SelectAirplaneFamily.SetItems(AirplaneFamilies)
        try:
            if len(AirplaneFamilies) * len(AirplaneName) > 0:
                self.SelectAirplaneFamily.SetSelection(AirplaneFamilies.index(AirplaneFamily))
                theAirplaneList = [i for i in
                                   AirplaneSeries.get(AirplaneFamilies[AirplaneFamilies.index(AirplaneFamily)]).keys()]
                self.SelectAirplaneInFamily.SetItems(theAirplaneList)
                self.SelectAirplaneInFamily.SetSelection(theAirplaneList.index(AirplaneName))
                # 禁用控件防止触发文本更改
                self.SeriesOrIndependentBudgetInput.Disable()
                self.SeriesOrIndependentBudgetInput.SetValue(
                    str(self.BudgetData.get('Series').get(AirplaneFamily).get(AirplaneName)))
                self.SeriesOrIndependentBudgetInput.Enable()
        except:
            pass
