## AS自动排班助理

本项目实现了基于Python3和HTTP交互的AS自动排程。

在使用本项目前，您可能需要先安装 [Python3](https://www.python.org/downloads/release/python-397/) 环境。  
以及使用pip安装以下的包：

```shell
pip install requests beautifulsoup4 html5lib
```

本项目初步实现了以下功能：

- 基于自定义往返机场、服务、价格的单航机单航线自动排程
- 基于配置解析的单航机多航线自动排程
- 自动纠正时刻表异常并发出提醒

TODO：

- 允许用户选择出发和目的地的航站楼
- GUI化

目前本程序仍在进一步开发中，请在下方的联系方式中获取更多使用上的帮助。

### 感谢麻将航空（Q：1252066431）和“航空经营游戏爱好者交流群”（Q：623382722）对本项目的支持。