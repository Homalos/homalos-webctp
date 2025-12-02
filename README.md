# webctp

webctp是一个基于 [openctp-ctp](https://github.com/openctp/openctp-ctp-python) 开发的提供websocket接口的CTP服务。

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

1. 准备Python环境(3.10+, 推荐 3.10 或 3.11)
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
   
   > :pushpin: 项目使用 pyproject.toml 管理依赖，默认使用 openctp-ctp 6.7.11.0+自定义配置文件  
   参考示例 config.example.yaml
   > :pushpin: 示例中行情和交易前置地址，默认配置的是 SimNow 7x24 环境， 更多 SimNow
   环境参考 [openctp环境监控](http://121.37.80.177)，可根据需要变更为其他支持CTPAPI(官方实现)的柜台环境。

   创建自己的行情配置 config_md.yaml :
   ```yaml 
   TdFrontAddress: tcp://182.254.243.31:40001 # 交易前置地址
   MdFrontAddress: tcp://182.254.243.31:40011 # 行情前置地址
   BrokerID: "9999"
   AuthCode: "0000000000000000"
   AppID: simnow_client_test
   Port: 8080         # the listening port, default 8080
   Host: 127.0.0.1      # the bind ip address, default 0.0.0.0
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
   Host: 127.0.0.1      # the bind ip address, default 0.0.0.0
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

> :pushpin: Postman 请求样例待补充，目前提供 Apifox 示例

### 示例（部分）

示例是基于 SimNow 电信1环境，不同环境的数据存在差异，以下示例数据未必可全部通过，根据环境调整即可。

<details>
<summary>登录</summary>
<details>
<summary>请求查询成交</summary>
<details>
<summary>请求查询投资者持仓</summary>
<details>
<summary>请求查询资金账户</summary>
<details>
<summary>请求查询投资者</summary>
<details>
<summary>请求查询交易编码</summary>
<details>
<summary>查询合约保证金率</summary>
<details>
<summary>请求查询合约手续费率</summary>
<details>
<summary>查询期权合约手续费</summary>
<details>
<summary>查询期权交易成本</summary>
<details>
<summary>查询报单手续费率</summary>
<details>
<summary>查询交易所保证金率</summary>
<details>
<summary>查询投资者持仓明细</summary>
<details>
<summary>查询行情</summary>
<details>
<summary>查询产品</summary>
<details>
<summary>查询交易所</summary>
<details>
<summary>查询合约</summary>
<details>
<summary>查询报单</summary>
<details>
<summary>查询最大报单数量</summary>
<details>
<summary>用户口令变更</summary>
<details>
<summary>报单录入（限价单）</summary>
<details>
<summary>报单撤销</summary>
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

* 由于精力有限，只进行了SimNow平台的简单的测试，请自行充分测试后再接入生产环境。
* 使用webctp进行实盘交易的后果完全有使用者自行承担。
