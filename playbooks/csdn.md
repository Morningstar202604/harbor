---
title: CSDN 私密转公开（模板）
platform: csdn
schedule: "建议每天 1 次，直到清零"
scope: template
updated: 2026-11-22
---

# CSDN 私密转公开（模板）

> 可复用模板，不含任何真实账号或文章 ID。复制到 `profiles/<name>/playbooks/csdn.md` 后使用。

## 目标

把创作中心“仅我可见”的文章逐批改为“全部可见”，直到私密文章为 0。

## 执行

1. 读 `{{profile.paths.workspace}}/csdn-private-to-public.md`，拿到当前剩余数量与已公开 ID；文件不存在就从创作中心列表页自己数。
2. 登录 CSDN（账号 `{{profile.accounts.csdn}}`），进入创作中心，筛“仅我可见”。
3. CSDN 每天最多公开 5 篇私密文章，每次最多处理 5 篇；按列表顺序取前 5 篇改“全部可见”。
4. 改之前检查正文图片是否均为 CSDN 托管；发现外链（raw.githubusercontent.com / gitee.com / gitcode.com）先替换成 CSDN 图床再公开。
5. 改完立刻回读列表页复核状态确实变成“全部可见”，不能只看点击成功。
6. 成功后把已公开的 ID 和剩余数量追加写入 `{{profile.paths.workspace}}/csdn-private-to-public.md`。
7. 登录态失效就明确报告并停止，不反复重试。

## 输出

今天公开了哪些 ID、剩余多少篇、遇到的阻塞。明确写“已做完”，失败项写“未完成 + 原因”。

## 硬约束

禁止把 GitHub / Gitee / GitCode 仓库当图床、素材库、备份盘或发布产物存放点。CSDN“文章备份→同时备份到 GitCode”保持关闭，不要重新开启；正文图片一律用 CSDN 自带图床，禁止引用仓库直链。
