# 工具清单与用法要点

可用工具取决于构建功能和 **NexDB Settings → MCP** 的 allowlist。启用连接作用域后，
修改连接的工具和桌面 UI 工具会被隐藏。客户端缓存了旧列表时，服务端仍会拒绝
不在当前 allowlist 里的调用，改完权限记得刷新工具列表。

## 发现类

| 工具 | 说明 |
| --- | --- |
| `dbx_list_connections` | 列出当前 MCP 会话可见的连接 |
| `dbx_list_databases` | 列出连接中可通过 MCP 访问的数据库，遵守该连接的数据库范围 |
| `dbx_list_tables` | 列出表、视图、集合或消息队列 Topic |
| `dbx_describe_table` | 返回列定义和表元数据 |
| `dbx_list_routines` | 列出 Schema 中的存储过程与函数，可用 `routine_type` 过滤（`PROCEDURE` / `FUNCTION`） |
| `dbx_get_routine_source` | 按名称返回存储过程 / 函数源码，重载时用可选 `signature` 区分 |
| `dbx_get_schema_context` | 返回适合塞进 AI 上下文的紧凑 Schema 描述 |

先用 `dbx_list_connections` → `dbx_list_databases` → `dbx_list_tables` →
`dbx_describe_table` 把名字问清楚，再执行查询。不要凭猜测拼库名或表名。

## 连接管理类

| 工具 | 说明 |
| --- | --- |
| `dbx_add_connection` | 添加连接到 NexDB 存储 |
| `dbx_duplicate_connection` | 复制连接及其完整配置 |
| `dbx_remove_connection` | 从 NexDB 存储删除连接 |

这三个会改动 NexDB 的持久化配置。启用连接作用域时它们会被隐藏；
删除前务必向使用者确认。

## 执行类

| 工具 | 说明 |
| --- | --- |
| `dbx_execute_query` | 执行 SQL 或受支持的 MongoDB shell 命令，默认返回 100 行 |
| `dbx_execute_batch` | 一次执行多条语句的 SQL 脚本，按语句返回结果 |
| `dbx_execute_redis_command` | 执行 Redis 命令 |
| `dbx_peek_messages` | 读取 Kafka 消息，不提交消费位点 |
| `dbx_send_message` | 向支持的 MQ Topic / 队列发送消息 |

### `dbx_execute_query`

- `max_rows` 取值 1–1000，默认 100；越界会被夹取到范围内，而不是报错。
- `max_rows` 只对 SQL 生效。MongoDB shell 命令始终最多 100 行；
  多语句脚本路由到批量执行器时，每条语句最多 100 行。
- SQL 文本默认不进普通 MCP 错误，也不记日志。临时诊断用
  `DBX_MCP_DEBUG_SQL=1`，查完关掉。

### `dbx_execute_batch`

- 用方言感知的解析器拆语句，字符串、注释、存储过程里的分号不会拆坏批次。
- 默认遇第一条失败语句就停；`continue_on_error` 可让批内继续（连接级错误仍终止）。
- `use_transaction` 把多条语句放进同一个 `BEGIN … COMMIT`，整批要么全成要么回滚。
  该模式只返回一个合并结果，且不能与 `session_id` 或 `continue_on_error` 同时用。
  MySQL 系连接对含 DDL 的脚本会拒绝该选项（DDL 隐式提交，无法回滚）。
- 只读策略下，只要批内含一条写入或 DDL，整次调用都会被拒绝。
- 每个批次在执行期间独占连接，临时表和 `SET` 状态可在批内保留；
  要跨多次调用保留这些状态，先用 `dbx_open_session`。
- Redis 和 MongoDB 连接不支持批处理。

### `dbx_peek_messages`

需要构建包含 `mq-admin`。通过 `connection_id` 或 `connection_name` 选已保存的
Kafka 连接，并指定 `topic`：

```json
{
  "connection_name": "Kafka",
  "topic": "events",
  "count": 20,
  "start_position": "offset",
  "partition": 0,
  "offset": 120
}
```

- `count` 1–100，默认 20。
- `start_position` 为 `latest`（默认）、`earliest` 或 `offset`；
  只有 `offset` 模式必须传非负 `offset`。
- `partition` 可选；不传则跨分区读取。
- 结果含 `messages`，保留 base64 消息体和可无损解码时的 UTF-8 预览。
  `incomplete` 表示达到超时或扫描上限，`outputTruncated` 表示
  为满足 256 KiB 输出预算省略了整条消息。
- 只读快照，不提供持续订阅或全 Topic 文本搜索；其他 MQ 类型会被拒绝。

## 会话与事务

| 工具 | 说明 |
| --- | --- |
| `dbx_open_session` | 打开固定后端连接的有状态 SQL 会话 |
| `dbx_begin_transaction` | 在启用事务的原生 MySQL 会话上开始事务 |
| `dbx_commit_transaction` | 在 MySQL 确认 `COMMIT` 后提交当前会话事务 |
| `dbx_rollback_transaction` | 回滚当前会话事务 |
| `dbx_close_session` | 关闭会话并释放固定连接资源 |

普通 `dbx_execute_query` 调用彼此独立。需要保持数据库 Session 状态时，
先 `dbx_open_session`，再把返回的 `sessionId` 传给后续 `dbx_execute_query`
或 `dbx_execute_batch`。适用场景：`USE` 切换库、临时表、Session 变量与设置、
需要固定连接的显式事务或多步诊断。

- 会话只支持 SQL 连接，固定到一个连接和数据库。
- 未知、已关闭或过期的 `sessionId` 会失败，不会静默退化成普通查询。
- 用完调 `dbx_close_session`；默认空闲 30 分钟回收，最多 32 个并发会话。
- 会话不会放宽 SQL 策略，写入、DDL、生产保护、连接只读和数据库权限仍按每次请求重查。

### 原生 MySQL 显式事务

`dbx_open_session` 传 `enable_transactions: true` 会立即保留一条物理原生 MySQL 连接，
然后依次 `dbx_begin_transaction` → 带该 `session_id` 的一个或多个
`dbx_execute_query` / `dbx_execute_batch` → `dbx_commit_transaction` 或
`dbx_rollback_transaction`。

- 仅支持**本地原生 MySQL** 连接；NexDB Web / `DBX_WEB_URL`、外部驱动 profile、
  兼容引擎和其他数据库类型返回 `TRANSACTION_UNSUPPORTED`，不会静默退化成自动提交。
- 事务会话每次操作只接受一条已解析的 `SELECT`（含锁定读）、`INSERT`、`UPDATE`、
  `DELETE` 或 `REPLACE`；原始事务控制、DDL、`CALL`、`LOAD`、表锁、`SET`、`USE`、
  XA、文件/输出子句、可执行注释、优化器 hint 和多语句均被拒绝。
- 响应含 `transaction_state`（`idle` / `active` / `unknown`），适用时含
  `transaction_outcome`（`committed` / `rolled_back` / `unknown`）。
- 超时、取消、传输故障或丢失 `COMMIT` 确认会把结果永久标为 `unknown`，
  禁止该会话继续执行 SQL 并销毁连接，不会重放语句或 `COMMIT`。
- 回滚保证依赖 InnoDB 等事务型存储；触发器、存储函数、非事务表和外部副作用
  可能无法回滚。

## 桌面 UI 集成

| 工具 | 说明 |
| --- | --- |
| `dbx_open_table` | 在运行中的 NexDB 桌面端打开表 |
| `dbx_execute_and_show` | 执行查询并在 NexDB 中展示结果 |

这两个要求 NexDB 桌面端正在运行，且在 Web 模式或连接作用域下不可用。
其他工具是否需要桌面端，取决于该连接是原生执行还是 bridge / Agent 路径。

## Salesforce

Salesforce 连接用 SOQL 而非 SQL：`dbx_list_tables` 列出对象，`dbx_describe_table`
列出对象字段，`dbx_execute_query` 执行 SOQL。

| 工具 | 说明 |
| --- | --- |
| `dbx_salesforce_current_user` | 显示连接背后的用户与组织，含简档是否有 Modify All Data |
| `dbx_salesforce_prepare_write` | 准备一条记录写入，返回摘要和一次性确认令牌 |
| `dbx_salesforce_apply_write` | 用确认令牌应用已准备的写入 |

- `dbx_execute_batch` 与 `dbx_open_session` 会被拒绝：SOQL 只读、无多语句脚本、
  无固定会话、无事务。
- 写入永远不走查询通道，`dbx_execute_query` 以 `SALESFORCE_DML_REQUIRES_CONFIRMATION` 拒绝。
- 写入分两次调用：先 `prepare_write`，把摘要展示给使用者，再 `apply_write`。
  令牌一次性、5 分钟过期、与那一条语句绑定，变更内容就得重新准备。
- 需要 **NexDB Settings → MCP** 里该连接的 **允许 DML** 开关（默认关闭，
  未开启返回 `SALESFORCE_DML_DISABLED`）；只读执行模式下该开关无效。
- Salesforce 写入不是事务性的，`apply_write` 返回后无法回滚。

## 插件工具

实现了 `mcp/tools` 桥接协议的 NexDB 插件 sidecar，其工具可合并进 `tools/list`，
无需在客户端逐个配置插件的 `--mcp` 进程。只有 manifest 声明了 `mcp` 贡献且
`external_tools: true` 的插件（SSH、Files、Kafka、LDAP 等）才暴露。

- 工具名形如 `dbx_<插件前缀>__<工具名>`：`io.dbx.ssh` → `dbx_ssh__sftp_list_dir`。
- 连接由宿主绑定，schema 里的 `connectionId` / `connectionName` 被移除，
  改用可选的 `dbx_connection` 参数选择已放行的连接；只有一个可用连接时可省略。
  凭据由宿主注入，永不经过模型或客户端。
- 作用域会话与全局 MCP 设置同样约束插件工具。白名单按精确名称匹配，
  启用后要把 `dbx_<前缀>__<工具名>` 逐个加入 allowlist（或清空白名单全部放行）。
- Web / Docker 后端不提供插件工具。
- `DBX_MCP_PLUGIN_TOOLS=lazy` 只暴露 `dbx_plugin_list` / `dbx_plugin_tools` /
  `dbx_plugin_call` 三个元工具，按需把 schema 拉进上下文；`both` 同时平铺，
  默认 `flat`。

## Resources

支持 MCP Resources 的客户端可以读连接目录和元数据模板：

| Resource URI | 说明 |
| --- | --- |
| `dbx://connections` | 当前范围内可见的连接 |
| `dbx://connections/{connection_id}/databases` | 指定连接中可见的数据库 |
| `dbx://connections/{connection_id}/tables{?database,schema}` | 表和视图 |
| `dbx://connections/{connection_id}/table-schema{?database,schema,table}` | 指定表字段定义，`table` 必填 |

Resource 的发现与读取复用对应 Tool 的白名单和范围限制；查询参数值要 URI 编码。
SQL 执行和所有可写操作仍只通过 Tool 提供。
