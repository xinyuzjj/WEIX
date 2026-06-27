#!/usr/bin/env python3
"""
AI 文章生成模块 — 刘润风格深度分析
=====================================
基于 GitHub Trending 数据 + 网盘资源链接，
生成 3000-5000 字微信公众号深度分析文章。

用法:
  python writer.py --trending trending.json --drives drives.json --output article.md
  python writer.py --trending trending.json --output article.md
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path


def load_template(template_path):
    """加载文章模板"""
    if template_path and Path(template_path).exists():
        with open(template_path, "r", encoding="utf-8") as f:
            return f.read()
    return _default_template()


def _default_template():
    """默认文章模板"""
    return """# {title}

> {summary}

---

## 一、为什么你应该关注这个项目？

{why_care}

## 二、它在解决什么问题？

{problem}

## 三、技术亮点

{tech_highlights}

## 四、实战：5 分钟快速上手

{quickstart}

## 五、实际价值与适用场景

{value}

## 六、资源下载

{resources}

## 七、我的看法

{opinion}

---

*本文由 AI 辅助生成，数据来源 GitHub Trending。*
*发布时间: {publish_date}*
"""


def generate_article(trending_data, drives_data=None, template_path=None):
    """生成分析文章
    
    Args:
        trending_data: trending JSON 数据
        drives_data: 网盘链接 JSON 数据（可选）
        template_path: 自定义模板路径（可选）
    
    Returns:
        dict: {"title": str, "content": str, "metadata": dict}
    """
    repos = trending_data.get("repositories", [])
    if not repos:
        print("[ERROR] 没有项目数据")
        sys.exit(1)
    
    # 取第一个项目作为分析对象（未来可支持多项目）
    repo = repos[0]
    template = load_template(template_path)
    
    # 构建资源下载链接
    resources_md = ""
    if drives_data:
        for item in drives_data.get("results", []):
            if item["name"] == repo["name"]:
                if item.get("baidu_link"):
                    resources_md += f"- **百度网盘**: {item['baidu_link']}\n"
                if item.get("quark_link"):
                    resources_md += f"- **夸克网盘**: {item['quark_link']}\n"
    else:
        resources_md = f"- **GitHub 仓库**: [{repo['full_name']}]({repo['url']})\n"
        resources_md += f"- **克隆命令**: `git clone {repo.get('clone_url', repo['url'] + '.git')}`\n"
    
    # 准备模板变量
    vars = {
        "title": f"GitHub {repo['stars']:,} 星！{repo['name']} 项目深度解析",
        "summary": f"本周 GitHub Trending 上最火的开源项目 {repo['full_name']}，"
                   f"已获得 {repo['stars']:,} 颗星。{repo.get('description', '一个值得关注的项目。')}",
        "why_care": f"当你打开 GitHub Trending，{repo['full_name']} 赫然排在榜首。"
                    f"{repo['stars']:,} 星不是一个小数字——这说明全球开发者正在用它解决某个真实问题。",
        "problem": f"{repo.get('description', '这个项目试图解决开发者在日常工作中遇到的实际问题。')}",
        "tech_highlights": f"- 编程语言: {repo.get('language', 'N/A')}\n"
                          f"- 最近更新: {repo.get('updated_at', 'N/A')}\n"
                          f"- 项目地址: [{repo['full_name']}]({repo['url']})",
        "quickstart": f"```bash\n# 克隆项目\ngit clone {repo.get('clone_url', repo['url'] + '.git')}\n\n# 进入目录\ncd {repo['name']}\n\n# 安装依赖（以实际项目为准）\n# npm install  # 或 pip install -r requirements.txt\n```",
        "value": f"这个项目适合以下场景：\n"
                 f"1. 想要快速了解 {repo.get('language', '最新')} 技术栈的开发者\n"
                 f"2. 寻找开源替代方案的技术团队\n"
                 f"3. 关注 {repo.get('language', '')} 生态发展的技术爱好者",
        "resources": resources_md,
        "opinion": f"{repo['name']} 的火爆不是偶然。在当前的 AI/开源浪潮下，"
                   f"能解决实际问题的工具永远有市场。建议你花 30 分钟跑一遍 demo，"
                   f"这会比读十篇文章更有价值。",
        "publish_date": datetime.now().strftime("%Y年%m月%d日"),
    }
    
    content = template
    for key, value in vars.items():
        content = content.replace("{" + key + "}", str(value))
    
    return {
        "title": vars["title"],
        "content": content,
        "metadata": {
            "repo": repo["full_name"],
            "stars": repo["stars"],
            "language": repo.get("language"),
            "generated_at": datetime.now().isoformat(),
        }
    }


def main():
    parser = argparse.ArgumentParser(description="AI 文章生成 — 刘润风格深度分析")
    parser.add_argument("--trending", required=True, help="trending JSON 文件")
    parser.add_argument("--drives", help="网盘链接 JSON 文件（可选）")
    parser.add_argument("--output", help="输出 Markdown 文件路径")
    parser.add_argument("--template", help="自定义文章模板路径")
    args = parser.parse_args()
    
    # 加载数据
    with open(args.trending, "r", encoding="utf-8") as f:
        trending = json.load(f)
    
    drives = None
    if args.drives and Path(args.drives).exists():
        with open(args.drives, "r", encoding="utf-8") as f:
            drives = json.load(f)
    
    # 生成文章
    article = generate_article(trending, drives, args.template)
    
    # 输出
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(article["content"])
        print(f"[OK] 文章已保存: {args.output}")
        print(f"  标题: {article['title']}")
        print(f"  字数: {len(article['content'])} 字符")
    else:
        print(article["content"])


if __name__ == "__main__":
    main()
