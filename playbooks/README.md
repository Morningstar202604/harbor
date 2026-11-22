# playbooks — 运营 SOP 模板

这里放**可复用**的运营流程模板，供任何部署 Harbor 的人改造成自己的日常 SOP。模板里没有任何真实账号、ID、报告链接或本机路径。

**定时任务的 query 只负责触发并指到文件，流程写在这里。**

## 为什么放在文件里

cron 里的 query 改一次要重开任务、没法 diff、没法 review。写成文件后可以版本化，改一次全平台生效，AI 也能在动手前完整读到。

## 怎么用

1. 一条命令建档案：`cd backed && uv run python -m cli init --name <name>`。它会生成
   `profiles/<name>/profile.yaml` 并把模板渲染到 `profiles/<name>/playbooks/`（`profiles/` 已被 `.gitignore` 忽略）。
2. 打开 `profile.yaml` 填账号、主线、风格、报告位置、进度目录；`{{profile.*}}` 由 `init` 自动替换。
3. 也可以手工复制模板，保留占位符由执行任务的 AI 读档案时解析。
4. 定时任务的 query 写成：

   ```
   本次请求是由「{标题}」定时任务到时触发的。执行 /path/to/profiles/<name>/playbooks/{platform}.md。
   先读 AGENTS.md 与 docs/agent/CONTEXT.md。登录失效即停止并报告；图片一律用平台图床。
   结束明确写“已做完”，失败写“未完成 + 原因”。
   ```

## 模板索引

15 个适配器每个都有一份 SOP。首启默认只勾推荐的 4 个，其余在向导里点「添加平台」即可接入。

| 平台 | 文件 | 建议节奏 | 主要动作 |
|---|---|---|---|
| 博客园 | [cnblogs.md](cnblogs.md) | 每天 1 次 | 热点文、发布设置、复检、评论互动 |
| 知乎 | [zhihu.md](zhihu.md) | 每天 1-2 次 | 巡检通知/活动、回答、文章、AI 声明 |
| CSDN | [csdn.md](csdn.md) | 每天 1 次直到清零 | 私密转公开、图床检查、回读复核 |
| 掘金 | [juejin.md](juejin.md) | 每天 1 次 | 签到、评论、沸点、私信、回关 |
| B站专栏 | [bilibili.md](bilibili.md) | 按需 | 草稿、分区/封面人工发表、回读 |
| 头条号 | [toutiao.md](toutiao.md) | 按需 | 图文草稿/发布、二次确认、复检 |
| 小红书 | [xiaohongshu.md](xiaohongshu.md) | 按需 | 20 字标题、纯文本、图片人工上传 |
| 微信公众号 | [wechat.md](wechat.md) | 按需 | 官方草稿箱、IP 白名单、素材图 |
| 开源中国 | [oschina.md](oschina.md) | 按需 | UEditor 发布、代码块、复检 |
| 思否 | [segmentfault.md](segmentfault.md) | 按需 | API 草稿、标签、页面发布 |
| 51CTO | [51cto.md](51cto.md) | 按需 | XML-RPC、HTML、标签、复检 |
| Dev.to | [devto.md](devto.md) | 按需 | 英文标题/摘要、4 个标签、Markdown |
| GitHub Pages | [github.md](github.md) | 按需 | commit 即发布、front-matter、Pages 构建 |
| Telegraph | [telegraph.md](telegraph.md) | 按需 | 免登录快速页、更新、公开链接 |
| 自建博客 | [metaweblog.md](metaweblog.md) | 按需 | WordPress/Typecho、XML-RPC、原地更新 |

## AI 登录后怎么拿到 SOP

MCP 工具 `get_platform_skill(platform)` 返回该平台的完整 SOP、内容规则、能力矩阵、限制和发布示例。用户说“已经登录了，接下来怎么做”时，AI 先调它，不要凭平台常识猜按钮。`list_platforms` 的 `has_skill` 字段可以确认有没有技能卡。

## 写新 playbook

1. 文件名用平台 id（和 `backed/service/publishing/adapters/` 对齐）。
2. front matter 必填 `title` / `platform` / `schedule` / `scope: template` / `updated`。
3. 正文按“前置 / 执行 / 边界与验收 / 输出 / 硬约束”分段，写成可执行步骤。
4. 跑 `python scripts/gen_agent_context.py` 更新 `docs/agent/CONTEXT.md`，否则 CI 的 `--check` 会红。

## 隐私红线

- 不在仓库里写真实账号、平台用户 ID、文章 ID、cookie、报告链接、本机绝对路径。
- 个人档案、进度文件放 `profiles/<name>/`，只在本机。
- 提交前跑 `python scripts/scan_privacy.py`；CI 也会跑。

## 不要做的事

- 不要把 SOP 写回 cron query。
- 不要把平台临时状态（剩余篇数、当天选题）写进模板；状态放 `profiles/<name>/progress/`。
- 不要在这里写通用写作规范；那属于 de-ai-tone / humanizer-zh 两个 Skill。
