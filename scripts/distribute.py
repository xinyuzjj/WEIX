#!/usr/bin/env python3
"""
内容分发模块 — 多平台衍生内容生成
===================================
将一篇长文章拆解为多平台版本：
- Twitter: 280 字观点摘要
- LinkedIn: 500-800 字职业化改写
- Newsletter: 完整摘要 + 全文引导

用法:
  python distribute.py --article article.md --output ./distribute
  python distribute.py --article article.md --platforms twitter,linkedin
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path


def extract_sections(md_content):
    """从 Markdown 文章中提取各章节"""
    sections = {}
    current_section = "preamble"
    current_content = []
    
    for line in md_content.split("\n"):
        if line.startswith("## "):
            if current_content:
                sections[current_section] = "\n".join(current_content)
            current_section = line[3:].strip()
            current_content = []
        else:
            current_content.append(line)
    
    if current_content:
        sections[current_section] = "\n".join(current_content)
    
    return sections


def extract_title(md_content):
    """提取文章标题"""
    for line in md_content.split("\n"):
        if line.startswith("# "):
            return line[2:].strip()
    return "无标题"


def extract_key_points(sections):
    """从各章节提取关键观点"""
    points = []
    for title, content in sections.items():
        # 取每章第一段作为观点
        for line in content.split("\n"):
            stripped = line.strip()
            if stripped and not stripped.startswith("#") and not stripped.startswith(">"):
                if len(stripped) > 20:
                    points.append(stripped[:200])
                    break
    return points[:5]  # 最多 5 个观点


def generate_twitter(title, sections, original_url=""):
    """生成 Twitter 版本（280 字以内）"""
    key_points = extract_key_points(sections)
    
    # 构建推文
    tweet = f"{title}\n\n"
    
    # 缩写关键观点
    for i, point in enumerate(key_points[:2], 1):
        short = point[:100].rsplit("。", 1)[0] + "。"
        tweet += f"{i}. {short}\n"
    
    tweet += f"\n#GitHub #开源项目"
    if original_url:
        tweet += f"\n{original_url}"
    
    # 确保不超过 280 字
    if len(tweet) > 280:
        tweet = tweet[:277] + "..."
    
    return tweet.strip()


def generate_linkedin(title, sections, original_url=""):
    """生成 LinkedIn 版本（500-800 字，职业化风格）"""
    key_points = extract_key_points(sections)
    
    post = f"""{title}

在关注 GitHub Trending 的过程中，我发现了一个值得专业开发者关注的项目。

"""
    
    for i, point in enumerate(key_points, 1):
        post += f"**{i}.** {point}\n\n"
    
    post += f"""
作为一个关注技术趋势的开发者，我认为这个项目的价值在于它解决了一个真实的行业痛点。建议各位花30分钟深入了解。

推荐给所有关注开源技术的朋友。"""
    
    if original_url:
        post += f"\n\n原文链接: {original_url}"
    
    post += f"\n\n#OpenSource #GitHub #TechTrends #Developer"
    
    return post


def generate_newsletter(title, sections, original_url=""):
    """生成 Newsletter 版本"""
    key_points = extract_key_points(sections)
    
    newsletter = f"""Subject: 本周推荐 | {title}

---

{title}

本周 GitHub Trending 上有一个项目引起了我的注意。以下是核心要点：

"""
    
    for i, point in enumerate(key_points, 1):
        newsletter += f"{i}. {point}\n\n"
    
    newsletter += f"""
---

[阅读全文]({original_url})

如果这篇文章对你有帮助，欢迎转发给需要的朋友。

*Best,*
*你的技术摘要团队*
"""
    
    return newsletter


def main():
    parser = argparse.ArgumentParser(description="多平台内容分发")
    parser.add_argument("--article", required=True, help="文章 Markdown 文件路径")
    parser.add_argument("--output", required=True, help="输出目录")
    parser.add_argument("--platforms", default="twitter,linkedin,newsletter",
                       help="目标平台，逗号分隔 (默认: twitter,linkedin,newsletter)")
    parser.add_argument("--url", default="", help="原创文章 URL")
    args = parser.parse_args()
    
    # 读取文章
    article_path = Path(args.article)
    if not article_path.exists():
        print(f"[ERROR] 文章不存在: {article_path}")
        sys.exit(1)
    
    with open(article_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 解析
    title = extract_title(content)
    sections = extract_sections(content)
    
    # 创建输出目录
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    platforms = [p.strip() for p in args.platforms.split(",")]
    
    results = {}
    
    if "twitter" in platforms:
        tweet = generate_twitter(title, sections, args.url)
        tweet_path = output_dir / "twitter.txt"
        tweet_path.write_text(tweet, encoding="utf-8")
        print(f"[OK] Twitter 版本: {tweet_path} ({len(tweet)} 字)")
        results["twitter"] = str(tweet_path)
    
    if "linkedin" in platforms:
        linkedin = generate_linkedin(title, sections, args.url)
        li_path = output_dir / "linkedin.md"
        li_path.write_text(linkedin, encoding="utf-8")
        print(f"[OK] LinkedIn 版本: {li_path} ({len(linkedin)} 字)")
        results["linkedin"] = str(li_path)
    
    if "newsletter" in platforms:
        newsletter = generate_newsletter(title, sections, args.url)
        nl_path = output_dir / "newsletter.md"
        nl_path.write_text(newsletter, encoding="utf-8")
        print(f"[OK] Newsletter 版本: {nl_path} ({len(newsletter)} 字)")
        results["newsletter"] = str(nl_path)
    
    # 汇总
    summary = {
        "generated_at": datetime.now().isoformat(),
        "source": str(article_path),
        "platforms": results,
    }
    summary_path = output_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    
    print(f"\n[OK] 分发完成，输出目录: {output_dir}")


if __name__ == "__main__":
    main()
