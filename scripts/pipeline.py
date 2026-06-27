#!/usr/bin/env python3
"""
Content Pipeline — 内容分发自动化管道

GitHub Trending → 双网盘存储 → 文章写作 → 微信发布 → 网站同步 → 多平台分发

Usage:
    python pipeline.py                          # 完整管道 (weekly trending)
    python pipeline.py --period daily           # 今日热门
    python pipeline.py --project owner/repo     # 指定项目
    python pipeline.py --step trending          # 只看趋势
    python pipeline.py --step store             # 只存储
    python pipeline.py --step article article.md # 只写作
    python pipeline.py --step publish article.md # 只发布
    python pipeline.py --step sync article.md    # 只同步网站
    python pipeline.py --step distribute article.md # 只分发
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# ── Configuration ─────────────────────────────────────────────────

CONFIG_FILE = Path(__file__).parent / "config.json"
OUTPUT_DIR = Path(__file__).parent / "output"

# External tool paths
GITHUB_TRENDING_SCRIPT = Path.home() / ".workbuddy/skills/skill_2053082035554123776/scripts/github_trending.py"
QUARK_CLI = Path.home() / ".workbuddy/skills/quark-drive/scripts/quark_cli.py"

# Drive config
BDPAN_CONFIG_PATH = "E:/workbuk/.bdpan_config"
QUARK_CONFIG_DIR = "E:/workbuk/.quark_config"

# Python
PYTHON = Path.home() / ".workbuddy/binaries/python/versions/3.13.12/python.exe"

# ── Helpers ───────────────────────────────────────────────────────

def load_config():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def run(cmd, cwd=None, env=None, timeout=300):
    """Run a shell command and return (stdout, stderr, returncode)."""
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    result = subprocess.run(
        cmd, shell=True, capture_output=True, text=True,
        cwd=cwd, env=merged_env, timeout=timeout,
        encoding="utf-8", errors="replace"
    )
    return result.stdout.strip(), result.stderr.strip(), result.returncode

def step_header(step, name):
    print(f"\n{'='*60}")
    print(f"  Step {step}: {name}")
    print(f"{'='*60}")

def step_done(ok=True, detail=""):
    status = "✅ DONE" if ok else "❌ FAILED"
    print(f"  {status}  {detail}")
    return ok

def ensure_output_dir(name):
    d = OUTPUT_DIR / name
    d.mkdir(parents=True, exist_ok=True)
    return d

# ── Step 1: GitHub Trending ───────────────────────────────────────

def step1_trending(period="weekly", limit=5, language=None):
    """Fetch trending repos from GitHub."""
    step_header(1, "GitHub Trending")

    if not GITHUB_TRENDING_SCRIPT.exists():
        print(f"  ⚠️  github_trending.py not found at {GITHUB_TRENDING_SCRIPT}")
        print(f"  Install the 'github-trending-cn' skill first.")
        return None

    cmd = f'{PYTHON} "{GITHUB_TRENDING_SCRIPT}" --period {period} --limit {limit} --json'
    if language:
        cmd += f" --language {language}"

    print(f"  Running: github_trending.py --period {period} --limit {limit}")
    stdout, stderr, rc = run(cmd, timeout=60)

    if rc != 0:
        print(f"  stderr: {stderr[:500]}")
        return step_done(False, "GitHub API may be rate-limited")

    try:
        repos = json.loads(stdout)
    except json.JSONDecodeError:
        # Try to find JSON in output
        import re
        match = re.search(r'\[.*\]', stdout, re.DOTALL)
        if match:
            repos = json.loads(match.group())
        else:
            print(f"  Raw output (first 500 chars): {stdout[:500]}")
            return step_done(False, "Could not parse JSON output")

    print(f"  Found {len(repos)} trending repos:")
    for i, r in enumerate(repos[:5], 1):
        stars = r.get("stargazers_count", r.get("stars", "?"))
        lang = r.get("language", "")
        name = r.get("full_name", r.get("name", "?"))
        desc = (r.get("description", "") or "")[:60]
        print(f"    {i}. {name}  ⭐{stars}  [{lang}]  {desc}")

    return step_done(True), repos

# ── Step 2: Dual Drive Storage ────────────────────────────────────

def step2_store(repos, selected_index=0):
    """Download project and upload to both Baidu and Quark drives."""
    step_header(2, "Dual Drive Storage")

    if not repos:
        return step_done(False, "No repos to store")

    repo = repos[selected_index] if isinstance(repos, list) else repos
    name = repo.get("full_name", repo.get("name", ""))
    html_url = repo.get("html_url", f"https://github.com/{name}")

    print(f"  Selected: {name}")
    print(f"  URL: {html_url}")

    # Clone repo
    output_dir = ensure_output_dir(datetime.now().strftime("%Y-%m-%d"))
    clone_dir = output_dir / name.replace("/", "_")

    print(f"\n  Cloning {html_url} ...")
    if clone_dir.exists():
        shutil.rmtree(clone_dir)

    stdout, stderr, rc = run(f'git clone --depth 1 "{html_url}" "{clone_dir}"', timeout=120)
    if rc != 0:
        print(f"  Clone failed: {stderr[:300]}")
        print(f"  Will try archive download instead...")
        # Fallback: download zip
        zip_url = f"{html_url}/archive/refs/heads/main.zip"
        stdout, stderr, rc = run(
            f'curl -L -o "{output_dir}/{name.replace("/", "_")}.zip" "{zip_url}"',
            timeout=180
        )
        if rc != 0:
            return step_done(False, "Could not download repo")
        print(f"  Downloaded as zip archive")

    # Upload to Baidu Drive
    print(f"\n  Uploading to Baidu Drive...")
    bdpan_remote = f"github-trending/{name.replace('/', '_')}"
    bd_path = str(clone_dir) if clone_dir.exists() else str(output_dir / f"{name.replace('/', '_')}.zip")
    stdout, stderr, rc = run(
        f'export PATH="$HOME/AppData/Local/bdpan:$PATH" && bdpan upload "{bd_path}" "{bdpan_remote}" --config-path "{BDPAN_CONFIG_PATH}"',
        timeout=300
    )
    baidu_ok = rc == 0
    print(f"  Baidu: {'✅' if baidu_ok else '⚠️'} {stderr[:200] if stderr else 'uploaded'}")

    # Get Baidu share link
    baidu_share = None
    if baidu_ok:
        stdout, stderr, rc = run(
            f'export PATH="$HOME/AppData/Local/bdpan:$PATH" && bdpan share "{bdpan_remote}" --json --config-path "{BDPAN_CONFIG_PATH}"',
            timeout=30
        )
        if rc == 0:
            try:
                share = json.loads(stdout)
                baidu_share = share.get("link", share.get("url", ""))
            except:
                baidu_share = stdout[:500]
        print(f"  Baidu Share: {baidu_share}")

    # Upload to Quark Drive
    print(f"\n  Uploading to Quark Drive...")
    quark_remote = f"/GitHub热门/{name.replace('/', '_')}"
    stdout, stderr, rc = run(
        f'QUARK_CONFIG_DIR="{QUARK_CONFIG_DIR}" PYTHONIOENCODING=utf-8 {PYTHON} "{QUARK_CLI}" upload "{bd_path}" "{quark_remote}"',
        timeout=300
    )
    quark_ok = rc == 0
    print(f"  Quark: {'✅' if quark_ok else '⚠️'} {stderr[:200] if stderr else 'uploaded'}")

    # Get Quark share link
    quark_share = None
    if quark_ok:
        stdout, stderr, rc = run(
            f'QUARK_CONFIG_DIR="{QUARK_CONFIG_DIR}" PYTHONIOENCODING=utf-8 {PYTHON} "{QUARK_CLI}" share "{quark_remote}" --expire 30d',
            timeout=30
        )
        if rc == 0:
            # Parse share link from output
            for line in stdout.split("\n"):
                if "pan.quark.cn" in line or "分享链接" in line:
                    quark_share = line.strip()
                    break
            if not quark_share:
                quark_share = stdout[:500]
        print(f"  Quark Share: {quark_share}")

    result = {
        "repo": name,
        "url": html_url,
        "baidu_share": baidu_share,
        "quark_share": quark_share,
        "local_path": str(bd_path),
    }

    # Save storage result
    with open(output_dir / "02_storage.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    return step_done(True), result

# ── Step 3: Article Writing ───────────────────────────────────────

LIURUN_TEMPLATE = """# {title}

{opening}

## 一、{subtitle_1}

{body_1}

## 二、{subtitle_2}

{body_2}

## 三、{subtitle_3}

{body_3}

## 四、{subtitle_4}

{body_4}

## 总结

{conclusion}

---

**资源获取：**

- 📦 GitHub 仓库：[{repo_name}]({repo_url})
- ☁️ 百度网盘：{baidu_link}
- ☁️ 夸克网盘：{quark_link}

> 说明：以上链接均为项目源码和依赖包，仅供学习研究使用。请遵守项目开源协议。
"""


def generate_article_prompt(repo, storage):
    """Build the article generation prompt."""
    name = repo.get("full_name", repo.get("name", ""))
    desc = repo.get("description", "") or "一个优秀的开源项目"
    stars = repo.get("stargazers_count", repo.get("stars", "?"))
    lang = repo.get("language", "")
    html_url = repo.get("html_url", "")
    topics = repo.get("topics", [])

    return f"""请写一篇微信公众号文章，主题是分析 GitHub 开源项目「{name}」。

项目信息：
- 名称：{name}
- 简介：{desc}
- Stars：{stars}
- 语言：{lang}
- 网址：{html_url}
- 标签：{", ".join(topics) if topics else "开源项目"}

资源链接：
- 百度网盘：{storage.get("baidu_share", "见文末")}
- 夸克网盘：{storage.get("quark_share", "见文末")}

写作要求（严格遵循刘润风格）：
1. 从一个具体的开发者痛点或行业现象切入，引发共鸣
2. 分析这个项目解决了什么实际问题，用真实场景说明
3. 技术亮点要讲得通俗，让非技术读者也能理解核心价值
4. 给出 2-3 个实际落地场景/案例
5. 最后给出"要不要学、怎么学"的行动建议
6. 语言简洁有力，段落短，每段一个观点
7. 小标题要有观点（不是描述性标题，是有态度的标题）
8. 3000-5000 字
9. 文末嵌入网盘资源链接
10. 禁止加 #话题标签
11. 禁止说"欢迎在评论区分享"
12. 禁止大量使用 emoji"""


def step3_article(repo, storage):
    """Generate article (placeholder - AI will fill content)."""
    step_header(3, "Article Writing")

    name = repo.get("full_name", repo.get("name", ""))
    stars = repo.get("stargazers_count", repo.get("stars", "?"))

    output_dir = ensure_output_dir(datetime.now().strftime("%Y-%m-%d"))
    article_path = output_dir / "03_article.md"

    # Generate article skeleton + prompt for AI to fill
    article_skeleton = {
        "repo": repo,
        "storage": storage,
        "prompt": generate_article_prompt(repo, storage),
        "template": LIURUN_TEMPLATE,
        "params": {
            "title": f"{name.split('/')[-1]}: 凭什么一周暴涨 {stars} Star？",
            "opening": "[从开发者的具体痛点切入，描述没有这个工具之前开发者是怎么挣扎的]",
            "subtitle_1": "它解决了一个被所有人忽视的痛点",
            "body_1": "[痛点描述 → 现有方案为什么不work → 这个项目的方案 → 为什么是对的]",
            "subtitle_2": "技术架构上，它做对了三件事",
            "body_2": "[技术亮点1 + 案例] [技术亮点2 + 对比] [技术亮点3 + 数据]",
            "subtitle_3": "三个你明天就能用上的场景",
            "body_3": "[场景1: 具体怎么用] [场景2: 具体怎么用] [场景3: 具体怎么用]",
            "subtitle_4": "要不要学？我的建议",
            "body_4": "[上手门槛分析] [学习路径] [常见坑点] [投入产出比]",
            "conclusion": "[一句话总结核心观点] [行动建议: 马上去试试/先观望/不值得花时间]",
            "repo_name": name,
            "repo_url": repo.get("html_url", ""),
            "baidu_link": storage.get("baidu_share", "（生成中）"),
            "quark_link": storage.get("quark_share", "（生成中）"),
        }
    }

    with open(article_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(article_skeleton, ensure_ascii=False, indent=2))

    print(f"  Article skeleton saved: {article_path}")
    print(f"  Title: {article_skeleton['params']['title']}")
    print(f"  ⚠️  Next step: AI will fill in the article content")
    print(f"  Prompt ready for generation ({len(article_skeleton['prompt'])} chars)")

    return step_done(True), article_skeleton

# ── Step 4: WeChat Publishing ─────────────────────────────────────

def step4_publish(article_data, auto_publish=False):
    """Publish article to WeChat Official Account draft box."""
    step_header(4, "WeChat Publish")

    appid = os.environ.get("WECHAT_APPID", "")
    secret = os.environ.get("WECHAT_SECRET", "")

    if not appid or not secret:
        print("  ⚠️  WECHAT_APPID / WECHAT_SECRET not configured")
        print("  Article is ready for manual publishing.")
        print("  Use the 'mp-draft-push' or 'wechat-publisher' skill to publish.")
        return step_done(False, "Missing WeChat credentials")

    # The actual publishing is handled by the mp-draft-push skill
    # This step prepares the data for it
    output_dir = ensure_output_dir(datetime.now().strftime("%Y-%m-%d"))

    title = article_data.get("params", {}).get("title", "GitHub 热门项目分析")
    summary = f"本周 GitHub 最值得关注的开源项目深度分析"

    publish_data = {
        "title": title,
        "summary": summary,
        "article_path": str(output_dir / "03_article_final.md"),
        "cover_path": str(output_dir / "03_article_cover.png"),
        "status": "ready" if auto_publish else "pending_manual"
    }

    with open(output_dir / "04_publish_result.json", "w", encoding="utf-8") as f:
        json.dump(publish_data, f, ensure_ascii=False, indent=2)

    print(f"  Title: {title}")
    print(f"  Status: {'auto-publish' if auto_publish else 'pending manual review'}")
    print(f"  Data saved: {output_dir / '04_publish_result.json'}")

    return step_done(True, "Ready for publish"), publish_data

# ── Step 5: Website Sync ──────────────────────────────────────────

def step5_sync(article_data, repo_info):
    """Sync article to xyjunjunni.space website."""
    step_header(5, "Website Sync")

    website_repo = repo_info.get("repo", "xyjunjunni.space")
    content_dir = repo_info.get("content_dir", "content/articles")
    branch = repo_info.get("branch", "main")

    title = article_data.get("params", {}).get("title", "GitHub Trending")
    repo_name = article_data.get("params", {}).get("repo_name", "")

    print(f"  Target: {website_repo} → {content_dir}/")
    print(f"  Article: {title}")

    # This step requires the website repo to be cloned locally
    # For now, generate the sync script
    output_dir = ensure_output_dir(datetime.now().strftime("%Y-%m-%d"))
    sync_script = output_dir / "05_sync_commands.sh"

    slug = repo_name.replace("/", "-").lower()
    date_str = datetime.now().strftime("%Y-%m-%d")

    with open(sync_script, "w", encoding="utf-8") as f:
        f.write(f"""#!/bin/bash
# Auto-generated sync script for {website_repo}
# Generated: {datetime.now().isoformat()}

cd {website_repo}

# Copy article
cp "{output_dir}/03_article_final.md" "{content_dir}/{date_str}-{slug}.md"

# Update index
echo "- [{date_str}] {title}" >> {content_dir}/index.md

# Commit and push
git add {content_dir}/
git commit -m "Add article: {title}"
git push origin {branch}

echo "✅ Website synced. Cloudflare Pages will auto-deploy."
""")

    print(f"  Sync script generated: {sync_script}")
    print(f"  Run manually or set up auto-sync in config.")
    print(f"  Or clone {website_repo} first, then pipeline can auto-push.")

    return step_done(True, "Sync script ready"), str(sync_script)

# ── Step 6: Content Repurposing ───────────────────────────────────

def step6_distribute(article_data):
    """Repurpose article for multiple platforms."""
    step_header(6, "Content Repurposing")

    output_dir = ensure_output_dir(datetime.now().strftime("%Y-%m-%d"))
    dist_dir = output_dir / "06_dist"
    dist_dir.mkdir(exist_ok=True)

    title = article_data.get("params", {}).get("title", "Hot GitHub Project")
    repo_name = article_data.get("params", {}).get("repo_name", "")
    repo_url = article_data.get("params", {}).get("repo_url", "")

    # Generate platform-specific content
    platforms = {}

    # Twitter/X Thread
    twitter_thread = f"""1/ 🔥 本周 GitHub 最火的项目：{repo_name}

{article_data.get('params', {}).get('subtitle_1', '一个被忽视的痛点，一个优雅的解决方案')}

👇 为什么它值得关注？

2/ 它解决的核心问题很简单：

[核心痛点]

但市面上现有的方案，要么太重，要么太慢。

3/ 这个项目的做法，聪明在哪？

1. [亮点1]
2. [亮点2]
3. [亮点3]

4/ 实际效果？

[数据/对比]

我一个朋友试了之后说："[真实反馈]"

5/ 三个立刻能用的场景：

🚀 [场景1]
🛠️ [场景2]
📊 [场景3]

6/ 要不要学？

✅ 如果你做 [相关领域]，强烈推荐
⏸️ 如果只是好奇，可以先 Star 观望

7/ 📦 完整资源：

🔗 GitHub: {repo_url}
☁️ 百度网盘 + 夸克网盘: 见公众号文章

RT to help a dev out 🙏"""

    platforms["twitter"] = twitter_thread

    # LinkedIn Post
    linkedin_post = f"""🔥 {title}

作为一个持续关注开源生态的人，本周 GitHub Trending 上有一个项目让我反复看了三遍。

{repo_name}

简单说，它做了一件很多人在抱怨但没人真正解决的事。

核心洞察：

1️⃣ [洞察1]
2️⃣ [洞察2]
3️⃣ [洞察3]

数据说话：
• [关键指标1]
• [关键指标2]

我的判断：

如果这个项目的维护者能持续迭代，它完全有可能成为 [领域] 的标配工具。

原因很简单：它解决的痛点太痛了，而且方案够轻。

三个建议：
1. 先 Star，再 Clone 下来跑一跑
2. 看一遍它的 README 和核心代码，架构设计值得学习
3. 如果你恰好有对应场景，直接试用

GitHub: {repo_url}

完整分析 + 资源下载，见评论 👇

#OpenSource #GitHub #DeveloperTools"""

    platforms["linkedin"] = linkedin_post

    # Newsletter
    newsletter = f"""Subject: 🔥 本周 GitHub 必看：{repo_name}

---

Hi there,

本周我在 GitHub Trending 上发现了一个很有意思的项目。

{repo_name}

一句话概括：{article_data.get('params', {}).get('subtitle_1', '它解决了一个被忽视的痛点')}

---

### 为什么值得关注？

[核心价值分析 - 300字]

---

### 技术亮点

• **亮点1**: [说明]
• **亮点2**: [说明]
• **亮点3**: [说明]

---

### 实际应用场景

1. **[场景1]**: [说明]
2. **[场景2]**: [说明]
3. **[场景3]**: [说明]

---

### 要不要学？

[建议 - 100字]

---

### 资源

📦 GitHub: {repo_url}
☁️ 百度网盘: [链接]
☁️ 夸克网盘: [链接]

---

Happy coding! 🚀"""

    platforms["newsletter"] = newsletter

    # Save all
    for platform, content in platforms.items():
        ext = "txt"
        if platform == "newsletter":
            ext = "md"
        filepath = dist_dir / f"{platform}.{ext}"
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  ✅ {platform}.{ext}  ({len(content)} chars)")

    return step_done(True), platforms

# ── Main Pipeline ─────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Content Pipeline - 内容分发自动化管道",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python pipeline.py                          # Full pipeline (weekly)
  python pipeline.py --period daily           # Today's trending
  python pipeline.py --project pytorch/pytorch # Specific project
  python pipeline.py --step trending          # Only fetch trending
  python pipeline.py --step article           # Only write article
        """
    )
    parser.add_argument("--period", choices=["daily", "weekly", "monthly"], default="weekly")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--language", help="Programming language filter")
    parser.add_argument("--project", help="Specific GitHub project (owner/repo)")
    parser.add_argument("--step", choices=["trending", "store", "article", "publish", "sync", "distribute"], help="Run single step")
    parser.add_argument("--article", help="Path to existing article for publish/sync/distribute")
    parser.add_argument("--auto-publish", action="store_true", help="Auto-publish to WeChat (default: manual)")
    parser.add_argument("--skip", nargs="+", choices=["trending", "store", "article", "publish", "sync", "distribute"], help="Steps to skip")

    args = parser.parse_args()
    config = load_config()

    print("╔══════════════════════════════════════════════════════════════╗")
    print("║         Content Pipeline — 内容分发自动化管道 v1.0           ║")
    print("║  GitHub Trending → 网盘 → 文章 → 微信 → 网站 → 全平台      ║")
    print("╚══════════════════════════════════════════════════════════════╝")

    # ── Determine steps to run ──
    all_steps = ["trending", "store", "article", "publish", "sync", "distribute"]
    if args.skip:
        steps = [s for s in all_steps if s not in args.skip]
    else:
        steps = all_steps

    if args.step:
        steps = [args.step]

    print(f"\n  Pipeline steps: {' → '.join(steps)}")
    print(f"  Period: {args.period}, Limit: {args.limit}")
    if args.project:
        print(f"  Target project: {args.project}")
    print()

    # ── Step-specific execution ──

    repos = None
    storage = None
    article = None

    if args.project and args.step in [None, "store", "article", "publish", "sync", "distribute"]:
        # Skip trending, use specified project
        repos = [{
            "full_name": args.project,
            "html_url": f"https://github.com/{args.project}",
            "description": "User-specified project",
            "stargazers_count": "?",
            "language": args.language or "",
        }]
        print(f"  Using specified project: {args.project}")

    for step in steps:
        if step == "trending" and repos is None:
            ok, repos = step1_trending(args.period, args.limit, args.language)
            if not ok:
                print("\n⚠️  Trending fetch failed. Stopping pipeline.")
                break

        elif step == "store" and repos is not None:
            ok, storage = step2_store(repos)
            if not ok:
                print("\n⚠️  Storage step had issues. Continuing anyway...")

        elif step == "article" and repos is not None:
            if storage is None:
                storage = {}
            ok, article = step3_article(repos[0] if isinstance(repos, list) else repos, storage)

        elif step == "publish":
            if args.article:
                pass  # Use existing article
            elif article:
                ok, _ = step4_publish(article, args.auto_publish)

        elif step == "sync":
            website_config = config.get("website", {})
            if article:
                ok, _ = step5_sync(article, website_config)
            else:
                print("  ⚠️  No article data to sync")

        elif step == "distribute":
            if article:
                ok, _ = step6_distribute(article)
            else:
                print("  ⚠️  No article data to distribute")

    print(f"\n{'='*60}")
    print(f"  Pipeline complete!")
    print(f"  Output: {OUTPUT_DIR}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
