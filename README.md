# Content Pipeline — 内容分发自动化管道

> 🔥 GitHub Trending → ☁️ 双网盘存储 → ✍️ 深度文章 → 📱 微信发布 → 🌐 网站同步 → 📢 全平台分发

**一条命令，把「发现热点」到「全网覆盖」的全部环节自动化。**

---

## 这是什么？

每周手动做这些事的程序员，请举手：

1. 翻 GitHub Trending 找项目 ✋
2. 下载源码存网盘 ✋
3. 写分析文章 ✋
4. 排版发公众号 ✋
5. 更新自己的网站 ✋
6. 拆成 Twitter/LinkedIn 发 ✋

**Content Pipeline 把上面 6 步变成 1 条命令。**

---

## 快速开始

```bash
# 1. 克隆
git clone https://github.com/YOUR_USERNAME/content-pipeline.git
cd content-pipeline

# 2. 配置
cp config.example.json config.json
# 编辑 config.json，填入你的配置

# 3. 运行
python scripts/pipeline.py --period weekly
```

30 秒后，你得到：
- 📊 GitHub 本周最火项目列表
- ☁️ 百度网盘 + 夸克网盘分享链接
- ✍️ 一篇刘润风格的分析文章
- 📱 公众号草稿（待确认发布）
- 🌐 网站更新脚本
- 🐦 Twitter 串 / LinkedIn / Newsletter 多平台内容

---

## 管道流程

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ Step 1       │    │ Step 2       │    │ Step 3       │
│ GitHub       │───▶│ 百度+夸克     │───▶│ AI 写文      │
│ Trending     │    │ 双网盘存储    │    │ 刘润风格     │
└──────────────┘    └──────────────┘    └──────────────┘
                                               │
                    ┌──────────────────────────┤
                    ▼                          ▼
             ┌──────────────┐          ┌──────────────┐
             │ Step 4       │          │ Step 5       │
             │ 微信公众号    │          │ 网站同步      │
             │ 草稿箱       │          │ GitHub Pages  │
             └──────────────┘          └──────────────┘
                                               │
                                               ▼
                                        ┌──────────────┐
                                        │ Step 6       │
                                        │ 多平台分发    │
                                        │ Twitter等     │
                                        └──────────────┘
```

---

## 命令选项

```bash
# 完整管道（默认 weekly）
python scripts/pipeline.py

# 今日热门
python scripts/pipeline.py --period daily

# 只看 Python 项目
python scripts/pipeline.py --language python

# 指定某个项目
python scripts/pipeline.py --project vercel/ai

# 单步运行
python scripts/pipeline.py --step trending    # 只看趋势
python scripts/pipeline.py --step article     # 只写文章

# 跳过某些步骤
python scripts/pipeline.py --skip store       # 不存网盘
python scripts/pipeline.py --skip publish     # 不发公众号

# 自动发布
python scripts/pipeline.py --auto-publish
```

---

## 前置依赖

| 工具 | 用途 | 安装方式 |
|------|------|---------|
| `github_trending.py` | GitHub 热门抓取 | WorkBuddy 技能: github-trending-cn |
| `bdpan` CLI | 百度网盘操作 | WorkBuddy 技能: baidu-drive |
| `quark_cli.py` | 夸克网盘操作 | WorkBuddy 技能: quark-drive |
| `mp-draft-push` | 微信发布 | WorkBuddy 技能: wechat-publisher |
| `content-repurposer` | 多平台分发 | WorkBuddy 技能: content-repurposer |
| Git | 网站同步 | 系统自带 |
| Python 3.10+ | 脚本运行 | 系统自带 |

详见 [reference/tools.md](reference/tools.md)

---

## 配置说明

复制 `config.example.json` 为 `config.json`，按需修改：

```json
{
  "storage": {
    "baidu": { "enabled": true },
    "quark": { "enabled": true }
  },
  "wechat": {
    "appid": "wx_YOUR_APPID",
    "secret": "YOUR_SECRET"
  },
  "website": {
    "repo": "xyjunjunni.space",
    "auto_commit": false
  },
  "repurpose": {
    "enabled_platforms": ["twitter", "linkedin", "newsletter"]
  }
}
```

---

## 输出结构

```
output/
└── 2026-06-27/                    # 按日期组织
    ├── 01_trending.json           # GitHub 热门项目数据
    ├── 02_storage.json            # 网盘分享链接
    ├── 03_article.md              # 完整文章
    ├── 03_article_cover.png       # AI 封面图
    ├── 04_publish_result.json     # 微信发布状态
    ├── 05_sync_commands.sh        # 网站同步脚本
    └── 06_dist/
        ├── twitter.txt
        ├── linkedin.txt
        └── newsletter.md
```

---

## 许可证

MIT License — 自由使用、修改、分发。
