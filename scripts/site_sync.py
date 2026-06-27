#!/usr/bin/env python3
"""
网站同步模块 — GitHub + Cloudflare Pages
=========================================
将新文章同步到 GitHub 仓库，触发 Cloudflare Pages 自动部署。

用法:
  python site_sync.py --article article.md --repo /path/to/xyjunjunni.space
  python site_sync.py --article article.md --repo git@github.com:user/repo.git
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
import shutil


def sync_article_to_site(article_path, repo_path):
    """同步文章到网站仓库"""
    article_path = Path(article_path)
    repo_path = Path(repo_path)
    
    if not article_path.exists():
        print(f"[ERROR] 文章文件不存在: {article_path}")
        sys.exit(1)
    
    # 如果仓库不存在，尝试 clone
    if not repo_path.exists() or not (repo_path / ".git").exists():
        print(f"[INFO] 仓库不存在，尝试 clone...")
        if str(repo_path).startswith("git@") or str(repo_path).startswith("https://"):
            result = subprocess.run(
                f'git clone "{repo_path}" "{repo_path.name}"',
                shell=True, capture_output=True, text=True, timeout=60
            )
            if result.returncode != 0:
                print(f"[ERROR] Clone 失败: {result.stderr}")
                sys.exit(1)
            repo_path = Path(repo_path.name)
        else:
            print(f"[ERROR] 目录不存在且不是 Git URL: {repo_path}")
            sys.exit(1)
    
    # 确定内容目录
    content_dir = None
    for candidate in ["content", "posts", "articles", "src/posts", "blog"]:
        d = repo_path / candidate
        if d.exists():
            content_dir = d
            break
    
    if not content_dir:
        print("[INFO] 未找到文章目录，使用仓库根目录")
        content_dir = repo_path
    
    # 复制文章
    target_path = content_dir / article_path.name
    shutil.copy2(article_path, target_path)
    print(f"[OK] 文章已复制到: {target_path}")
    
    # 更新资源列表（如果存在 resources.json）
    resources_file = repo_path / "public" / "resources.json"
    if resources_file.exists():
        with open(resources_file, "r", encoding="utf-8") as f:
            resources = json.load(f)
        
        # 添加新文章
        resources.append({
            "title": article_path.stem,
            "path": str(target_path.relative_to(repo_path)),
            "date": datetime.now().strftime("%Y-%m-%d"),
            "type": "article",
        })
        
        with open(resources_file, "w", encoding="utf-8") as f:
            json.dump(resources, f, ensure_ascii=False, indent=2)
        print(f"[OK] 资源列表已更新")
    
    # Git 操作
    os.chdir(repo_path)
    
    # git add
    subprocess.run(
        f'git add "{target_path.relative_to(repo_path)}"',
        shell=True, check=True, timeout=30
    )
    
    # git commit
    commit_msg = f"Add article: {article_path.stem}"
    result = subprocess.run(
        ["git", "commit", "-m", commit_msg],
        capture_output=True, text=True, timeout=30
    )
    
    if result.returncode == 0:
        print(f"[OK] 已提交: {commit_msg}")
    else:
        if "nothing to commit" in result.stdout + result.stderr:
            print("[INFO] 没有变更需提交")
            return {"status": "no_changes"}
        else:
            print(f"[WARN] 提交可能失败: {result.stderr[:300]}")
    
    # git push
    result = subprocess.run(
        ["git", "push", "origin", "main"],
        capture_output=True, text=True, timeout=60
    )
    
    if result.returncode == 0:
        print(f"[OK] 已推送到 GitHub，Cloudflare Pages 将自动部署")
        return {"status": "success", "pushed": True}
    else:
        print(f"[ERROR] Push 失败: {result.stderr[:300]}")
        return {"status": "push_failed"}


def main():
    parser = argparse.ArgumentParser(description="网站同步 — GitHub + Cloudflare Pages")
    parser.add_argument("--article", required=True, help="文章 Markdown 文件路径")
    parser.add_argument("--repo", required=True, help="网站 GitHub 仓库路径或 URL")
    args = parser.parse_args()
    
    result = sync_article_to_site(args.article, args.repo)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
