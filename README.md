# Content Pipeline — 内容分发管道

> AgentSkills.io 标准技能 | 兼容 Hermes Agent / OpenClaw / Claude Code / WorkBuddy

一键完成「GitHub Trending → 双网盘存储 → AI 文章 → 微信发布 → 网站同步 → 全平台分发」完整链路。

## 管道架构

```
Step 1: GitHub Trending 抓取 → 本周/今日最热开源项目
Step 2: 双网盘存储       → 百度网盘 + 夸克网盘，生成分享链接
Step 3: AI 文章生成      → 3000-5000 字深度分析（刘润风格）
Step 4: 微信公众号发布   → 推送到草稿箱
Step 5: 网站同步         → GitHub + Cloudflare Pages 自动部署
Step 6: 多平台分发       → Twitter / LinkedIn / Newsletter
```

## 安装

### Hermes Agent

```bash
# 克隆到 Hermes skills 目录
git clone https://github.com/xinyuzjj/content-pipeline.git ~/.hermes/skills/content-pipeline
```

### OpenClaw

```bash
# 克隆到 OpenClaw agents 目录
git clone https://github.com/xinyuzjj/content-pipeline.git ~/.agents/skills/content-pipeline
```

### WorkBuddy

```bash
# 克隆到技能目录
git clone https://github.com/xinyuzjj/content-pipeline.git ~/.workbuddy/skills/content-pipeline
```

### 手动安装

```bash
git clone https://github.com/xinyuzjj/content-pipeline.git
cd content-pipeline
cp config.example.json config.json
# 编辑 config.json 填入密钥
```

## 快速开始

```bash
# 完整管道：本周最热 1 个项目
python3 scripts/pipeline.py --period weekly --limit 1

# 逐步确认模式
python3 scripts/pipeline.py --step-by-step

# 仅生成文章（不发布）
python3 scripts/writer.py --trending output/xxx/trending.json --output article.md

# 仅发布已有文章
python3 scripts/wechat_pub.py --article article.md --config config.json
```

## 前置条件

| 依赖项 | 用途 | 必需 |
|--------|------|------|
| Python 3.11+ | 主运行环境 | 是 |
| `bdpan` CLI | 百度网盘操作 | 是 |
| `gh` CLI | GitHub Trending / Git 操作 | 是 |
| 夸克网盘 Skill | 夸克网盘操作 | 是 |
| 微信公众号 APPID/SECRET | 发布到微信 | 否 |

## 许可证

MIT
