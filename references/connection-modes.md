# 接入通道与运行模式

先判断「MCP 进程在哪里跑、连的是哪份 NexDB 数据」，再挑传输方式。
传输（stdio / Streamable HTTP）和运行模式（本地 / Web）是两个正交的维度。

```text
传输        stdio（默认）          本地进程，客户端负责拉起
            Streamable HTTP        常驻端口 + Bearer Token

运行模式    本地（默认）            读本机 NexDB 连接存储
            Web / Docker           DBX_WEB_URL 指向部署好的后端
```

## 1. 原生二进制（推荐）

无需 Node.js。macOS / Linux：

```bash
curl -fsSL https://dbxio.com/install-mcp | sh
```

Windows PowerShell：

```powershell
irm https://dbxio.com/install-mcp.ps1 | iex
```

脚本会校验下载内容，把 `dbx-mcp` 装到 `~/.dbx/bin`，并打印 Claude Code、
Cursor、Codex 和通用客户端配置。重跑同一命令即升级；版本相同时提示
`already up to date`。下载源依次为 npmjs、npmmirror、GitHub Releases，
断网时失败但不会替换已有二进制。

macOS 上，Shell 安装器会在替换前验证官方 Developer ID 签名与稳定的
`com.dbx.app.mcp` designated requirement；未签名、临时签名或身份不符的包会被拒绝，
已安装的程序保持不变。Homebrew 与 npm 走各自的安装流程，不做这一步。

macOS / Linux 的 Homebrew 通道：

```bash
brew install t8y2/tap/dbx-mcp
brew upgrade t8y2/tap/dbx-mcp
```

Homebrew 只装 MCP 服务器，不装独立的 `dbx` CLI。配置里用
`echo "$(brew --prefix)/bin/dbx-mcp"` 给出的绝对路径。

**GUI 客户端要点：** 填展开后的绝对路径，不要填 `~` 或裸命令 `dbx-mcp`。

## 2. npm / npx（兼容通道）

```bash
npm install -g @dbx-app/mcp-server
```

- 全局安装后 `command` 可用 `dbx-mcp-server`。
- 免安装用 `"command": "npx", "args": ["-y", "@dbx-app/mcp-server"]`。
- 平台二进制走 npm optional dependencies，**不要加 `--no-optional`**。
- 需要 Node.js 18.18.0 或更高版本。
- npm 包是一个小 Node 启动器，实际执行对应平台的 Rust `dbx-mcp` 二进制。

平台包对应关系：

| 平台 | npm 平台包 | GitHub 资产 |
| --- | --- | --- |
| macOS Apple Silicon | `@dbx-app/mcp-darwin-arm64` | `dbx-mcp-darwin-arm64.tar.gz` |
| macOS Intel | `@dbx-app/mcp-darwin-x64` | `dbx-mcp-darwin-x64.tar.gz` |
| Linux glibc ARM64 | `@dbx-app/mcp-linux-arm64-gnu` | `dbx-mcp-linux-arm64-gnu.tar.gz` |
| Linux glibc x64 | `@dbx-app/mcp-linux-x64-gnu` | `dbx-mcp-linux-x64-gnu.tar.gz` |
| Windows ARM64 | `@dbx-app/mcp-win32-arm64` | `dbx-mcp-win32-arm64.zip` |
| Windows x64 | `@dbx-app/mcp-win32-x64` | `dbx-mcp-win32-x64.zip` |

离线或内网环境可直接下 GitHub Releases 的资产，校验 `SHA256SUMS` 后解压，
把绝对路径填进客户端。直接跑原生二进制不需要 Node.js。

## 3. NexDB 桌面 Streamable HTTP

由 NexDB 桌面进程托管，**默认关闭**，开启后默认监听 `127.0.0.1:5225/mcp`。

1. **NexDB Settings → MCP → HTTP 服务**，打开 **Streamable HTTP 服务**。
2. 点 **保存并应用**（保存配置并按开关启动 / 重启 / 停止服务）。
3. 复制页面上的地址和 Bearer Token 到客户端。

```json
{
  "type": "http",
  "url": "http://127.0.0.1:5225/mcp",
  "headers": {
    "Authorization": "Bearer <NexDB 设置页展示的 Token>"
  }
}
```

默认回环地址只接受同一台电脑上的连接。绑定非回环地址需要同时开启
**允许远程访问**、填精确 `Host`，浏览器客户端还要填精确 `Origin`
（带非默认端口时写成 `host:port`）。轮换 Token 立刻让旧凭证失效。

## 4. NexDB Web / Docker（`DBX_WEB_URL`）

设置 `DBX_WEB_URL` 后，MCP 使用部署好的 NexDB Web 后端，而不是本机连接存储；
Web 登录启用密码时再加 `DBX_WEB_PASSWORD`。这条通道仍是 stdio，适合只支持
stdio 的客户端。

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

代理与 TLS 相关变量：

| 变量 | 用途 |
| --- | --- |
| `HTTP_PROXY` / `HTTPS_PROXY` / `ALL_PROXY` | 标准系统代理；空值表示直连。支持 HTTP/HTTPS/SOCKS5，认证用 `http://user:pass@host:port` |
| `NO_PROXY` | 逗号分隔的绕过主机列表，例如 `localhost,127.0.0.1,.internal.example` |
| `DBX_WEB_HEADERS` | 附加请求头的 JSON 对象，例如 `{"Authorization":"Bearer token"}`，对每次请求生效 |
| `DBX_WEB_INSECURE_SKIP_VERIFY` | `1` / `true` 时跳过 TLS 证书验证（自签名后端；默认验证） |
| `DBX_WEB_CA_CERT` | 信任的 PEM/DER CA 文件 |

Web / Docker 模式下桌面 UI 工具（`dbx_open_table`、`dbx_execute_and_show`）不可用。

## 5. NexDB Web 原生 Streamable HTTP

NexDB Web 可复用现有监听器和 `/mcp` 路径托管 MCP，Docker 与反向代理部署
不必额外暴露第二个端口。容器映射为 `4225:4224` 时端点是 `http://localhost:4225/mcp`：

```yaml
environment:
  DBX_WEB_MCP_TOKEN: replace-with-a-long-random-secret
  DBX_WEB_MCP_ALLOWED_HOSTS: localhost:4225
ports:
  - "4225:4224"
```

客户端发送 `Authorization: Bearer <DBX_WEB_MCP_TOKEN>`；浏览器客户端还需要在
`DBX_WEB_MCP_ALLOWED_ORIGINS` 里填精确 Origin。反向代理加了路径前缀时设置
`DBX_PUBLIC_BASE_PATH=/dbx`，端点变成 `/dbx/mcp`。生产环境优先用
`DBX_WEB_MCP_TOKEN_FILE` 或部署平台的 Secret 管理，不要把真实 Token 提交进 Compose。

## 6. 本地连接存储位置

| 平台 | 默认路径 |
| --- | --- |
| macOS | `~/Library/Application Support/org.mutantcat.app/dbx.db` |
| Linux | `~/.local/share/org.mutantcat.app/dbx.db` |
| Windows | `%APPDATA%\org.mutantcat.app\dbx.db` |

`DBX_DATA_DIR` 指向**包含 `dbx.db` 的目录**，不是数据库文件本身。
Windows 便携版通常是 NexDB 可执行文件同级的 `data` 目录。

## 7. 哪些连接能直接跑

原生 SQL（PostgreSQL、MySQL、SQLite 及兼容引擎）、独立 Redis、MongoDB 等
可以由 MCP 直接执行。SSH、集群、厂商专用、外部驱动和 Agent/JDBC 连接是否可用，
取决于连接配置和本机已安装的 NexDB 组件——不要从「NexDB 支持该数据库」
推断 MCP 原生包内置了全部运行时。

- DuckDB 需要先在 NexDB Driver Manager 装独立 DuckDB 驱动（Docker 会存到 `/app/data/agents`）。
- Oracle、金仓 KingbaseES、虚谷等原生 Agent 不需要 JRE。
- 达梦、DB2、Hive、Trino、Snowflake、SAP HANA 等 JDBC Agent 需要匹配的
  Agent、JDBC 驱动和 JRE。

## 8. 有状态会话与超时

`DBX_SESSION_IDLE_TTL_SECS` 控制有状态会话空闲回收，默认 `1800` 秒。
非法值、零、负数或无法表示的时长都回退默认值；修改后要重启 MCP 宿主进程。
嵌入式 NexDB Web MCP 在 Web 服务端设置，独立启动器在启动器环境里设置。
