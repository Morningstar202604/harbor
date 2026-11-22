---
title: GitHub Pages 发布（模板）
platform: github
schedule: "按需发布"
scope: template
updated: 2026-11-23
---

# GitHub Pages 发布（模板）

> 可复用模板，不含账号或真实文章 ID。AI 在用户登录后先读本文件，再决定发布、草稿、复检与报告。

## 目标

把文章以 Markdown + front-matter commit 到自己的 GitHub 仓库，由 Jekyll/Hugo/Astro 构建成 Pages。**commit 即发布，没有草稿箱。**

## 登录后先确认

1. 在 Harbor 设置里填 `platforms.github.token/owner/repo/branch/path_prefix`，或设 `GITHUB_TOKEN`。
2. token 需要有对应仓库 Contents 读写权限；403/404 就停，核对 owner/repo/branch。
3. token 不写进文章、不提交仓库。

## 内容适配

- 文件名和 slug 用英文/拼音，不要中文空格；front-matter 至少含 title/date/tags。
- 日期用 UTC；未来日期可能被 Jekyll 丢弃，发布当天就用当天日期。
- 正文 Markdown 原文，代码块标语言；图片放站点自己的静态资源目录或独立图床，不把仓库当通用图床/素材库，不用 raw.githubusercontent.com 直链当外链。
- 主线 `{{profile.mainline}}`；Pages 适合沉淀长文和系列，不适合短平快。

## 执行

1. 用 `publish_article` 发 `github`；`draft_only` 不支持，commit 成功即上线。
2. 回读仓库文件确认内容落盘，再等 Pages 构建；打开公开 URL 确认 HTTP 200。
3. 404 时检查 Actions/Pages 构建、front-matter 日期和路径，不要反复空推。
4. 更新用同一 path 再 PUT，天然是原地更新。

## 限制

- 没有草稿；commit 即发布。
- 单文件 ≤1MB；大图不要塞进 Markdown base64。
- Pages 构建有延迟，刚 push 完 404 不一定是失败。

## 输出

写明 commit/path、公开 URL、Pages 构建状态。明确写“已做完”；未完成写“未完成 + 原因”。

## 硬约束

token 只在本机；不要把仓库当通用图床、素材库或备份盘；图片只放站点构建所需的静态目录或独立图床，正文不引用 raw.githubusercontent.com 直链。
