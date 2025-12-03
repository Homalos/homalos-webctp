# webctp

webctp 是一个基于 ctp 开发的提供 websocket 接口的 CTP 服务。

---

* [安装及运行](#安装及运行)
    * [环境搭建](#环境搭建)
    * [运行](#运行)
* [请求示例](#请求示例)
* [协议](#协议)
    * [通用协议格式](#通用协议格式)
    * [部分通用错误码说明](#部分通用错误码说明)
* [开发说明](#开发说明)
* [其他说明](#其他说明)

---

## 安装及运行

### 环境搭建

1. 准备 Python 环境(3.13+, 推荐 3.13)

2. 克隆 webctp
   ```bash
   $ git clone https://github.com/Homalos/homalos-webctp.git
   $ cd webctp
   ```
   
3. 安装依赖库
   
   **使用 uv (推荐)**
   
   ```bash
   $ uv sync
   ```
   
   **或使用 pip**
   
   ```bash
   $ pip install -e .
   ```
   
4. 配置

      > :pushpin: 项目使用 pyproject.toml 管理依赖，默认使用 CTP 版本为 6.7.10
      >
      > :pushpin: 配置参考示例 config.example.yaml，示例中行情和交易前置地址，默认配置的是 SimNow 7x24 环境， 更多 SimNow 环境详细信息参考 [SimNow官网](https://www.simnow.com.cn/product.action)、[openctp环境监控](http://121.37.80.177)，可根据需变更为其他支持CTPAPI(官方实现)的柜台环境。
      >
      > :pushpin: SimNow 7x24 环境：
      >
      > <table>
      > <tr>
      > 	<th colspan="3">前置信息</th>
      > </tr>
      > <tr>
      > 	<td>BrokerID</td>
      > 	<td>9999</td>
      > 	<td>券商ID</td>
      > </tr>
      > <tr>
      > 	<td>Trade Front</td>
      > 	<td>182.254.243.31:40001</td>
      > 	<td rowspan="2">（看穿式前置，使用监控中心生产秘钥）</td>
      > </tr>
      > <tr>
      > 	<td>Market Front</td>
      > 	<td>182.254.243.31:40011</td>
      > </tr>
      > <tr>
      > 	<td rowspan="2">交易阶段(服务时间)</td>
      > 	<td>交易日，16:00～次日09:00</td>
      > 	<td></td>
      > </tr>
      > <tr>
      > 	<td>非交易日，16:00～次日12:00</td>
      > 	<td></td>
      > </tr>
      > </table>
      > 该环境仅服务于CTP API开发爱好者，仅为用户提供CTP API测试需求，不提供结算等其它服务。
      >
      > 新注册用户，需要等到第三个交易日才能使用第二套环境。
      >
      > 账户、钱、仓跟第一套环境上一个交易日保持一致。
      >
      > :pushpin:  SimNow 非7x24环境：
      >
      > <table>
      > <tr>
      > 	<th colspan="4">前置信息</th>
      > </tr>
      > <tr>
      > 	<td>BrokerID</td>
      > 	<td colspan="3">9999</td>
      > </tr>
      > <tr>
      > 	<td>APPID</td>
      > 	<td colspan="3">simnow_client_test</td>
      > </tr>
      > <tr>
      > 	<td>AuthCode</td>
      > 	<td colspan="3">0000000000000000（16个0）</td>
      > </tr>
      > <tr>
      > 	<td rowspan="2">第一组</td>
      > 	<td>Trade Front</td>
      > 	<td>182.254.243.31:30001</td>
      > 	<td rowspan="6">（看穿式前置，使用监控中心生产秘钥）</td>
      > </tr>
      > <tr>
      > 	<td>Market Front</td>
      > 	<td>182.254.243.31:30012</td>
      > </tr>
      > <tr>
      > 	<td rowspan="2">第二组</td>
      > 	<td>Trade Front</td>
      > 	<td>182.254.243.31:30002</td>
      > </tr>
      > <tr>
      > 	<td>Market Front</td>
      > 	<td>182.254.243.31:30012</td>
      > </tr>
      > <tr>
      > 	<td rowspan="2">第三组</td>
      > 	<td>Trade Front</td>
      > 	<td>182.254.243.31:30003</td>
      > </tr>
      > <tr>
      > 	<td>Market Front</td>
      > 	<td>182.254.243.31:30013</td>
      > </tr>
      > <tr>
      > 	<td>交易阶段(服务时间)</td>
      > 	<td colspan="3">与实际生产环境保持一致。</td>
      > </tr>
      > </table>
      > 支持上期所期权、能源中心期权、中金所期权、广期所期权、郑商所期权、大商所期权
      > 用户注册后，默认的 APPID 为 simnow_client_test，认证码为 0000000000000000（16个0），默认开启终端认证，程序化用户可以选择不开终端认证接入。
> 交易品种：六所所有期货品种以及上期所、能源中心、中金所、广期所所有期权品种，以及郑商所、大商所部分期权品种。
   > 账户资金：初始资金两千万，支持入金，每日最多三次。
> 见 [SimNow官网](https://www.simnow.com.cn/product.action)
   
   创建自己的行情配置 config_md.yaml :
   
      ```yaml 
   TdFrontAddress: tcp://182.254.243.31:40001 # 交易前置地址
   MdFrontAddress: tcp://182.254.243.31:40011 # 行情前置地址
   BrokerID: "9999"
   AuthCode: "0000000000000000"
   AppID: simnow_client_test
   Port: 8080         # the listening port, default 8080
Host: 127.0.0.1      # the bind ip address, default 127.0.0.1
   LogLevel: INFO     # NOTSET, DEBUG, INFO, WARN, ERROR, CRITICAL
   ```
   
   创建自己的交易配置 config_td.yaml :
   
      ```yaml 
   TdFrontAddress: tcp://182.254.243.31:40001 # 交易前置地址
   MdFrontAddress: tcp://182.254.243.31:40011 # 行情前置地址
   BrokerID: "9999"
   AuthCode: "0000000000000000"
   AppID: simnow_client_test
   Port: 8081         # the listening port, default 8081
   Host: 127.0.0.1      # the bind ip address, default 127.0.0.1
   LogLevel: INFO     # NOTSET, DEBUG, INFO, WARN, ERROR, CRITICAL
      ```



### 运行

```bash
# 启动交易服务
$ python main.py --config=config_td.yaml --app_type=td
# 启动行情服务
$ python main.py --config=config_md.yaml --app_type=md
```

## 请求示例

> :pushpin: 见 [md_protocol.md](docs/md_protocol.md)、[td_protocol.md](docs/td_protocol.md)

### 部分示例

示例是基于 SimNow 电信1环境，不同环境的数据存在差异，以下示例数据未必可全部通过，根据环境调整即可。

<details>
<summary>登录</summary>

```json
{
  "MsgType": "ReqUserLogin",
  "ReqUserLogin": {
    "UserID": "028742",
    "Password": "123456"
  }
}
```
</details>

## 协议

### 通用协议格式

``` python
# 请求
{
  "MsgType": "{method_name}",
  "{request_field}": {
    "filed1": {value1},
    "...": "...",
    "fieldn": {valuen}
  },
  "RequestID": 1
}

# 响应
{
    "MsgType": "{rsp_of_method}",
    "RspInfo": {
        "ErrorID": 0,
        "ErrorMsg": "OK"
    },
    "IsLast": true,
    "RequestID": 1
    "{response_filed}": {response_body}  # 具体参见详细文档
}
```

### 部分通用错误码说明

```bash
ErrorID="-400" ErrorMsg="参数有误"
ErrorID="-401" ErrorMsg="未登录"
ErrorID="-404" ErrorMsg="Webctp还未实现该方法"
ErrorID="-1" ErrorMsg="CTP:请求失败"
ErrorID="-2" ErrorMsg="CTP:未处理请求超过许可数"
ErrorID="-3" ErrorMsg="CTP:每秒发送请求数超过许可数"
ErrorID="0" ErrorMsg="CTP:正确"
ErrorID="1" ErrorMsg="CTP:不在已同步状态"
ErrorID="2" ErrorMsg="CTP:会话信息不一致"
ErrorID="3" ErrorMsg="CTP:不合法的登录"
ErrorID="4" ErrorMsg="CTP:用户不活跃"
ErrorID="5" ErrorMsg="CTP:重复的登录"
ErrorID="6" ErrorMsg="CTP:还没有登录"
ErrorID="7" ErrorMsg="CTP:还没有初始化"
ErrorID="8" ErrorMsg="CTP:前置不活跃"
ErrorID="9" ErrorMsg="CTP:无此权限"
ErrorID="10" ErrorMsg="CTP:修改别人的口令"
ErrorID="11" ErrorMsg="CTP:找不到该用户"
ErrorID="12" ErrorMsg="CTP:找不到该经纪公司"
ErrorID="13" ErrorMsg="CTP:找不到投资者"
ErrorID="14" ErrorMsg="CTP:原口令不匹配"
ErrorID="15" ErrorMsg="CTP:报单字段有误"
ErrorID="16" ErrorMsg="CTP:找不到合约"
```

### 详细接口文档

[交易服务协议文档](./docs/td_protocol.md)

[行情服务协议文档](./docs/md_protocol.md)

# 开发说明

## 项目结构

```
webctp/
├── apps/              # FastAPI 应用入口
│   ├── md_app.py     # 行情服务应用
│   └── td_app.py     # 交易服务应用
├── clients/           # CTP 客户端封装
│   ├── md_client.py  # 行情客户端
│   └── td_client.py  # 交易客户端
├── services/          # 业务逻辑层
│   ├── base_client.py    # 客户端基类
│   ├── md_client.py      # 行情服务
│   ├── td_client.py      # 交易服务
│   └── connection.py     # WebSocket 连接管理
├── constants/         # 常量定义
├── model/            # 数据模型
├── utils/            # 工具函数
└── docs/             # 文档
```

## 架构说明

### 三层架构

1. **应用层 (apps/)**: FastAPI WebSocket 端点
2. **服务层 (services/)**: 异步/同步边界处理，消息路由
3. **客户端层 (clients/)**: CTP API 封装

### 核心组件

- **BaseClient**: 抽象基类，提供公共的客户端管理逻辑
- **TdClient/MdClient (services)**: 处理 WebSocket 消息和 CTP 客户端的交互
- **TdClient/MdClient (clients)**: 封装 CTP API 调用

## 开发指南

### 本地开发

1. 安装开发依赖
   ```bash
   $ uv sync --dev
   ```

2. 配置文件
   ```bash
   $ cp config.sample.yaml config_md.yaml
   $ cp config.sample.yaml config_td.yaml
   # 编辑配置文件，填入正确的前置地址和认证信息
   ```

3. 启动服务
   ```bash
   # 启动行情服务
   $ python main.py --config=config_md.yaml --app_type=md
   # 启动交易服务
   $ python main.py --config=config_td.yaml --app_type=td
   ```

### 代码规范

- 使用类型注解 (Type Hints)
- 遵循 PEP 8 代码风格
- 使用有意义的变量和函数名
- 添加必要的文档字符串

### 添加新的 API

1. 在 `clients/` 中添加 CTP API 封装方法
2. 在 `services/` 的 `_init_call_map` 中注册新方法
3. 在 `constants/` 中添加相应的常量定义
4. 更新协议文档

### 测试

建议在 SimNow 仿真环境中进行充分测试后再接入生产环境。

更多详细信息请参考 [开发文档](./docs/development.md)

# 其他说明

* 由于精力有限，只进行了 SimNow 平台的简单的测试，请自行充分测试后再接入生产环境。
* 使用 webctp 进行实盘交易的后果完全有使用者自行承担。
