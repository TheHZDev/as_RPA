import urllib3
import wx

from GUI.GUI_AutoFlightPlanningBaseOnExcel import GUIAutoFlightPlanningBaseOnExcel, Public_ConfigDB_Path
from GUI.GUI_LoginAS import LoginAirlineSimDialog

urllib3.disable_warnings()


def callback_afterLogonInit(logonSession, serverName):
    """对话框后，才初始化主窗口"""
    global mainWin, mainSession
    preDialog.Destroy()
    mainWin = GUIAutoFlightPlanningBaseOnExcel(logonSession, serverName)
    mainSession = logonSession
    mainWin.Show()


if __name__ == '__main__':
    mainAPP = wx.App()
    mainWin = None
    mainSession = None
    try:
        preDialog = LoginAirlineSimDialog(None, Public_ConfigDB_Path, callback_afterLogonInit)
        preDialog.Show()
        mainAPP.MainLoop()
    finally:
        from AirlineSim.LoginAirlineSim import LogoutAirlineSim
        from sys import exit

        LogoutAirlineSim(mainSession)
        exit(0)
