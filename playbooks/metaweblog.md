---
title: 自建博客发布（模板）
platform: metaweblog
schedule: "按需发布"
scope: template
updated: 2026-11-23
---

# 自建博客发布（模板）

> 可复用模板，不含账号或真实文章 ID。AI 在用户登录后先读本文件，再决定发布、草稿、复检与报告。

## 目标

用 MetaWeblog XML-RPC 发到自己的 WordPress / Typecho / Halo 等博客，完全掌控内容和归档。

## 登录后先确认

1. 在 Harbor「设置 → 平台账号 → 配置凭据」填 XML-RPC 地址、登录名与应用密码；WordPress 建议用“应用程序密码”，不要用主密码。
2. 确认 endpoint 是 `https://域名/xmlrpc.php` 或站点实际 XML-RPC 地址；404/403 先查伪静态和 XML-RPC 开关。
3. 凭据不写进文章、不提交仓库。

## 内容适配

- 标题直给；正文传 Markdown 原文，Typecho 原生渲染，WordPress 需 Markdown 插件。
- 标签写 3–8 个具体词；没有封面接口，封面在主题/后台设置。
- 主线 `{{profile.mainline}}`，风格 `{{profile.style}}`；自建站适合长文、系列和永久归档。

## 执行

1. 用 `publish_article` 发 `metaweblog`；`draft_only=true` 存草稿，false 直接发布。
2. 回读文章页：HTTP 200、标题、正文首段、代码块、标签可见；图片逐张确认。
3. 更新用同一 post_id 原地改，不重复发新文。

## 限制

- 没有封面接口；部分主题不显示代码高亮，发布前预览。
- XML-RPC 可能被安全插件关闭；失败时让用户检查插件/防火墙。
- Markdown 渲染取决于站点插件，必要时转 HTML。

## 输出

写明文章 URL、草稿/已发布、标签、图片检查结果。明确写“已做完”；未完成写“未完成 + 原因”。

## 硬约束

密码/应用密码只在本机；图片上传到自己博客媒体库，不引用仓库直链。
