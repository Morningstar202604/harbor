# 接入 MCP 客户端

## 结论

Harbor 自带 MCP Server（[`mcp_server.py`](../../mcp_server.py)，32 个工具），不需要再包一层插件。
客户端只负责"要做什么"，真正的浏览器、登录态、发布都在 Harbor 这台机器上执行。

登录**不在 MCP 里**完成：工具清单里没有登录工具。未登录时任务停在 `waiting_human`，
由人打开 Harbor 前端或 CLI 完成扫码。原因见 [login.md](login.md)。

## 本机 stdio（推荐）

适用于豆包工作、Claude Code、Cursor、Windsurf 等能拉起本地进程的客户端：

```json
{
  "mcpServers": {
    "harbor": {
      "command": "/path/to/harbor/backed/.venv/bin/python",
      "args": ["/path/to/harbor/mcp_server.py"],
      "env": {
        "HUB_DATA_DIR": "/path/to/harbor-data"
      }
    }
  }
}
```

- `command` 用绝对路径。Windows 指向 `backed\.venv\Scripts\python.exe`。
- `HUB_DATA_DIR` 只在 Harbor 服务用了自定义数据目录时填，**必须与服务端同一个目录**，
  否则客户端看到的是另一个空库、也没有登录态。默认可以省略。
- 保存后重启客户端，工具列表应出现 32 个。先调 `list_articles` 验证连通。

## 远程 streamable-http

Harbor 跑在服务器上、客户端在另一台机器时：

```bash
export HARBOR_MCP_TOKEN='<随机长串>'
cd /path/to/harbor
uv run --project backed python mcp_server.py \
  --transport streamable-http --host 127.0.0.1 --port 8900
```

客户端填 `http://127.0.0.1:8900/mcp`，请求头 `Authorization: Bearer <同一个 token>`。
建议用 SSH 隧道或 VPN 访问，不要把端口直接开到公网；非回环地址不带 token 时服务会拒绝启动。

## 边界

| 能做 | 不能做 |
|---|---|
| 建文章、AI 写/改/译/润色、发布、原地更新、查任务 | 代替人登录、输入密码、接管 cookie |
| 带登录态抓页面、截图、入库图片 | 把登录态导出给别的机器或模型 |
| 查平台在线状态、内容质检、标签建议 | 多租户隔离（一次部署服务一个人） |

## 排错

- **工具列表为空**：`command` 路径错，或依赖没装。先跑 `cd backed && uv sync`，
  再直接执行 `backed/.venv/bin/python mcp_server.py --help` 看是否报错。
- **看不到自己的文章**：`HUB_DATA_DIR` 与服务端不一致，改成同一个数据目录。
- **远程 401**：`HARBOR_MCP_TOKEN` 没设、客户端请求头没带，或两处值不一致。
- **发布停在 `waiting_human`**：登录失效。到 Harbor 主机点登录，完成后 `resume_task`，
  不要连续重试。
