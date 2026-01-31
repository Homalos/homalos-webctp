"""
Project: homalos-webctp
File: test_redis.py
Date: 2025-12-15
Author: Kiro AI Assistant
Description: Redis 连接和功能测试脚本
"""

import sys
import time
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    import redis
    from redis.exceptions import ConnectionError, TimeoutError
except ImportError:
    print("❌ 错误: redis 模块未安装")
    print("请运行: uv sync")
    sys.exit(1)


def test_redis_connection(host="localhost", port=6379, password="", db=0):
    """测试 Redis 连接"""
    print(f"\n{'='*60}")
    print("Redis 连接测试")
    print(f"{'='*60}")

    try:
        # 创建 Redis 客户端
        client = redis.Redis(
            host=host,
            port=port,
            password=password if password else None,
            db=db,
            socket_timeout=5.0,
            socket_connect_timeout=5.0,
            decode_responses=True,
        )

        # 测试连接
        print(f"\n📡 连接到 Redis: {host}:{port} (DB: {db})")
        response = client.ping()
        if response:
            print("✅ Redis 连接成功!")
        else:
            print("❌ Redis 连接失败")
            return False

        # 获取 Redis 信息
        info = client.info()
        print("\n📊 Redis 服务器信息:")
        print(f"  - 版本: {info.get('redis_version', 'N/A')}")
        print(f"  - 运行模式: {info.get('redis_mode', 'N/A')}")
        print(f"  - 操作系统: {info.get('os', 'N/A')}")
        print(f"  - 进程 ID: {info.get('process_id', 'N/A')}")
        print(f"  - 运行时间: {info.get('uptime_in_seconds', 0)} 秒")

        # 内存信息
        used_memory = info.get("used_memory_human", "N/A")
        max_memory = info.get("maxmemory_human", "N/A")
        print("\n💾 内存使用:")
        print(f"  - 已使用: {used_memory}")
        print(f"  - 最大限制: {max_memory if max_memory != '0B' else '无限制'}")

        # 持久化信息
        print("\n💿 持久化配置:")
        print(
            f"  - RDB 快照: {'启用' if info.get('rdb_bgsave_in_progress', 0) == 0 else '进行中'}"
        )
        print(f"  - 最后保存: {info.get('rdb_last_save_time', 'N/A')}")
        print(f"  - AOF 日志: {'启用' if info.get('aof_enabled', 0) == 1 else '禁用'}")

        return True

    except ConnectionError as e:
        print(f"❌ 连接错误: {e}")
        print("\n💡 请检查:")
        print("  1. Redis 服务是否正在运行")
        print("  2. 连接参数是否正确")
        print("  3. 防火墙是否允许连接")
        return False
    except TimeoutError as e:
        print(f"❌ 连接超时: {e}")
        return False
    except Exception as e:
        print(f"❌ 未知错误: {e}")
        return False


def test_redis_operations(host="localhost", port=6379, password="", db=0):
    """测试 Redis 基本操作"""
    print(f"\n{'='*60}")
    print("Redis 基本操作测试")
    print(f"{'='*60}")

    try:
        client = redis.Redis(
            host=host,
            port=port,
            password=password if password else None,
            db=db,
            socket_timeout=5.0,
            decode_responses=True,
        )

        test_key = "webctp:test:key"
        test_value = "test_value_123"

        # 测试 SET
        print("\n1️⃣ 测试 SET 操作")
        client.set(test_key, test_value, ex=60)
        print(f"✅ SET {test_key} = {test_value}")

        # 测试 GET
        print("\n2️⃣ 测试 GET 操作")
        result = client.get(test_key)
        if result == test_value:
            print(f"✅ GET {test_key} = {result}")
        else:
            print(f"❌ GET 失败: 期望 {test_value}, 得到 {result}")
            return False

        # 测试 HASH
        print("\n3️⃣ 测试 HASH 操作")
        hash_key = "webctp:test:hash"
        # Redis 3.x 兼容语法
        client.hset(hash_key, "field1", "value1")
        client.hset(hash_key, "field2", "value2")
        client.hset(hash_key, "field3", "value3")
        print(f"✅ HSET {hash_key}")

        hash_data = client.hgetall(hash_key)
        print(f"✅ HGETALL {hash_key}: {hash_data}")

        # 测试 DELETE
        print("\n4️⃣ 测试 DELETE 操作")
        client.delete(test_key, hash_key)
        print(f"✅ DELETE {test_key}, {hash_key}")

        # 验证删除
        if client.get(test_key) is None:
            print("✅ 验证删除成功")
        else:
            print("❌ 删除失败")
            return False

        print("\n✅ 所有基本操作测试通过!")
        return True

    except Exception as e:
        print(f"❌ 操作测试失败: {e}")
        return False


def test_redis_pubsub(host="localhost", port=6379, password="", db=0):
    """测试 Redis Pub/Sub"""
    print(f"\n{'='*60}")
    print("Redis Pub/Sub 测试")
    print(f"{'='*60}")

    try:
        # 创建发布者和订阅者
        publisher = redis.Redis(
            host=host,
            port=port,
            password=password if password else None,
            db=db,
            decode_responses=True,
        )

        subscriber = redis.Redis(
            host=host,
            port=port,
            password=password if password else None,
            db=db,
            decode_responses=True,
        )

        channel = "webctp:test:channel"
        test_message = "test_message_123"

        # 订阅频道
        print(f"\n📡 订阅频道: {channel}")
        pubsub = subscriber.pubsub()
        pubsub.subscribe(channel)

        # 等待订阅确认
        time.sleep(0.1)

        # 发布消息
        print(f"📤 发布消息: {test_message}")
        publisher.publish(channel, test_message)

        # 接收消息
        print("等待接收消息...")
        received = False
        for message in pubsub.listen():
            if message["type"] == "message" and message["data"] == test_message:
                print(f"接收到消息: {message['data']}")
                received = True
                break

        # 取消订阅
        pubsub.unsubscribe(channel)
        pubsub.close()

        if received:
            print("\n✅ Pub/Sub 测试通过!")
            return True
        print("\n❌ Pub/Sub 测试失败: 未接收到消息")
        return False

    except Exception as e:
        print(f"❌ Pub/Sub 测试失败: {e}")
        return False


def test_redis_performance(host="localhost", port=6379, password="", db=0):
    """测试 Redis 性能"""
    print(f"\n{'='*60}")
    print("Redis 性能测试")
    print(f"{'='*60}")

    try:
        client = redis.Redis(
            host=host,
            port=port,
            password=password if password else None,
            db=db,
            socket_timeout=5.0,
            decode_responses=True,
        )

        # 测试 SET 性能
        print("\n⚡ 测试 SET 性能 (1000 次操作)")
        start_time = time.time()
        for i in range(1000):
            client.set(f"webctp:perf:test:{i}", f"value_{i}")
        set_time = time.time() - start_time
        set_ops = 1000 / set_time
        print(f"✅ SET: {set_time:.3f} 秒, {set_ops:.0f} ops/s")

        # 测试 GET 性能
        print("\n⚡ 测试 GET 性能 (1000 次操作)")
        start_time = time.time()
        for i in range(1000):
            client.get(f"webctp:perf:test:{i}")
        get_time = time.time() - start_time
        get_ops = 1000 / get_time
        print(f"✅ GET: {get_time:.3f} 秒, {get_ops:.0f} ops/s")

        # 清理测试数据
        print("\n🧹 清理测试数据...")
        for i in range(1000):
            client.delete(f"webctp:perf:test:{i}")
        print("✅ 清理完成")

        print("\n✅ 性能测试完成!")
        print("\n📊 性能摘要:")
        print(f"  - SET: {set_ops:.0f} ops/s")
        print(f"  - GET: {get_ops:.0f} ops/s")

        return True

    except Exception as e:
        print(f"❌ 性能测试失败: {e}")
        return False


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("🚀 homalos-webctp Redis 测试工具")
    print("=" * 60)

    # 从配置文件读取 Redis 配置
    host = "localhost"
    port = 6379
    password = ""
    db = 0

    # 运行所有测试
    tests = [
        ("连接测试", lambda: test_redis_connection(host, port, password, db)),
        ("基本操作测试", lambda: test_redis_operations(host, port, password, db)),
        ("Pub/Sub 测试", lambda: test_redis_pubsub(host, port, password, db)),
        ("性能测试", lambda: test_redis_performance(host, port, password, db)),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ {test_name} 异常: {e}")
            results.append((test_name, False))

    # 输出测试结果摘要
    print(f"\n{'='*60}")
    print("测试结果摘要")
    print(f"{'='*60}\n")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {test_name}")

    print(f"\n{'='*60}")
    print(f"总计: {passed}/{total} 测试通过")
    print(f"{'='*60}\n")

    if passed == total:
        print("🎉 所有测试通过! Redis 配置正确。")
        return 0
    print("⚠️ 部分测试失败，请检查 Redis 配置。")
    return 1


if __name__ == "__main__":
    sys.exit(main())
