#!/usr/bin/env python3
"""
GitHub Trending 抓取模块
========================
从 GitHub Trending 获取热门项目，输出结构化 JSON。

用法:
  python trending.py --period weekly --limit 5
  python trending.py --period daily --output trending.json
"""

import argparse
import json
import sys
from datetime import datetime


def fetch_trending_demo(period="weekly", limit=3):
    """
    抓取 GitHub Trending 数据。
    
    实际部署时替换为真实 API 调用:
    - GitHub Search API: https://api.github.com/search/repositories?q=created:>YYYY-MM-DD&sort=stars
    - 或使用 gh CLI: gh search repos --created=">$(date -d '7 days ago' +%Y-%m-%d)" --sort stars --limit 10 --json name,url,description,stargazersCount,language
    """
    print(f"[TRENDING] 获取 {period} 热门项目 (limit={limit})...")
    
    # 使用 gh CLI 获取真实数据
    import subprocess
    try:
        date_filter = {
            "daily": ">$(date -d '1 day ago' +%Y-%m-%d)",
            "weekly": ">$(date -d '7 days ago' +%Y-%m-%d)",
            "monthly": ">$(date -d '30 days ago' +%Y-%m-%d)",
        }
        
        cmd = (
            f'gh search repos --sort stars --order desc '
            f'--limit {limit} '
            f'--json name,owner,url,description,stargazersCount,language,updatedAt,topics '
            f'-- created:{date_filter.get(period, ">2026-06-20")}'
        )
        
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0 and result.stdout.strip():
            repos = json.loads(result.stdout)
        else:
            raise Exception(f"gh 命令失败: {result.stderr}")
            
    except Exception as e:
        print(f"  [WARN] gh CLI 调用失败: {e}")
        print(f"  [INFO] 使用示例数据代替（请确保已安装 GitHub CLI 并登录）")
        repos = _get_demo_data(limit)
    
    # 格式化输出
    output = {
        "fetched_at": datetime.now().isoformat(),
        "period": period,
        "count": len(repos),
        "repositories": []
    }
    
    for repo in repos:
        output["repositories"].append({
            "name": repo.get("name", ""),
            "full_name": repo.get("nameWithOwner", repo.get("fullName", "")),
            "owner": repo.get("owner", {}).get("login", "") if isinstance(repo.get("owner"), dict) else repo.get("owner", ""),
            "url": repo.get("url", ""),
            "description": repo.get("description", ""),
            "stars": repo.get("stargazersCount", repo.get("stargazers_count", 0)),
            "language": repo.get("language", ""),
            "topics": repo.get("topics", repo.get("repositoryTopics", {}).get("nodes", []) if isinstance(repo.get("repositoryTopics"), dict) else []),
            "updated_at": repo.get("updatedAt", repo.get("updated_at", "")),
            "clone_url": f"https://github.com/{repo.get('nameWithOwner', repo.get('full_name', repo.get('fullName', '')))}.git",
        })
    
    return output


def _get_demo_data(limit):
    """示例数据（当 gh CLI 不可用时使用）"""
    demo = [
        {"name": "openclaw", "owner": {"login": "openclaw"}, "nameWithOwner": "openclaw/openclaw",
         "url": "https://github.com/openclaw/openclaw",
         "description": "Open-source, local-first AI agent gateway — connect any LLM to any chat platform",
         "stargazersCount": 315000, "language": "TypeScript",
         "updatedAt": datetime.now().isoformat()},
        {"name": "hermes-agent", "owner": {"login": "NousResearch"}, "nameWithOwner": "NousResearch/hermes-agent",
         "url": "https://github.com/NousResearch/hermes-agent",
         "description": "Self-evolving AI agent with long-term memory and auto-skill creation",
         "stargazersCount": 280000, "language": "Python",
         "updatedAt": datetime.now().isoformat()},
        {"name": "claude-code", "owner": {"login": "anthropics"}, "nameWithOwner": "anthropics/claude-code",
         "url": "https://github.com/anthropics/claude-code",
         "description": "Claude Code is an agentic coding tool that lives in your terminal",
         "stargazersCount": 450000, "language": "TypeScript",
         "updatedAt": datetime.now().isoformat()},
        {"name": "v0", "owner": {"login": "vercel"}, "nameWithOwner": "vercel/v0",
         "url": "https://github.com/vercel/v0",
         "description": "Generative UI — generate React/Next.js apps from natural language",
         "stargazersCount": 120000, "language": "TypeScript",
         "updatedAt": datetime.now().isoformat()},
        {"name": "mastra", "owner": {"login": "mastra-ai"}, "nameWithOwner": "mastra-ai/mastra",
         "url": "https://github.com/mastra-ai/mastra",
         "description": "TypeScript agent framework for building AI applications",
         "stargazersCount": 85000, "language": "TypeScript",
         "updatedAt": datetime.now().isoformat()},
    ]
    return demo[:limit]


def main():
    parser = argparse.ArgumentParser(description="GitHub Trending 抓取")
    parser.add_argument("--period", choices=["daily", "weekly", "monthly"], default="weekly")
    parser.add_argument("--limit", type=int, default=3)
    parser.add_argument("--output", type=str, help="输出 JSON 文件路径")
    args = parser.parse_args()
    
    data = fetch_trending_demo(args.period, args.limit)
    
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"[OK] 已保存到: {args.output}")
    
    # 打印摘要
    print(f"\n{'='*50}")
    print(f"  GitHub Trending ({args.period}) — {data['count']} 个项目")
    print(f"{'='*50}")
    for i, repo in enumerate(data["repositories"], 1):
        print(f"\n  {i}. {repo['full_name']}")
        print(f"     ⭐ {repo['stars']:,}  |  {repo['language']}")
        print(f"     {repo['description'][:100]}")
    
    # 同时输出 JSON 到 stdout（方便管道使用）
    if not args.output:
        print(f"\n[JSON]\n{json.dumps(data, ensure_ascii=False, indent=2)}")


if __name__ == "__main__":
    main()
