# Content Pipeline — 内容分发自动化管道

> GitHub Trending → 网盘存储 → 深度文章 → 微信发布 → 网站同步 → 全平台分发

把一条内容从「发现热点」到「全网覆盖」的全部环节，压缩成一条命令。

---

## 一句话说明

找到 GitHub 本周最火的项目 → 把资源存到百度网盘+夸克网盘 → 写一篇刘润风格的深度分析文章 → 发布到微信公众号 → 同步更新你的网站 → 再拆成 Twitter/LinkedIn/Newsletter 多平台内容。

**以前：6 个工具来回切换，至少 3 小时。现在：一条命令，一杯咖啡的时间。**

---

## 触发规则

当用户提到以下关键词组合时触发：

| 触发词 | 示例 |
|--------|------|
| "公众号文章" + "热门项目" | "帮我写一篇 GitHub 热门项目的公众号文章" |
| "内容分发" + "管道" | "跑一下内容分发管道" |
| "GitHub trending" + "发布" | "找一个热门仓库，写文章发布" |
| "热点" + "网盘" + "微信公众号" | "分析最近的 AI 热点，上传资源，发公众号" |

---

## 完整工作流

```
┌─────────────────────────────────────────────────────────────────┐
│                    CONTENT PIPELINE v1.0                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Step 1  →  GitHub Trending  抓本周最火的开源项目                │
│              ↓                                                  │
│  Step 2  →  Baidu/Quark      上传项目资源 → 生成分享链接         │
│              ↓                                                  │
│  Step 3  →  AI Writer        撰写 3000-5000 字刘润风格文章      │
│              ↓                                                  │
│  Step 4  →  WeChat OA        推送到公众号草稿箱                  │
│              ↓                                                  │
│  Step 5  →  Website Sync     更新 xyjunjunni.space 网站内容      │
│              ↓                                                  │
│  Step 6  →  Repurposer       拆成 Twitter/LinkedIn/Newsletter    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Step 1: 抓热点 — GitHub Trending

```bash
python scripts/step1_trending.py --period weekly --limit 5
```

调用 GitHub Search API，抓本周 stars 增长最快的 5 个项目。输出 JSON 格式的项目列表，包含：
- 项目名、简介、语言、stars、链接
- 作者、最近更新日期

**策略**：优先选择「实用性高 + 有资源可下载」的项目（工具、框架、模板），跳过纯文档/配置类仓库。

### Step 2: 存储 — 双网盘分发

```bash
python scripts/step2_store.py --project <repo_name> --source <local_path>
```

自动完成：
1. **git clone** 或下载项目的 release 文件
2. 上传到百度网盘 `/apps/bdpan/github-trending/<project>/`
3. 上传到夸克网盘 `/GitHub热门/<project>/`
4. 生成两个分享链接（含提取码）
5. 输出 JSON：`{baidu_share, quark_share, files}`

**前置条件**：百度网盘（bdpan CLI）和夸克网盘（quark_cli.py）均需提前登录。

### Step 3: 写作 — 刘润风格深度分析

AI 自动生成一篇 3000-5000 字的文章，严格遵循刘润风格：

- 从一个具体场景/问题切入
- 3-4 个分论点，每个配真实案例
- 数据支撑，观点鲜明
- 最后给出行动建议
- 段落短，逻辑层层递进
- 自动嵌入网盘分享链接

**模板结构**：
```
# [项目名]：凭什么一周暴涨 Xk Star？

## 一、它解决了什么痛点？
[场景] → [痛点] → [方案]

## 二、技术上有哪些亮点？
[架构亮点] [性能对比] [创新点]

## 三、实际能用在什么地方？
[3个真实落地场景]

## 四、要不要学？怎么学？
[上手成本] [学习路径] [坑点提示]

## 总结
[核心建议] + [资源获取方式]
```

### Step 4: 发布 — 微信公众号

```bash
python scripts/step4_publish.py --article article.md --cover cover.png
```

- 调用 `wechat-publisher` 技能或 `mp-draft-push` 技能
- 自动生成 AI 封面图
- 推送到公众号草稿箱
- 支持预览和手动确认后再发布

### Step 5: 同步 — 更新网站

```bash
python scripts/step5_sync.py --article article.md --project <name>
```

更新 `xyjunjunni.space` 网站（GitHub + Cloudflare Pages）：
1. 将文章转为 Markdown 添加到网站仓库
2. 更新文章列表索引
3. Git commit + push
4. Cloudflare Pages 自动部署

### Step 6: 分发 — 多平台拆解

```bash
python scripts/step6_distribute.py --article article.md
```

将同一篇文章拆成：
- **Twitter/X Thread**（7-10 条推文）
- **LinkedIn Post**（专业版）
- **Newsletter**（邮件版）
- **Instagram Caption**（带 emoji）

---

## 一键运行

```bash
# 完整管道：从热点到全网覆盖
python scripts/pipeline.py --period weekly --topic "AI工具"

# 只看趋势（不发布）
python scripts/pipeline.py --step trending --period daily

# 从已有项目开始（跳过抓热点）
python scripts/pipeline.py --project "https://github.com/xxx/yyy"

# 只看分发（已有文章）
python scripts/pipeline.py --step distribute --article article.md
```

---

## 配置

### config.json

```json
{
  "pipeline": {
    "steps": ["trending", "store", "article", "publish", "sync", "distribute"],
    "auto_publish": false,
    "auto_sync": true
  },
  "trending": {
    "period": "weekly",
    "limit": 5,
    "github_token": ""
  },
  "storage": {
    "baidu": {
      "remote_base": "/apps/bdpan/github-trending",
      "config_path": "E:/workbuk/.bdpan_config"
    },
    "quark": {
      "remote_base": "/GitHub热门",
      "config_dir": "E:/workbuk/.quark_config"
    }
  },
  "wechat": {
    "appid": "",
    "secret": "",
    "article_style": "liurun"
  },
  "website": {
    "repo": "xyjunjunni.space",
    "branch": "main",
    "content_dir": "content/articles"
  },
  "repurpose": {
    "platforms": ["twitter", "linkedin", "newsletter"],
    "voice": "professional-casual"
  }
}
```

复制 `config.example.json` 为 `config.json` 并填入你的配置。

---

## 依赖关系

| 步骤 | 依赖工具 | 状态检查 |
|------|---------|---------|
| Step 1 | `github_trending.py` | Python 标准库，无额外依赖 |
| Step 2 | `bdpan` CLI + `quark_cli.py` | 需先登录: `bdpan whoami`、`quark_cli.py user` |
| Step 3 | AI 写作（内置） | 无需额外工具 |
| Step 4 | `mp-draft-push` / `wechat-publisher` | 需配置 WECHAT_APPID + WECHAT_SECRET |
| Step 5 | Git + `gh` CLI | 需配置 GitHub SSH key |
| Step 6 | `content-repurposer` | 需先 `scripts/setup.sh` |

---

## 错误处理

| 场景 | 处理方式 |
|------|---------|
| GitHub API 限流 | 自动重试，建议设置 GITHUB_TOKEN |
| 百度网盘未登录 | 提示运行 `bdpan login` |
| 夸克网盘未登录 | 提示运行 `quark_cli.py login` |
| 微信推送失败 | 检查 WECHAT_APPID / SECRET，回退到手动发布 |
| 网站同步失败 | 检查 Git remote / SSH 配置，输出手动步骤 |
| 某个步骤失败 | 不中断管道，跳过该步骤并记录日志 |

---

## 输出结构

每次运行在 `output/` 目录生成：

```
output/
└── 2026-06-27-awesome-tool/
    ├── 01_trending.json          # Step 1: 项目数据
    ├── 02_storage.json           # Step 2: 网盘链接
    ├── 03_article.md              # Step 3: 完整文章
    ├── 03_article_cover.png       # Step 3: AI 封面图
    ├── 04_publish_result.json     # Step 4: 发布状态
    ├── 05_sync_log.txt            # Step 5: 网站同步日志
    └── 06_dist/
        ├── twitter-thread.txt
        ├── linkedin-post.txt
        └── newsletter.md
```

---

## 使用场景

- **技术博主**：每周自动生成一篇 GitHub 趋势分析，发公众号 + 网站
- **资源站站长**：自动抓工具 → 存网盘 → 更新网站 → 发文章引流
- **团队 TL**：快速了解本周值得关注的开源项目，一键同步全平台
- **独立开发者**：分析竞品项目，存资源，写分析发公众号吸引种子用户

---

## 许可

MIT License — 自由使用，欢迎 PR。
