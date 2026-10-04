# 各客户端配置片段

所有片段里的 `dbx` 只是服务器名（serverName）。**保持它稳定**，否则工具名会变、
权限规则也要跟着改。下面默认用原生绝对路径 `/Users/you/.dbx/bin/dbx-mcp` 举例；
npm 通道把 `command` / `args` 换成对应写法即可（见文末「三种 command 写法」）。

## 三种 command 写法

| 通道 | 配置 |
| --- | --- |
| 原生二进制（推荐） | `"command": "/Users/you/.dbx/bin/dbx-mcp"` |
| npm 全局安装 | `"command": "dbx-mcp-server"` |
| npx（免安装） | `"command": "npx"`, `"args": ["-y", "@dbx-app/mcp-server"]` |

原生路径必须是展开后的绝对路径，不要写 `~`，也不要只写 `dbx-mcp`：
GUI 客户端不一定继承 shell 的 PATH。

## Claude Code

项目内 `.mcp.json`：

```json
{
  "mcpServers": {
    "dbx": {
      "command": "/Users/you/.dbx/bin/dbx-mcp"
    }
  }
}
```

或直接用 CLI 添加：

```bash
claude mcp add dbx -- /Users/you/.dbx/bin/dbx-mcp
```

## Cursor

项目内 `.cursor/mcp.json`，或全局 `~/.cursor/mcp.json`：

```json
{
  "mcpServers": {
    "dbx": {
      "command": "/Users/you/.dbx/bin/dbx-mcp"
    }
  }
}
```

## Codex

`~/.codex/config.toml`：

```toml
[mcp_servers.dbx]
command = "/Users/you/.dbx/bin/dbx-mcp"
```

npx 写法：

```toml
[mcp_servers.dbx]
command = "npx"
args = ["-y", "@dbx-app/mcp-server"]
```

带环境变量（例如连 NexDB Web 后端）：

```toml
[mcp_servers.dbx]
command = "dbx-mcp-server"

[mcp_servers.dbx.env]
DBX_WEB_URL = "https://nexdb.example.com"
DBX_WEB_PASSWORD = "your-web-login-password"
```

## Windsurf

`~/.codeium/windsurf/mcp_config.json`：

```json
{
  "mcpServers": {
    "dbx": {
      "command": "/Users/you/.dbx/bin/dbx-mcp"
    }
  }
}
```

## VS Code + Copilot

项目内 `.vscode/mcp.json`（注意顶层键是 `servers`，不是 `mcpServers`）：

```json
{
  "servers": {
    "dbx": {
      "type": "stdio",
      "command": "/Users/you/.dbx/bin/dbx-mcp"
    }
  }
}
```

## DeepSeek Harness

DSH 通过 Cordis 插件条目加载 MCP Server，不读 `mcpServers` JSON。为某个 profile
把下面的条目合并进 `$DSH_HOME/profiles/<profile>/cordis.patch.yml`；未设置
`DSH_HOME` 时默认 `~/.dsh`。保留最外层的 `- insert:`，不要覆盖文件里已有的 patch 条目。

```yaml
- insert:
    - id: mcp-dbx
      name: '@deepseek-ai/dsh-mcp-client'
      config:
        serverName: dbx
        transport: stdio
        command: dbx-mcp-server
```

DSH 进程的 PATH 必须能找到 `dbx-mcp-server`；必要时改成可执行文件的绝对路径。
用 `dsh web --dump-config` 检查合并结果，再重启 DSH 或等热加载。模型侧工具名是
`mcp__dbx__<tool>`。

## 通用 stdio 客户端

任何接受「命令 + 参数」的 MCP 客户端都用这套：

```json
{
  "mcpServers": {
    "dbx": {
      "command": "/Users/you/.dbx/bin/dbx-mcp",
      "env": {
        "DBX_DATA_DIR": "/absolute/path/to/data"
      }
    }
  }
}
```

`DBX_DATA_DIR` 只在需要覆盖 NexDB 数据目录时写（便携版、非默认安装位置）。
普通桌面安装不需要设置。

## 通用 Streamable HTTP 客户端

字段名各客户端略有差异，核心是 URL 加 Bearer Token：

```json
{
  "type": "http",
  "url": "http://127.0.0.1:5225/mcp",
  "headers": {
    "Authorization": "Bearer <NexDB 设置页展示的 Token>"
  }
}
```

地址、路径、Token 都以 **NexDB Settings → MCP → HTTP 服务** 页面为准；
换端口或路径后要重新复制。桌面 UI 工具（`dbx_open_table`、
`dbx_execute_and_show`）只在这条通道下、且 NexDB 桌面端运行时可用。

## 验证是否连上

连上后让助手执行一句自然语言，例如「列出我的 NexDB 连接」，它会调用
`dbx_list_connections`。返回空列表说明连接没暴露给 MCP，去
**NexDB Settings → MCP** 检查连接 allowlist，而不是改客户端配置。
