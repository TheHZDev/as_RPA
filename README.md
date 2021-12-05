## AS自动排班助理

本项目实现了基于Python3和HTTP交互的AS自动排程。

* 菜单

    - [准备使用](#准备使用)
    - [自动排程示例](#自动排程示例)
    - [信息收集示例](#信息收集示例)
    - [高级自动排程示例](#高级自动排程)

<a id="prepare-use"></a>

### 准备使用

在使用本项目前，您可能需要先安装 [Python3](https://www.python.org/downloads/release/python-398/) 环境。  
以及使用pip安装以下的包：

```shell
pip install requests[socks] beautifulsoup4 html5lib wxPython zhconv
```

本项目初步实现了以下功能：

- 基于自定义往返机场、服务、价格的单航机单航线自动排程
- 基于配置解析的单航机多航线自动排程
- 自动纠正时刻表异常并发出提醒
- 允许用户选择出发和目的地的航站楼

----
TODO：

- GUI化

目前本程序仍在进一步开发中，请在下方的联系方式中获取更多使用上的帮助。

**感谢麻将航空（Q：1252066431）和“航空经营游戏爱好者交流群”（Q：623382722）对本项目的支持。**

<a id="example-auto-execute-flight-plan"></a>

### 自动排程示例

在本地项目中新建文件**Main.py**，然后先输入以下代码：

```python
from LoginAirlineSim import LoginAirlineSim
from Flight_Planning_System import Flight_Planning_Sub_System

MyUserName = input('你的用户名是：')
MyPasswd = input('你的登陆密码是：')
ServerName = input('要登陆的服务器名是：')

PreLogin = LoginAirlineSim(ServerName, MyUserName, MyPasswd)
FleetManager = Flight_Planning_Sub_System(PreLogin, ServerName)
```

在运行程序前，你应该知道登陆的服务器名，以及对应的用户名和密码。  
如果你不想在运行时动态输入这些东西，可以将以上代码的对应三行改成这样：  
（这里假设登陆Otto服务器，用户名为Administrator，密码为123456）

```python
MyUserName = 'Administrator'
MyPasswd = '123456'
ServerName = 'Otto'
```

然后，你需要规划好待排班飞机的排程信息，包括初始起飞时间、服务方案全称（AS上你设定的服务方案全称）、每趟航班的价格百分比。  
这里，我以一条路线为HKG-REP-HKG，服务方案为Standard，价格百分比为150，起飞时间为UTC 16:07 的航线演示对绰号为B-AAA的航机是怎么排程的。

```python
Scheme_B_AAA = FleetManager.Experimental_MakeFlightPlanConfig('HKG-REP-HKG', ['Standard', 'Standard'], [150, 150],
                                                              '16:07')
```

它可以被简化为

```python
Scheme_B_AAA = FleetManager.Experimental_MakeFlightPlanConfig('HKG-REP-HKG', ['Standard'], [150], '16:07')
```

由于我在程序中使用了循环冗余的方法来安排方案和价格百分比，原本2条航线需要安排两个服务方案和价格，现在只需要使用一个即可。  
现在让我为您演示实际执行的过程：

```python
ToManageFleets = FleetManager.SearchFleets()
for FleetURL in ToManageFleets.keys():
    if ToManageFleets.get(FleetURL).get('NickName') == 'B-AAA':
        FleetManager.UI_AutoMakeFlightPlan(FleetURL, Scheme_B_AAA)
```

如果在此基础上，还需要为另一架绰号为B-ATU的航机排班，以上代码可修改为

```python
ToManageFleets = FleetManager.SearchFleets()
for FleetURL in ToManageFleets.keys():
    if ToManageFleets.get(FleetURL).get('NickName') == 'B-AAA':
        FleetManager.UI_AutoMakeFlightPlan(FleetURL, Scheme_B_AAA)
    elif ToManageFleets.get(FleetURL).get('NickName') == 'B-ATU':
        FleetManager.UI_AutoMakeFlightPlan(FleetURL, Scheme_B_AAA)
```

只需要更改一些条件，就能快捷地分配排班方案。  
最后让我们把所有代码整合起来：

```python
from LoginAirlineSim import LoginAirlineSim
from Flight_Planning_System import Flight_Planning_Sub_System

MyUserName = input('你的用户名是：')
MyPasswd = input('你的登陆密码是：')
ServerName = input('要登陆的服务器名是：')

PreLogin = LoginAirlineSim(ServerName, MyUserName, MyPasswd)
FleetManager = Flight_Planning_Sub_System(PreLogin, ServerName)
try:
    Scheme_B_AAA = FleetManager.Experimental_MakeFlightPlanConfig('HKG-REP-HKG', ['Standard'], [150], '16:07')
    ToManageFleets = FleetManager.SearchFleets()
    for FleetURL in ToManageFleets.keys():
        if ToManageFleets.get(FleetURL).get('NickName') == 'B-AAA':
            FleetManager.UI_AutoMakeFlightPlan(FleetURL, Scheme_B_AAA)
finally:
    FleetManager.close()
```

如果一切顺利且没有出错，您的航机将会排班成功，如您遇到了这样或那样的问题，欢迎使用GitHub的Issue向我提问。

### 信息收集示例

目前信息收集的功能主要为资产计算，后续会增加机场信息收集。  
资产计算主要考虑的是各航司的飞机数量及座椅价格。  
由于贷款和现金等具体财务数据为非公开数据，本程序收集的信息可能不尽准确，敬请谅解。  
新建程序文件**Main.py**，填入以下内容：  
**（重要提示：您必须在对应的服务器开设企业才能取得具体的资产信息，或者使用公开数据库）**

```python
from GetOtherInfo import CalcAirplaneProperty
from time import sleep
from threading import Thread

ServerName = input('请输入要收集信息的服务器名称：')
MyUserName = input('请输入您在%s服务器上的用户名，或者放空：' % ServerName)
MyPasswd = input('请输入您在%s服务器上的密码，或者放空：' % ServerName)

CalcService = CalcAirplaneProperty(ServerName, MyUserName, MyPasswd)
CalcService.getAirplaneInfoIndex()
while len(CalcService.cache_CountryIndex) > 0:
    sleep(30)
CalcService.getAirCompanyInfoIndex()
Thread(target=CalcService.thread_getAirplanePrice).start()
while len(CalcService.cache_AirCompanyURL) > 0 or not CalcService.flag_price_ok:
    sleep(30)
sleep(10)
resultList = CalcService.CalcBalanceSheet()
# 输出到控制台并非明智之举，可以改为输出到Excel或HTML
# print('企业名称\t资产数额')
# for line in resultList:
#   print('%s\t%.2f K AS$' % (line[0], line[1] / 1000))

# CalcService.OutputPropertyToExcel(resultList)  # 输出到Excel
CalcService.OutputPropertyToHTML(resultList)  # 输出到HTML
```

如果您知悉航机数据表有更新，请删除生成的数据库文件（.sqlite）以降低程序出错概率。  
多线程抓取信息的时候有可能会卡住，请在网络状况良好时再尝试。

如果需要使用机场信息抓取功能，请填入以下代码并执行：

```python
from GetOtherInfo import GetAirportInfo

GetAirportInfo('Otto')
```

该程序将自动抓取Otto服务器的机场信息，并在控制台上显示。  
数据会被保存在同目录下的数据库文件中，以便之后查询。

### 高级自动排程

在前面的示例中，使用了相对简单的参数和函数完成了基本的排程管理。但实际操作的时候，往往需要同时对多架飞机进行不同的排程管理，甚至还可能会调整航机的起飞时间和飞行速度。  
在这个示例中，我会对三架飞机进行排程操作，并讲解不同的参数的作用。

第1架飞机的航机编号为B-HKG，路线为HKG-SIN-HKG，第一趟起飞时间为17:05，服务方案分别为ServiceA和ServiceB，价格分别为70和130，  
**HKG至SIN的航班使用最高巡航速度，SIN至HKG的航班使用最低巡航速度**  
则代码可以写成：

```python
Scheme_B_HKG = FleetManager.Experimental_MakeFlightPlanConfig('HKG-SIN-HKG', ['ServiceA', 'ServiceB'], [70, 130],
                                                              '17:05', SpeedConfig=('Max', 'Min'))
```

第2架飞机的航机编号为B-HMMS，路线为HKG-BLR-HKG-KUL-HKG，第一趟起飞时间为1:20，服务方案统一为ServiceC，价格统一为120，速度统一为最高巡航速度。  
**其中所有从HKG出发的航班使用T2航站楼，所有到达HKG的航班使用T3航站楼。**  
则代码可以写成：

```python
Scheme_B_HMMS = FleetManager.Experimental_MakeFlightPlanConfig('HKG-BLR-HKG-KUL-HKG', ['ServiceC'], [120], '1:20',
                                                               SpeedConfig=('Max'),
                                                               TerminalConfig=[('T2', 'T1'), ('T1', 'T3')])
```

航站楼的设置也是允许循环使用的。

第3架飞机的航机编号为P-257，路线为PEK-HKG-SIN-SYD-PEK，第1，2，3趟航班的起飞时间分别为4:20、6:45、8:
50，最后一趟航班使用系统推荐时间，服务方案统一为ServiceD，价格分别为110、200、50、80， 其中  
**PEK至HKG的航程使用最高巡航速度，SIN至SYD的航程使用最低巡航速度，其它航程保持最佳巡航速度不变。经过HKG的航班都使用T2航站楼，经过SYD的都使用T5航站楼。**  
在这个示例中，由于配置变得相对复杂化，我将使用原始方法演示配置过程：

```python
Scheme_P_257 = [
    FleetManager.MakeSingleFlightPlan('PEK', 'HKG', 110, 'ServiceD', '4:20', ('T1', 'T2'), 'Max'),
    FleetManager.MakeSingleFlightPlan('HKG', 'SIN', 200, 'ServiceD', '6:45', ('T2', 'T1'), 'Normal'),
    FleetManager.MakeSingleFlightPlan('SIN', 'SYD', 50, 'ServiceD', '8:50', ('T1', 'T5'), 'Min'),
    FleetManager.MakeSingleFlightPlan('SYD', 'PEK', 80, 'ServiceD', '', ('T5', 'T1'), 'Normal')
]
```

**（注意：以上航班均为演示需要而随机使用了机场和时间，请勿直接照搬到游戏排班中！！！）**