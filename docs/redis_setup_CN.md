# Redis 配置指南

**项目**: homalos-webctp\
**版本**: v0.2.0\
**更新日期**: 2025-12-15

______________________________________________________________________

## 概述

本文档说明如何为 homalos-webctp 配置 Redis 缓存服务。Redis 用于缓存行情数据、账户状态，并通过 Pub/Sub 实现行情广播。

______________________________________________________________________

## 系统要求

### Redis 版本

- **最低版本**: Redis 3.0+
- **推荐版本**: Redis 5.0+ 或更高
- **当前测试版本**: Redis 3.0.504（Windows）

### 系统资源

- **内存**: 建议至少 512 MB 可用内存
- **磁盘**: 建议至少 1 GB 可用空间（用于持久化）
- **网络**: 本地连接或低延迟网络

______________________________________________________________________

## 安装 Redis

### Windows 安装

#### 方法 1: MSI 安装包（推荐）

1. 下载 Redis for Windows: https://github.com/microsoftarchive/redis/releases
1. 运行 MSI 安装程序
1. 选择安装路径（默认: `C:\Program Files\Redis`）
1. 勾选"Add Redis to PATH"
1. 勾选"Install Windows Service"
1. 完成安装

#### 方法 2: Chocolatey

```powershell
choco install redis-64
```

#### 方法 3: WSL (Windows Subsystem for Linux)

```bash
# 在 WSL 中
sudo apt-get update
sudo apt-get install redis-server
```

### Linux 安装

#### Ubuntu/Debian

```bash
sudo apt-get update
sudo apt-get install redis-server
```

#### CentOS/RHEL

```bash
sudo yum install redis
```

#### 从源码编译

```bash
wget http://download.redis.io/redis-stable.tar.gz
tar xvzf redis-stable.tar.gz
cd redis-stable
make
sudo make install
```

______________________________________________________________________

## 启动 Redis

### Windows

#### 方法 1: Windows 服务（推荐）

```powershell
# 启动服务
net start Redis

# 停止服务
net stop Redis

# 查看服务状态
sc query Redis
```

#### 方法 2: 命令行

```powershell
# 前台运行
redis-server

# 指定配置文件
redis-server C:\path\to\redis.conf
```

### Linux

#### 使用 systemd

```bash
# 启动服务
sudo systemctl start redis

# 停止服务
sudo systemctl stop redis

# 重启服务
sudo systemctl restart redis

# 查看状态
sudo systemctl status redis

# 开机自启
sudo systemctl enable redis
```

#### 命令行

```bash
# 前台运行
redis-server

# 后台运行
redis-server --daemonize yes

# 指定配置文件
redis-server /etc/redis/redis.conf
```

______________________________________________________________________

## 验证 Redis 安装

### 使用 redis-cli

```bash
# 连接到 Redis
redis-cli

# 测试连接
127.0.0.1:6379> PING
PONG

# 设置值
127.0.0.1:6379> SET test "hello"
OK

# 获取值
127.0.0.1:6379> GET test
"hello"

# 退出
127.0.0.1:6379> EXIT
```

### 使用测试脚本

```bash
# 激活虚拟环境
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux

# 运行测试脚本
python scripts/test_redis.py
```

测试脚本会验证：

- ✅ Redis 连接
- ✅ 基本操作（SET/GET/HASH/DELETE）
- ✅ Pub/Sub 功能
- ✅ 性能测试

______________________________________________________________________

## Redis 配置

### 配置文件位置

#### Windows

- 默认: `C:\Program Files\Redis\redis.windows.conf`
- 服务配置: `C:\Program Files\Redis\redis.windows-service.conf`

#### Linux

- Ubuntu/Debian: `/etc/redis/redis.conf`
- CentOS/RHEL: `/etc/redis.conf`

### 重要配置项

#### 1. 网络配置

```conf
# 绑定地址（默认只允许本地连接）
bind 127.0.0.1

# 端口
port 6379

# 超时时间（秒，0 表示禁用）
timeout 0
```

#### 2. 内存配置

```conf
# 最大内存限制（建议设置）
maxmemory 512mb

# 内存淘汰策略
maxmemory-policy allkeys-lru
```

推荐的淘汰策略：

- `allkeys-lru`: 所有键使用 LRU 算法淘汰（推荐）
- `volatile-lru`: 只对设置了过期时间的键使用 LRU
- `allkeys-lfu`: 所有键使用 LFU 算法（Redis 4.0+）

#### 3. 持久化配置

**RDB 快照（默认启用）**:

```conf
# 自动保存规则
save 900 1      # 900 秒内至少 1 个键变化
save 300 10     # 300 秒内至少 10 个键变化
save 60 10000   # 60 秒内至少 10000 个键变化

# RDB 文件名
dbfilename dump.rdb

# 数据目录
dir ./
```

**AOF 日志（可选，更安全）**:

```conf
# 启用 AOF
appendonly yes

# AOF 文件名
appendfilename "appendonly.aof"

# 同步策略
appendfsync everysec  # 每秒同步（推荐）
# appendfsync always  # 每次写入同步（最安全但慢）
# appendfsync no      # 由操作系统决定（最快但不安全）
```

#### 4. 日志配置

```conf
# 日志级别
loglevel notice

# 日志文件
logfile "redis.log"
```

______________________________________________________________________

## homalos-webctp 配置

### 配置文件

在 `config/config_md.yaml` 和 `config/config_td.yaml` 中配置 Redis：

```yaml
# Redis 缓存配置（可选，默认禁用）
Redis:
  Enabled: true                    # 启用 Redis
  Host: localhost                  # Redis 主机
  Port: 6379                       # Redis 端口
  Password: ""                     # Redis 密码（如有）
  DB: 0                            # 数据库编号
  MaxConnections: 50               # 最大连接数
  SocketTimeout: 5.0               # 套接字超时（秒）
  SocketConnectTimeout: 5.0        # 连接超时（秒）
  MarketSnapshotTTL: 60            # 行情快照 TTL（秒）
  MarketTickTTL: 5                 # 实时 tick TTL（秒）
  OrderTTL: 86400                  # 订单 TTL（秒，24小时）
```

### 环境变量

也可以通过环境变量配置（优先级高于配置文件）：

```bash
# Windows PowerShell
$env:WEBCTP_REDIS_ENABLED="true"
$env:WEBCTP_REDIS_HOST="localhost"
$env:WEBCTP_REDIS_PORT="6379"
$env:WEBCTP_REDIS_PASSWORD=""
$env:WEBCTP_REDIS_DB="0"

# Linux/Mac
export WEBCTP_REDIS_ENABLED=true
export WEBCTP_REDIS_HOST=localhost
export WEBCTP_REDIS_PORT=6379
export WEBCTP_REDIS_PASSWORD=
export WEBCTP_REDIS_DB=0
```

______________________________________________________________________

## 性能优化

### 1. 连接池配置

根据系统负载调整连接池大小：

| 负载 | MaxConnections | 说明               |
| ---- | -------------- | ------------------ |
| 低   | 10-20          | 单客户端，低频操作 |
| 中   | 30-50          | 多客户端，正常操作 |
| 高   | 50-100         | 多客户端，高频操作 |

### 2. TTL 配置

根据数据特性调整 TTL：

| 数据类型  | 推荐 TTL | 说明                     |
| --------- | -------- | ------------------------ |
| 行情快照  | 60 秒    | 相对稳定，可缓存较长时间 |
| 实时 tick | 5 秒     | 快速变化，短时间缓存     |
| 订单记录  | 24 小时  | 历史记录，长时间保留     |
| 持仓信息  | 无限期   | 实时更新，不过期         |
| 资金信息  | 无限期   | 实时更新，不过期         |

### 3. 内存优化

```conf
# 设置合理的最大内存
maxmemory 512mb  # 根据系统内存调整

# 使用 LRU 淘汰策略
maxmemory-policy allkeys-lru

# 启用内存压缩（Redis 7.0+）
# activedefrag yes
```

### 4. 持久化优化

**生产环境推荐配置**:

```conf
# 启用 RDB 快照
save 900 1
save 300 10
save 60 10000

# 启用 AOF 日志
appendonly yes
appendfsync everysec

# AOF 重写优化
auto-aof-rewrite-percentage 100
auto-aof-rewrite-min-size 64mb
```

______________________________________________________________________

## 监控和维护

### 1. 监控 Redis 状态

#### 使用 redis-cli

```bash
# 查看信息
redis-cli INFO

# 查看内存使用
redis-cli INFO memory

# 查看客户端连接
redis-cli CLIENT LIST

# 查看慢查询
redis-cli SLOWLOG GET 10
```

#### 使用 Python 脚本

```python
import redis

client = redis.Redis(host='localhost', port=6379, decode_responses=True)

# 获取信息
info = client.info()
print(f"已使用内存: {info['used_memory_human']}")
print(f"连接数: {info['connected_clients']}")
print(f"命中率: {info.get('keyspace_hits', 0) / (info.get('keyspace_hits', 0) + info.get('keyspace_misses', 1)):.2%}")
```

### 2. 性能监控

homalos-webctp 自动监控 Redis 性能：

- **命中率**: 每分钟报告缓存命中率
- **延迟**: 记录 Redis 操作延迟
- **连接数**: 监控连接池使用情况

查看监控日志：

```bash
# 查看性能报告
tail -f logs/webctp.log | grep "性能报告"

# 查看 Redis 告警
tail -f logs/webctp.log | grep "Redis"
```

### 3. 数据备份

#### 手动备份

```bash
# 触发 RDB 快照
redis-cli BGSAVE

# 复制 RDB 文件
cp /path/to/dump.rdb /backup/dump_$(date +%Y%m%d).rdb
```

#### 自动备份脚本（Linux）

```bash
#!/bin/bash
# backup_redis.sh

BACKUP_DIR="/backup/redis"
DATE=$(date +%Y%m%d_%H%M%S)

# 创建备份目录
mkdir -p $BACKUP_DIR

# 触发快照
redis-cli BGSAVE

# 等待快照完成
sleep 5

# 复制文件
cp /var/lib/redis/dump.rdb $BACKUP_DIR/dump_$DATE.rdb

# 删除 7 天前的备份
find $BACKUP_DIR -name "dump_*.rdb" -mtime +7 -delete

echo "备份完成: $BACKUP_DIR/dump_$DATE.rdb"
```

#### 定时任务（crontab）

```bash
# 每天凌晨 2 点备份
0 2 * * * /path/to/backup_redis.sh
```

### 4. 数据恢复

#### 从 RDB 恢复

```bash
# 1. 停止 Redis
sudo systemctl stop redis

# 2. 替换 RDB 文件
cp /backup/dump_20251215.rdb /var/lib/redis/dump.rdb

# 3. 启动 Redis
sudo systemctl start redis
```

#### 从 AOF 恢复

```bash
# 1. 停止 Redis
sudo systemctl stop redis

# 2. 替换 AOF 文件
cp /backup/appendonly_20251215.aof /var/lib/redis/appendonly.aof

# 3. 启动 Redis
sudo systemctl start redis
```

______________________________________________________________________

## 故障排查

### 问题 1: 无法连接到 Redis

**症状**: `ConnectionError: Error connecting to localhost:6379`

**解决方案**:

1. 检查 Redis 服务是否运行

   ```bash
   # Windows
   sc query Redis

   # Linux
   sudo systemctl status redis
   ```

1. 检查端口是否被占用

   ```bash
   # Windows
   netstat -ano | findstr :6379

   # Linux
   netstat -tlnp | grep 6379
   ```

1. 检查防火墙设置

   ```bash
   # Windows
   netsh advfirewall firewall add rule name="Redis" dir=in action=allow protocol=TCP localport=6379

   # Linux
   sudo ufw allow 6379/tcp
   ```

### 问题 2: Redis 内存不足

**症状**: `OOM command not allowed when used memory > 'maxmemory'`

**解决方案**:

1. 增加最大内存限制

   ```conf
   maxmemory 1gb
   ```

1. 启用内存淘汰策略

   ```conf
   maxmemory-policy allkeys-lru
   ```

1. 清理不需要的数据

   ```bash
   redis-cli FLUSHDB  # 清空当前数据库
   redis-cli FLUSHALL # 清空所有数据库
   ```

### 问题 3: Redis 性能慢

**症状**: 操作延迟高，响应慢

**解决方案**:

1. 检查慢查询日志

   ```bash
   redis-cli SLOWLOG GET 10
   ```

1. 优化持久化配置

   ```conf
   # 减少快照频率
   save 900 1
   save 300 10

   # 使用 everysec 而不是 always
   appendfsync everysec
   ```

1. 增加连接池大小

   ```yaml
   Redis:
     MaxConnections: 100
   ```

### 问题 4: 数据丢失

**症状**: Redis 重启后数据丢失

**解决方案**:

1. 启用持久化

   ```conf
   # 启用 RDB
   save 900 1

   # 启用 AOF
   appendonly yes
   ```

1. 检查持久化文件

   ```bash
   # 检查 RDB 文件
   ls -lh /var/lib/redis/dump.rdb

   # 检查 AOF 文件
   ls -lh /var/lib/redis/appendonly.aof
   ```

1. 验证持久化配置

   ```bash
   redis-cli CONFIG GET save
   redis-cli CONFIG GET appendonly
   ```

______________________________________________________________________

## 安全建议

### 1. 设置密码

```conf
# redis.conf
requirepass your_strong_password_here
```

配置文件中使用密码：

```yaml
Redis:
  Password: "your_strong_password_here"
```

### 2. 绑定地址

```conf
# 只允许本地连接
bind 127.0.0.1

# 允许特定 IP
bind 127.0.0.1 192.168.1.100
```

### 3. 禁用危险命令

```conf
# 重命名危险命令
rename-command FLUSHDB ""
rename-command FLUSHALL ""
rename-command CONFIG ""
rename-command SHUTDOWN ""
```

### 4. 使用防火墙

```bash
# Linux (ufw)
sudo ufw deny 6379/tcp
sudo ufw allow from 127.0.0.1 to any port 6379

# Linux (iptables)
sudo iptables -A INPUT -p tcp --dport 6379 -s 127.0.0.1 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 6379 -j DROP
```

______________________________________________________________________

## 测试验证

### 运行测试脚本

```bash
# 激活虚拟环境
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux

# 运行 Redis 测试
python scripts/test_redis.py
```

### 预期输出

```
============================================================
🚀 homalos-webctp Redis 测试工具
============================================================

✅ 通过 - 连接测试
✅ 通过 - 基本操作测试
✅ 通过 - Pub/Sub 测试
✅ 通过 - 性能测试

============================================================
总计: 4/4 测试通过
============================================================

🎉 所有测试通过! Redis 配置正确。
```

### 启动服务测试

```bash
# 启动 MD 服务
python main.py --config=./config/config_md.yaml --app_type=md

# 启动 TD 服务
python main.py --config=./config/config_td.yaml --app_type=td
```

查看日志确认 Redis 连接：

```
[INFO] Redis 连接成功: localhost:6379 (DB: 0)
[INFO] Redis 命中率: 78.5%
```

______________________________________________________________________

## 参考资源

### 官方文档

- Redis 官网: https://redis.io/
- Redis 文档: https://redis.io/documentation
- Redis 命令参考: https://redis.io/commands

### Windows 版本

- Redis for Windows: https://github.com/microsoftarchive/redis
- Redis on WSL: https://docs.microsoft.com/en-us/windows/wsl/

### Python 客户端

- redis-py: https://github.com/redis/redis-py
- redis-py 文档: https://redis-py.readthedocs.io/

### 相关文档

- [监控指南](./monitoring_guide_CN.md) - 性能监控和告警
- [故障排查](./troubleshooting_CN.md) - 常见问题解决
- [迁移指南](./migration_guide_CN.md) - 版本升级指南

______________________________________________________________________

**最后更新**: 2025-12-15\
**维护者**: homalos-webctp 团队\
**版本**: v0.2.0
