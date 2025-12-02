# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- 创建 `BaseClient` 抽象基类，统一客户端管理逻辑
- 添加重连控制机制，防止配置错误导致的疯狂重连
- 使用 UUID 生成随机任务名称，提升安全性和可追踪性
- 添加开发文档 `docs/development.md`
- 添加变更日志 `CHANGELOG.md`

### Changed
- 重构 `TdClient` 和 `MdClient` 继承 `BaseClient`，减少代码重复约50%
- 统一 `MdClient` 和 `TdClient` 的错误处理逻辑
- 改进异常日志记录，使用 `logging.exception()` 替代 `logging.info()`
- 更新 README.md 安装说明，从 requirements.txt 改为 pyproject.toml
- 规范化 .gitignore，移除重复项

### Fixed
- 修复所有拼写错误：
  - `resposne` → `response`
  - `secenario` → `scenario`
  - `corroutine` → `coroutine`
  - `stpped` → `stopped`
  - `courrtine` → `coroutine`
  - `boundray` → `boundary`
- 统一类型注解：所有 `any` 改为 `Any`
- 修复安全问题：`yaml.load()` 改为 `yaml.safe_load()`
- 移除未使用的导入：`WebSocketDisconnect` in `apps/td_app.py`

### Security
- 使用 `yaml.safe_load()` 替代 `yaml.load()`，消除安全漏洞

## [0.1.0] - Initial Release

### Added
- 基于 FastAPI 的 WebSocket CTP 服务
- 行情服务 (md_app)
- 交易服务 (td_app)
- 基本的 CTP API 封装
- 配置文件支持
- 协议文档
