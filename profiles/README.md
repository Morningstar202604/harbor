# profiles — 你自己的运营档案（不入库）

Harbor 的仓库只放代码和模板；账号、主线、报告位置、进度文件这些属于**个人数据**，放在 `profiles/<name>/`，不进版本库。

```
profiles/
├── README.md          # 本文件，入库
├── example.yaml       # 字段示例，入库
└── <your-name>/       # 你的档案，.gitignore 忽略
    ├── profile.yaml
    ├── playbooks/     # 从 ../*.md 复制后改
    └── progress/      # 每日进度、剩余清单
```

## 用法

```bash
cp profiles/example.yaml profiles/<your-name>/profile.yaml
cp playbooks/cnblogs.md profiles/<your-name>/playbooks/
```

然后把 `profile.yaml` 填成自己的，playbook 里的 `{{profile.*}}` 由执行任务的 AI 读取 profile 后替换。

## 字段

| 字段 | 用途 |
|---|---|
| `name` / `timezone` | 档案名与时区 |
| `accounts.<platform>` | 各平台账号标识（不是密码） |
| `mainline` | 账号主线，选题时用来判断相关性 |
| `style` | 写作口吻与禁区 |
| `engagement` | 每日互动额度 |
| `content_plan` | 栏目/字数计划（知乎、掘金用） |
| `links.report` / `links.topic_bank` | 运营报告、选题库位置 |
| `paths.workspace` / `paths.progress` | 进度文件目录（绝对路径或相对仓库根） |
| `windows.active` | 活跃发布时段 |

## 红线

- 不把 `profile.yaml`、`playbooks/`、`progress/` 提交到任何仓库。
- 不在模板里写死真实账号、平台 ID、文章 ID、cookie、报告链接。
- 提交前跑 `python scripts/scan_privacy.py`。
