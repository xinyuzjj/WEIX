---
name: weix
description: >
  Full-stack content distribution pipeline. Fetches GitHub trending projects,
  stores resources to Baidu Drive + Quark Drive with share links, writes
  deep-analysis articles (Liu Run style), publishes to WeChat Official Account,
  syncs to personal website (GitHub + Cloudflare Pages), and repurposes content
  for Twitter/LinkedIn/Newsletter. One command, end-to-end.
metadata: {
  "openclaw": {
    "emoji": "🚀",
    "requires": { "bins": ["python3", "bdpan", "git", "gh"], "env": ["WECHAT_APPID", "WECHAT_SECRET"] },
    "primaryEnv": "WECHAT_APPID"
  }
}
---

# Content Pipeline — 内容分发管道

一键完成「抓热点 → 存网盘 → 写文章 → 发微信 → 同步网站 → 多平台分发」完整链路。

## Skill 文件

| 文件 | 何时读取 |
|------|---------|
| `SKILL.md` | 技能触发后始终先读此处 |
| `scripts/pipeline.py` | 主控脚本，编排六个步骤 |
| `scripts/trending.py` | GitHub Trending 抓取模块 |
| `scripts/drives.py` | 百度网盘 + 夸克网盘操作模块 |
| `scripts/writer.py` | AI 文章生成模块（刘润风格） |
| `scripts/wechat_pub.py` | 微信公众号草稿箱发布模块 |
| `scripts/site_sync.py` | GitHub + Cloudflare Pages 网站同步模块 |
| `scripts/distribute.py` | 多平台内容分发模块 |
| `templates/article.md` | 文章输出模板 |
| `reference/tools.md` | 各工具详细参考文档 |
| `config.example.json` | 配置文件模板，复制为 config.json 后填写 |

## 管道流程

```
Step 1: GitHub Trending 抓取 → 选本周最热项目
Step 2: 双网盘存储      → 下载源码/工具包，上传百度+夸克，生成分享链接
Step 3: AI 文章生成     → 3000-5000字深度分析（刘润风格），嵌入网盘链接
Step 4: 微信发布        → 推送到公众号草稿箱
Step 5: 网站同步        → 更新 xyjunjunni.space（GitHub → Cloudflare Pages）
Step 6: 多平台分发      → 生成 Twitter/LinkedIn/Newsletter 版本
```

## 使用方式

### 初始化

首次使用需配置：

```bash
# 1. 复制配置文件
cp {baseDir}/config.example.json {baseDir}/config.json

# 2. 编辑 config.json，填入:
#    - WECHAT_APPID / WECHAT_SECRET（微信公众号）
#    - GITHUB_REPO（你的网站 GitHub 仓库路径）
#    - BAIDU_CONFIG（百度网盘配置路径，默认 E:/workbuk/.bdpan_config/bdpan.yaml）
#    - QUARK_CONFIG（夸克网盘配置路径，默认 E:/workbuk/.quark_config）
```

### 运行完整管道

```bash
# 抓本周最热 3 个项目，走完整管道
python3 {baseDir}/scripts/pipeline.py --period weekly --limit 3

# 抓今日热门，只做1个
python3 {baseDir}/scripts/pipeline.py --period daily --limit 1

# 逐步执行（可中断）
python3 {baseDir}/scripts/pipeline.py --step-by-step
```

### 单独运行某个步骤

```bash
# Step 1: 只看 GitHub 热门
python3 {baseDir}/scripts/trending.py --period weekly --limit 5

# Step 2: 上传文件到网盘
python3 {baseDir}/scripts/drives.py upload --file ./project.zip --project "some-project"

# Step 3: 生成文章
python3 {baseDir}/scripts/writer.py --trending ./trending_result.json

# Step 4: 发布到微信
python3 {baseDir}/scripts/wechat_pub.py --article ./output.md

# Step 5: 同步网站
python3 {baseDir}/scripts/site_sync.py --article ./output.md --repo ./xyjunjunni.space

# Step 6: 内容分发
python3 {baseDir}/scripts/distribute.py --article ./output.md --platforms twitter,linkedin,newsletter
```

## 执行规则

### 管道执行策略

当用户说「跑一遍完整管道」「发一篇文章」等时：

1. **先确认网盘登录状态** — 跑 `bdpan whoami` 和 `python3 {baseDir}/scripts/drives.py status`
2. **抓取 Trending** — 展示本周热门列表，让用户选一个或自动选第一个
3. **依次执行** — 按 Step 1→6 顺序，每步完成后报告状态
4. **失败处理** — 任一步骤失败，停止并报告，不继续

### 渐进式披露原则

- 不要一次性加载所有脚本内容到上下文
- 只读取当前步骤需要的脚本文件
- 运行时直接执行脚本，不要展开源码解读

### 网盘操作规则

百度网盘：
- CLI 命令: `bdpan <subcommand> --config-path "E:/workbuk/.bdpan_config/bdpan.yaml"`
- 上传: `bdpan upload --local-path <file> --remote-dir /<dir>`
- 分享: `bdpan share --remote-path /<path>`

夸克网盘：
- Python 脚本: `QUARK_CONFIG_DIR=E:/workbuk/.quark_config python3 {baseDir}/scripts/drives.py quark <action>`
- 上传: `quark upload --file <file> --dir <dir>`
- 分享: `quark share --file-id <id>`

### 文章生成规则

- 字数: 3000-5000 字
- 风格: 参考刘润公众号 — 逻辑清晰、有案例、有观点、接地气
- 结构: 标题 → 导语 → 项目简介 → 技术亮点 → 实际价值 → 快速上手 → 资源下载 → 总结
- 资源链接: 嵌入百度网盘 + 夸克网盘分享链接
- 模板: `{baseDir}/templates/article.md`

### 网站同步规则

- 目标仓库: xyjunjunni.space（GitHub + Cloudflare Pages 部署）
- 同步内容: 新文章 markdown 文件 + 更新资源列表
- 操作: git add → commit → push，Cloudflare Pages 自动部署

### 内容分发规则

- Twitter: 提取核心观点，280字以内 + 链接
- LinkedIn: 职业化改写，500-800字 + 链接
- Newsletter: 完整版摘要 + 阅读全文引导

## 核心操作指令

### 完整管道运行指令

```bash
cd {baseDir} && python3 scripts/pipeline.py --period weekly --limit 1
```

### 仅生成文章（不发布）

```bash
cd {baseDir} && python3 scripts/writer.py --trending trending_result.json --output article.md
```

### 仅发布到微信（已有文章）

```bash
cd {baseDir} && python3 scripts/wechat_pub.py --article article.md
```

## 错误处理

| 症状 | 原因 | 处理 |
|------|------|------|
| bdpan 命令不存在 | PATH 未设置 | `export PATH="$HOME/AppData/Local/bdpan:$PATH"` |
| 百度网盘 token 过期 | 超过30天 | `bdpan login --qrcode --config-path "E:/workbuk/.bdpan_config/bdpan.yaml"` |
| 夸克网盘 Cookie 过期 | 超过7天 | `python3 {baseDir}/scripts/drives.py quark login` |
| 微信发布返回 401 | APPID/SECRET 错误 | 检查 config.json 中的 WECHAT_APPID / WECHAT_SECRET |
| 网站同步失败 | GitHub 仓库路径不对 | 检查 config.json 中的 GITHUB_REPO |

## 依赖

- Python 3.11+ (httpx, qrcode, pillow)
- bdpan CLI（百度网盘）
- Git + GitHub CLI（网站同步）
- 微信公众号 APPID + SECRET
