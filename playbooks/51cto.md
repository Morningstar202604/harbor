---
title: 51CTO 博客发布（模板）
platform: 51cto
schedule: "按需发布"
scope: template
updated: 2026-11-23
---

# 51CTO 博客发布（模板）

> 可复用模板，不含账号或真实文章 ID。AI 在用户登录后先读本文件，再决定发布、草稿、复检与报告。

## 目标

用 MetaWeblog XML-RPC 直接发到 51CTO 博客，不需要浏览器扫码；适合技术长文和系列教程。

## 登录后先确认

1. 在 Harbor 设置里填 `platforms.51cto.endpoint`、`username`、`password`；endpoint 里的博客地址名不是昵称。
2. 检查 XML-RPC 能连通；返回 401/500 时先核对 endpoint 和登录密码，不要反复重试。
3. 凭据是登录密码，不写进文章、不提交仓库。

## 内容适配

- 标题直给系列名/技术点；正文用 Markdown，Harbor 转 HTML 提交。
- 51CTO 读者偏运维、网络、后端和教程：给完整环境、命令、拓扑/表格、排错过程。
- 标签 3–8 个具体技术词；主线 `{{profile.mainline}}`，风格 `{{profile.style}}`。
- 没有封面接口；封面在后台手动设。

## 执行

1. 用 `publish_article` 发 `51cto`；需要草稿就 `draft_only=true`，需要直接发布就 false。
2. 发布后回读博客文章页：HTTP 200、标题、正文首段、代码块可见；图片逐张确认。
3. 更新用同一套 XML-RPC；先确认旧文章还在，再原地改。

## 限制

- 不支持浏览器登录态；完全依赖 config 里的 XML-RPC 凭据。
- 没有封面接口；标签可写，列表可用。
- 平台对 HTML 支持比 Markdown 稳，正文不要依赖复杂前端组件。

## 输出

写明文章 URL、草稿/已发布状态、标签、图片检查结果。明确写“已做完”；未完成写“未完成 + 原因”。

## 硬约束

不要把 51CTO 密码写进仓库；图片上传到 51CTO 图床，不引用仓库直链。
