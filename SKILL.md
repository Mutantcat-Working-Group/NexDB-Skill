---
name: nexdb-mcp
description: Use when connecting an AI coding assistant (Claude Code, Cursor, Codex, Windsurf, VS Code + Copilot, DeepSeek Harness, or any MCP client) to NexDB, when installing or configuring the NexDB MCP server (`dbx-mcp` native binary or the `@dbx-app/mcp-server` npm package), when choosing between native, npm/npx, Streamable HTTP, or NexDB Web/Docker transports, or when diagnosing MCP failures such as connection refused, a missing `dbx.db`, `DATABASE_OUT_OF_SCOPE`, hidden desktop-only tools, or npm platform-package errors.
license: Apache-2.0
---

# 用 MCP 把 AI 助手接到 NexDB

NexDB（异猫工作群出品）内置一个 MCP 服务端，把已经保存的数据库连接暴露给
AI 编程助手。助手因此可以列连接、看表结构、跑 SQL、用有状态会话，还能让
NexDB 桌面端把结果打开给你看。这个技能负责把「装、配、连、排错」讲清楚，
并覆盖各家客户端写法。

品牌名统一是 **NexDB**；包名 `@dbx-app/mcp-server`、可执行文件 `dbx-mcp` /
`dbx-mcp-server`、环境变量 `DBX_*` 是历史内部标识，保持不变。

## 什么时候用

- 要让 Claude Code、Cursor、Codex、Windsurf、VS Code + Copilot、DeepSeek Harness
  或任意 MCP 客户端访问 NexDB 里已配置的数据库。
- 要在原生二进制、npm/npx、NexDB 桌面端 Streamable HTTP、NexDB Web/Docker 之间选通道。
- 客户端连不上、找不到 `dbx.db`、报 `DATABASE_OUT_OF_SCOPE`、工具被拒绝、或
  `dbx_open_table` 说 NexDB 没运行时，按本技能排错。

不适用：改 NexDB 界面样式、配 AI Provider 密钥、写数据库驱动。这些是 NexDB 本体的事。

## 三条通道，先选一条

| 场景 | 通道 | 启动方式 |
| --- | --- | --- |
| 本机桌面、想要最快最稳 | 原生二进制（推荐） | `dbx-mcp` 绝对路径，stdio |
| 已有 Node 环境、图省事 | npm / npx | `npx -y @dbx-app/mcp-server`，stdio |
| 只想开一个本机 HTTP 端口 | NexDB 桌面 Streamable HTTP | `http://127.0.0.1:5225/mcp` + Bearer Token |
| 连远程 / 容器里的 NexDB | NexDB Web / Docker | `DBX_WEB_URL` 走 stdio，或 Web 自带 `/mcp` |

细节和全部环境变量见 [references/connection-modes.md](references/connection-modes.md)。

## 原生安装（推荐，无需 Node.js）

macOS / Linux：

```bash
curl -fsSL https://dbxio.com/install-mcp | sh
```

Windows PowerShell：

```powershell
irm https://dbxio.com/install-mcp.ps1 | iex
```

安装脚本会校验下载内容，把 `dbx-mcp` 装到 `~/.dbx/bin`，并打印 Claude Code、
Cursor、Codex 和通用客户端配置。重跑同一条命令即可升级。Homebrew 也可：

```bash
brew install t8y2/tap/dbx-mcp
brew upgrade t8y2/tap/dbx-mcp
```

**关键一条：GUI 客户端不一定继承 shell 的 PATH。** 配置里请填脚本输出或
`echo "$(brew --prefix)/bin/dbx-mcp"` 给出的**展开后绝对路径**，不要写 `~`，
也不要只写 `dbx-mcp`。

## npm / npx（兼容通道）

```bash
npm install -g @dbx-app/mcp-server   # 全局装，之后 command 用 dbx-mcp-server
```

通用 stdio 配置：

```json
{
  "mcpServers": {
    "dbx": {
      "command": "npx",
      "args": ["-y", "@dbx-app/mcp-server"]
    }
  }
}
```

不要加 `--no-optional`：平台二进制走 npm optional dependencies，禁掉就装不上。
连接范围和执行权限统一在 **NexDB Settings → MCP** 里管，常规配置不要写权限环境变量。

## NexDB 桌面 Streamable HTTP

在 **NexDB Settings → MCP → HTTP 服务** 打开 **Streamable HTTP 服务**，点
**保存并应用**，然后复制页面上的地址和 Bearer Token。默认只监听本机回环：

```json
{
  "type": "http",
  "url": "http://127.0.0.1:5225/mcp",
  "headers": {
    "Authorization": "Bearer <页面展示的 Token>"
  }
}
```

除非确实要让别的设备访问，否则保持回环。要绑局域网地址，必须同时开启
**允许远程访问** 并填写精确的 `Host`（浏览器客户端还要精确 `Origin`）。
轮换 Token 会立刻让旧凭证失效。

## NexDB Web / Docker

给 stdio 进程设置 `DBX_WEB_URL`，就改用部署好的 NexDB Web 后端，而不是读本机
连接；Web 登录有密码时再加 `DBX_WEB_PASSWORD`：

```json
{
  "mcpServers": {
    "dbx": {
      "command": "dbx-mcp-server",
      "env": {
        "DBX_WEB_URL": "https://nexdb.example.com",
        "DBX_WEB_PASSWORD": "your-web-login-password"
      }
    }
  }
}
```

Web / Docker 模式下桌面 UI 工具会被隐藏。Web 也可以直接托管 `/mcp`，复用现有
监听器，适合只支持 Streamable HTTP 的客户端。

## 各客户端怎么写

Claude Code、Cursor、Codex（TOML）、Windsurf、VS Code + Copilot、DeepSeek Harness
和通用 stdio/HTTP 客户端的完整片段见 [references/clients.md](references/clients.md)。

## 权限与安全

**NexDB Settings → MCP** 保存唯一权威策略，每个请求都重新读取：

| 权限模式 | 允许的操作 |
| --- | --- |
| 只读 | 查询和元数据读取 |
| 数据读写 | 普通插入、带有效过滤条件的更新/删除、范围明确的 MongoDB 修改、普通 Redis 写入 |
| 完全访问 | 额外允许大范围更新/删除、DDL、`TRUNCATE`、MongoDB 破坏性操作、Redis `FLUSH*` |

同一页面还能限定可见连接、每连接的数据库范围和工具 allowlist。`WHERE TRUE`、
`WHERE 1 = 1`、`_id: {$exists: true}` 这类不透明过滤条件仍按高风险处理。

**不要在客户端配置里放权限开关。** `DBX_MCP_ALLOW_WRITES` /
`DBX_MCP_ALLOW_DANGEROUS_SQL` 只用于升级兼容，不能放宽中央策略；旧的
`DBX_MCP_SCOPE_*` 变量只能进一步收窄范围。

写操作前先确认目标连接和库；删除、DDL、批量改这类不可逆操作先向使用者确认。
`dbx_execute_query` 默认只返回 100 行（`max_rows` 最多 1000），别拿它当全量导出。

## 工具地图

`dbx_list_connections` / `dbx_list_databases` / `dbx_list_tables` / `dbx_describe_table` /
`dbx_get_schema_context` 负责发现；`dbx_execute_query` / `dbx_execute_batch` 负责执行；
`dbx_open_session` + `dbx_begin_transaction` / `dbx_commit_transaction` /
`dbx_rollback_transaction` / `dbx_close_session` 负责有状态会话与事务；
`dbx_open_table` / `dbx_execute_and_show` 把结果送回 NexDB 桌面端。

完整清单、参数要点和什么时候该开会话见 [references/tools.md](references/tools.md)。

## 出错怎么办

连不上、找不到 `dbx.db`、`DATABASE_OUT_OF_SCOPE`、工具被拒、npm 平台包缺失、
Docker/反代 Host 不匹配、DuckDB 或 Agent/JDBC 驱动没装——按现象查
[references/troubleshooting.md](references/troubleshooting.md)。

排错第一步永远是：确认走的是哪条通道，再看那条通道的前置条件。
本地查询不需要 NexDB 开着，只有 `dbx_open_table` 和 `dbx_execute_and_show` 需要。
