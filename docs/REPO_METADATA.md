# Repository Metadata

Canonical copy for every host. Apply this file first, then update each platform
through its API. The short description and homepage are identical on all five
remotes; topics are identical where the host supports the full set (GitCode caps
tags at five).

## Short description (≤ 120 chars)

```
Self-hosted publishing hub for writers. Draft once, publish to the platforms you use, and keep every copy in sync.
```

## Topics / tags

```
self-hosted  content-publishing  publishing  markdown  multi-platform
ai-writing  fastapi  vue3  mcp  playwright  sqlite  tauri  automation  chinese-content
```

## Homepage

```
https://badhope.github.io/harbor/
```

## Applying the metadata

### GitHub (three repositories)

```bash
gh api -X PATCH repos/badhope/harbor \
  -f description="Self-hosted publishing hub for writers. Draft once, publish to the platforms you use, and keep every copy in sync." \
  -f homepage="https://badhope.github.io/harbor/" \
  -f 'topics[]=self-hosted' -f 'topics[]=content-publishing' \
  -f 'topics[]=publishing' -f 'topics[]=markdown' \
  -f 'topics[]=multi-platform' -f 'topics[]=ai-writing' \
  -f 'topics[]=fastapi' -f 'topics[]=vue3' -f 'topics[]=mcp' \
  -f 'topics[]=playwright' -f 'topics[]=sqlite' -f 'topics[]=tauri' \
  -f 'topics[]=automation' -f 'topics[]=chinese-content'
```

Repeat for each additional GitHub mirror.

### Gitee

Repository fields use `PATCH /api/v5/repos/{owner}/{repo}`. Project labels use
`PUT /api/v5/repos/{owner}/{repo}/project_labels` with a JSON array of label names.

### GitCode

Repository fields use `PATCH /api/v5/repos/{owner}/{repo}` with form fields. GitCode
limits project tags to five (`tag_list` size 0–5), so the five broadest labels are
kept there: `self-hosted`, `content-publishing`, `multi-platform`, `automation`,
`mcp`. GitHub and Gitee carry the full topic list.
