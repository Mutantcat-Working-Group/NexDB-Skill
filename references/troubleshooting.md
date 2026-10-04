# 排错手册

先确认两件事，再往下查：**走的是哪条通道**（原生 / npm / 桌面 HTTP / Web），
以及**错误发生在客户端还是 NexDB 侧**。绝大多数「连不上」是通道前置条件没满足，
不是客户端配置写错。

## 连不上 / 没有工具

| 现象 | 处理 |
| --- | --- |
| 客户端里看不到任何 `dbx_*` 工具 | 服务器名保持 `dbx` 不变；检查客户端是否加载了配置（多数客户端要重启或重新载入 MCP） |
| 工具列表是空的 | 连接没暴露给 MCP。去 **NexDB Settings → MCP** 检查连接 allowlist 和工具 allowlist，不是改客户端配置 |
| 之前能用的工具现在被拒绝 | 该工具已不在 allowlist，或当前策略不允许。改完刷新客户端工具列表；服务端会拒绝缓存的旧调用 |
| `ERR_CONNECTION_REFUSED`（桌面 HTTP） | **NexDB Settings → MCP → HTTP 服务** 确认服务已开启并点 **保存并应用**；用页面展示的地址、路径和当前 Token；默认 `127.0.0.1` 只接受本机连接 |
| 桌面提示 HTTP 地址已被占用 | 有其他进程监听了该地址端口。在 **HTTP 服务** 里换一个未被占用的端口再保存；不要让两个 NexDB 实例用同一端点 |
| GUI 客户端报 command not found | 配置里改填展开后的绝对路径（`/Users/you/.dbx/bin/dbx-mcp`），不要写 `~` 或裸命令 |

## 找不到 `dbx.db`

把 `DBX_DATA_DIR` 设成**包含 `dbx.db` 的目录**，不是数据库文件本身。
Windows 便携版通常是 NexDB 可执行文件同级的 `data` 目录。

默认位置：

| 平台 | 路径 |
| --- | --- |
| macOS | `~/Library/Application Support/org.mutantcat.app/dbx.db` |
| Linux | `~/.local/share/org.mutantcat.app/dbx.db` |
| Windows | `%APPDATA%\org.mutantcat.app\dbx.db` |

桌面端正常安装时不需要设置 `DBX_DATA_DIR`。

## 权限与范围类错误

| 错误 | 含义与处理 |
| --- | --- |
| `DATABASE_OUT_OF_SCOPE` | 连接已暴露给 MCP，但请求的库不在它的数据库范围内。在 **NexDB Settings → MCP** 里加上精确库名，或把该连接设为全部数据库。指定范围时先调 `dbx_list_databases` 拿真实名称 |
| 跨库 SQL 被拒 | 配置了单库执行权限时，跨库 SQL 和 MongoDB 聚合写入会被拒绝，避免绕过库级限制 |
| 写入被拒（只读） | 全局或连接的执行权限是只读。在 **NexDB Settings → MCP** 调整，而不是加环境变量 |
| 高风险更新 / 删除被拒 | `WHERE TRUE`、`WHERE 1 = 1`、`_id: {$exists: true}`、互补谓词、不透明 MongoDB 过滤器都按高风险处理；普通模式需要可验证的有效过滤条件 |
| `SALESFORCE_DML_DISABLED` | 该连接的 **允许 DML** 开关没开（默认关闭），或执行模式是只读 |
| `CONFIRM_TOKEN_INVALID` | Salesforce 写入令牌已用、已过期（5 分钟）或写入内容变了。重新 `prepare_write` |
| `TRANSACTION_UNSUPPORTED` | 显式事务只支持本地原生 MySQL；Web / `DBX_WEB_URL`、外部驱动和兼容引擎不支持 |

**不要在客户端配置里放权限开关。** `DBX_MCP_ALLOW_WRITES` /
`DBX_MCP_ALLOW_DANGEROUS_SQL` 仅用于升级兼容，不能放宽 NexDB 中央策略；
`DBX_MCP_SCOPE_*` 只能进一步收窄范围。权限的唯一权威来源是
**NexDB Settings → MCP**。

## 「NexDB 未运行」

只有 `dbx_open_table` 和 `dbx_execute_and_show` 需要 NexDB 桌面端运行。
本地查询工具在 NexDB 关闭时也能执行。Web / Docker 模式下这两个工具不可用。

如果其他工具也报类似错误，多半是该连接需要 bridge 或 Agent 运行时，
而不是整个 MCP 不可用。

## npm 相关

| 现象 | 处理 |
| --- | --- |
| 提示缺少平台包 | 不要用 `--no-optional`，重装：`npm uninstall -g @dbx-app/mcp-server && npm install -g @dbx-app/mcp-server@latest` |
| 不确定平台 | `node -p 'process.platform + "-" + process.arch'` |
| Alpine / musl 不支持 | 已发布的 Linux 包目标是 glibc；Alpine 默认 musl，暂不支持。改用原生二进制或 glibc 发行版 |
| `better-sqlite3` 或 Node ABI 错误 | MCP 不依赖 `better-sqlite3`。先升级 `@dbx-app/mcp-server`；若错误来自 `@dbx-app/cli`，那是另一个包，按它自己的安装要求处理 |
| Node 版本过低 | 需要 Node.js 18.18.0 或更高 |

## macOS 钥匙串

独立 macOS MCP 在后台运行时不弹钥匙串对话框。已有加密密钥被锁定或拒绝访问时，
启动会保留 `KEYRING_ACCESS_FAILED`（可能包含在 `SECRET_KEY_UNAVAILABLE` 中），
而不是反复要求输入密码。

先解锁登录钥匙串；对旧版绑定构建哈希的授权，在终端对 **MCP 客户端实际使用的
同一个官方程序** 执行一次：

```bash
"$HOME/.dbx/bin/dbx-mcp" --authorize-keychain
```

Homebrew 或 npm 安装要换成对应二进制路径。该命令校验官方签名和稳定
designated requirement 后读取已有 NexDB 钥匙串条目，不会打开数据库、
不会启动传输、不会创建或导出密钥。macOS 首次迁移可能要求确认一次，
对已验证的 NexDB 程序选 **始终允许**，然后重启 MCP 客户端。

**不要**把 `--authorize-keychain` 加进 MCP 客户端的启动参数，它是执行后
立即退出的一次性恢复命令。密钥真的丢了要回到桌面端的数据安全设置处理。
Windows 和 Linux 不用这个命令，恢复同一系统用户的凭据库访问即可。

## Docker / 反向代理

- 用公网访问地址，包含映射后的端口和 `DBX_PUBLIC_BASE_PATH` 前缀。
- `DBX_WEB_MCP_ALLOWED_HOSTS` 必须与实际 `Host` authority 精确一致
  （例如容器映射 `4225:4224` 时是 `localhost:4225`）。
- 浏览器客户端还要在 `DBX_WEB_MCP_ALLOWED_ORIGINS` 里配置精确 Origin；
  原生客户端通常不发送 `Origin`。
- 无 Web 登录密码时，页面管理的 MCP 不会生效；演示部署禁用 MCP。
- 多实例部署应使用一致的部署 Secret 与白名单，而不是页面管理模式。

## 驱动与 Agent

| 现象 | 处理 |
| --- | --- |
| DuckDB 连接无法启动 | 在 NexDB Driver Manager 安装或更新 DuckDB 驱动；本地 MCP、Web 和 Docker 都通过独立驱动运行 DuckDB，不内置引擎 |
| Agent / JDBC 数据库无法启动 | 在 Driver Manager 安装或更新匹配的 Agent、JDBC 驱动和 JRE；厂商专有驱动不随 MCP 原生包发布 |
| 厂商专用 / 集群连接行为异常 | 这类连接是否可用取决于本机 NexDB 组件；不要假设原生 MCP 包内置全部运行时 |

## 排查顺序（照抄）

1. `dbx_list_connections` 能返回吗？不能 → 通道问题（本文第一节）。
2. 能返回但列表为空 → 连接 allowlist 问题（**NexDB Settings → MCP**）。
3. 能列连接但请求某个库失败 → 数据库范围问题（`DATABASE_OUT_OF_SCOPE`）。
4. 查询能跑但写入被拒 → 执行权限模式问题，不是客户端问题。
5. 只有桌面 UI 工具失败 → NexDB 桌面端没运行，或当前是 Web 模式。

需要看 SQL 时临时设 `DBX_MCP_DEBUG_SQL=1`，查完立刻关掉：
SQL 文本默认不进错误消息，也不记日志。
