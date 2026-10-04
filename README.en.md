<div align=center>
<img src="assets/icon.png" style="width:100px;" width="100"/>
<h2>NexDB-Skill</h2>
<p>Connect AI coding assistants to NexDB over MCP</p>
</div>

English | [中文](README.md)

### 1. What This Is

- A skill for AI agents that turns [NexDB](https://github.com/Mutantcat-Working-Group/NexDB)'s
  MCP surface — install, configure, connect, troubleshoot — into one searchable reference.
- **Compatibility first**: native binary, npm / npx, NexDB Desktop Streamable HTTP, and
  NexDB Web / Docker are all covered, with ready config snippets for Claude Code, Cursor,
  Codex, Windsurf, VS Code + Copilot, DeepSeek Harness, and generic MCP clients.
- **Brand-facing name is NexDB**: `@dbx-app/mcp-server`, `dbx-mcp`, and `DBX_*` are internal
  identifiers kept stable so existing configurations do not break.
- **Publisher**: Mutantcat Working Group (mutantcat.org), GitHub: https://github.com/Mutantcat-Working-Group

What it actually solves: the hard part of MCP integration is rarely the business arguments.
It is the transport details — GUI clients that do not inherit your shell PATH, a desktop HTTP
service that is off by default, permissions that live only in NexDB settings, Web/Docker `Host`
allowlists that must match exactly, and macOS keychain authorization that needs its own step.
Those traps repeat on every integration, so they are written down here.

### 2. Four Channels

| Situation | Channel | How it starts |
| --- | --- | --- |
| Local desktop, fastest and most reliable | Native binary (recommended) | Absolute `dbx-mcp` path, stdio |
| Node already installed, want zero setup | npm / npx | `npx -y @dbx-app/mcp-server`, stdio |
| Want a local HTTP endpoint | NexDB Desktop Streamable HTTP | `http://127.0.0.1:5225/mcp` + bearer token |
| Remote or containerized NexDB | NexDB Web / Docker | `DBX_WEB_URL` over stdio, or Web's own `/mcp` |

### 3. Installation

To use it as a skill, clone this repository into your skills directory:

```bash
git clone https://github.com/Mutantcat-Working-Group/NexDB-Skill.git \
  ~/.codex/skills/nexdb-mcp
```

Then install the NexDB MCP server itself (no Node.js required; native is recommended):

```bash
# macOS / Linux
curl -fsSL https://dbxio.com/install-mcp | sh
```

```powershell
# Windows PowerShell
irm https://dbxio.com/install-mcp.ps1 | iex
```

The script verifies the download, installs `dbx-mcp` into `~/.dbx/bin`, and prints ready-made
config for Claude Code, Cursor, Codex, and generic clients. Re-run the same command to upgrade.
Homebrew works on macOS / Linux too:

```bash
brew install t8y2/tap/dbx-mcp
brew upgrade t8y2/tap/dbx-mcp
```

**GUI clients need the expanded absolute path** — not `~`, not a bare `dbx-mcp`. They do not
necessarily inherit your shell PATH.

### 4. Quick Start

The shortest path is npx, with nothing installed globally:

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

Native binary form:

```json
{
  "mcpServers": {
    "dbx": {
      "command": "/Users/you/.dbx/bin/dbx-mcp"
    }
  }
}
```

Then just ask in natural language:

```text
List my NexDB connections
Show tables on local-pg
Describe the users table
Count orders created in the last seven days
Open the orders table        (requires NexDB Desktop running)
```

### 5. Permissions Live In NexDB

**NexDB Settings → MCP** stores one authoritative policy, re-read on every request: three
execution modes (read only / data read-write / full access), plus a connection allowlist,
per-connection database scope, and a tool allowlist.

**Do not put permission switches in client configuration.** `DBX_MCP_ALLOW_WRITES` and
`DBX_MCP_ALLOW_DANGEROUS_SQL` exist only for upgrade compatibility and cannot widen the central
policy; `DBX_MCP_SCOPE_*` can only narrow it further.

### 6. Documentation Map

| File | Contents |
| --- | --- |
| [SKILL.md](SKILL.md) | Skill body: choosing a channel, installing, configuring, safety boundaries |
| [references/clients.md](references/clients.md) | Claude Code / Cursor / Codex / Windsurf / VS Code / DSH / generic client configs |
| [references/connection-modes.md](references/connection-modes.md) | Four channels, environment variables, storage paths, driver and agent dependencies |
| [references/tools.md](references/tools.md) | Tool list, parameter notes, sessions and transactions, Salesforce, plugin tools, resources |
| [references/troubleshooting.md](references/troubleshooting.md) | Playbook for connection, permission, keychain, Docker, and driver failures |

### 7. Safety Boundaries

- Local mode only reads the connection profiles NexDB already stores; whether a query runs and
  whether writes are allowed is decided entirely by **NexDB Settings → MCP**.
- Desktop Streamable HTTP listens on loopback by default, and rotating the token takes effect
  immediately.
- In Web / Docker mode, keep tokens in `DBX_WEB_MCP_TOKEN_FILE` or your platform's secret
  manager — never commit a real token.
- This skill can lead to deletes, DDL, and bulk writes. Confirm destructive operations with the
  user before running them.

### 8. License

Apache-2.0, see [LICENSE](LICENSE).
