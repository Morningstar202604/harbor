# profiles — 你自己的运营档案（不入库）

Harbor 的仓库只放代码和模板；账号、主线、报告位置、进度文件这些属于**个人数据**，放在 `profiles/<name>/`，不进版本库。

位置：源码运行默认在仓库 `profiles/`；桌面版/容器设置了 `HUB_DATA_DIR` 后落在
`<data>/profiles`；也可以用 `HARBOR_PROFILES_DIR` 显式指定。

```
profiles/
├── README.md          # 本文件，入库
├── example.yaml       # 字段示例，入库
└── <your-name>/       # 你的档案，.gitignore 忽略
    ├── profile.yaml
    ├── playbooks/     # 15 份平台 SOP 的个人副本
    └── progress/      # 每日进度、剩余清单
```

## 用法

最省事的是 Web / 桌面端「开始使用」向导：勾平台 → 生成档案与 SOP → 登录 → 复制 MCP。
之后在「设置 → 内容档案」里改主线、风格、互动额度与时间窗，逐份查看/编辑 SOP，
也可以建多份档案（例如技术号、生活号）并切换当前档案。

```bash
# 不想开界面：CLI 建档案 + 渲染全部 playbook
cd backed && uv run python -m cli init --name <your-name> --platforms cnblogs,juejin

# 也可以手工复制
cp profiles/example.yaml profiles/<your-name>/profile.yaml
cp playbooks/cnblogs.md profiles/<your-name>/playbooks/
```

然后把 `profile.yaml` 填成自己的。`init` 会把 `{{profile.*}}` 换成档案值；手工复制的副本由执行任务的 AI 读取 profile 后解析。

在界面里手改过的 SOP 会打 `customized: true`，自检不再按模板漂移报错；想回模板点「恢复模板」。
模板更新后要批量同步，别用「覆盖重写」修 SOP：那会把 `profile.yaml` 的账号一起重置。用只重渲染：

```bash
python scripts/render_playbook.py --profile <your-name>           # 重渲染本档案声明的平台
python scripts/render_playbook.py --profile <your-name> --check   # 只比对
# 或走 API：POST /api/v1/hub/onboarding/rerender {"name":"<your-name>"}
```

## 字段

| 字段 | 用途 |
|---|---|
| `name` / `timezone` | 档案名与时区 |
| `platforms` | 本档案接入的发布平台列表；`init` 自动写入，旧档案缺省时按 `playbooks/` 里已有副本推断 |
| `accounts.<platform>` | 各平台账号标识（不是密码） |
| `mainline` | 账号主线，选题时用来判断相关性 |
| `style` | 写作口吻与禁区 |
| `engagement` | 每日互动额度 |
| `content_plan` | 栏目/字数计划（知乎、掘金用） |
| `links.report` / `links.topic_bank` | 运营报告、选题库位置 |
| `paths.workspace` / `paths.progress` | 进度文件目录（绝对路径或相对仓库根） |
| `windows.active` | 活跃发布时段 |

## 多档案

`profiles/.active_profile` 记录当前激活的档案名（只有档案名，不含个人信息）。`get_platform_skill`
不传 `profile` 时读这个标记；界面切换当前档案时自动改写。没有标记时退回按目录名排序的第一份。

## 登录

登录态不在 `profile.yaml` 里：cookie 存在 Harbor 的数据目录，登录必须在 Harbor 主机上用前端或 CLI 完成。模型/Agent 只查状态，不碰凭证。详见 [../docs/guides/login.md](../docs/guides/login.md)。

## 红线

- 不把 `profile.yaml`、`playbooks/`、`progress/` 提交到任何仓库。
- 不在模板里写死真实账号、平台 ID、文章 ID、cookie、报告链接。
- 提交前跑 `python scripts/scan_privacy.py`。
