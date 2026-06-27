#!/usr/bin/env python3
"""
Content Pipeline — 内容分发管道主控脚本
=========================================
一条命令完成: GitHub Trending → 网盘存储 → AI 文章 → 微信发布 → 网站同步 → 多平台分发

用法:
  python pipeline.py --period weekly --limit 3     # 完整管道
  python pipeline.py --step-by-step                 # 逐步执行
  python pipeline.py --step 1 --period daily        # 只跑某一步
"""

import argparse
import json
import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime

# ── 路径配置 ──────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = BASE_DIR / "scripts"
OUTPUT_DIR = BASE_DIR / "output"
CONFIG_FILE = BASE_DIR / "config.json"

# ── 工具函数 ──────────────────────────────────────────────

def load_config():
    """加载配置文件"""
    if not CONFIG_FILE.exists():
        print(f"[ERROR] 配置文件不存在: {CONFIG_FILE}")
        print(f"请复制 config.example.json 为 config.json 并填写必要信息")
        sys.exit(1)
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def run_step(name, cmd, cwd=None):
    """运行一个管道步骤"""
    print(f"\n{'='*60}")
    print(f"  Step: {name}")
    print(f"{'='*60}")
    result = subprocess.run(cmd, shell=True, cwd=cwd or str(BASE_DIR))
    if result.returncode != 0:
        print(f"\n[FAILED] {name} 执行失败 (exit code: {result.returncode})")
        return False
    print(f"\n[OK] {name} 完成")
    return True


def check_drives():
    """检查网盘登录状态"""
    print("[CHECK] 检查网盘登录状态...")
    ok = True

    # 百度网盘
    bdpan_path = os.environ.get("PATH", "")
    if "bdpan" not in bdpan_path:
        local_bdpan = Path.home() / "AppData" / "Local" / "bdpan"
        if local_bdpan.exists():
            os.environ["PATH"] = str(local_bdpan) + os.pathsep + bdpan_path

    result = subprocess.run(
        'bdpan whoami --config-path "E:/workbuk/.bdpan_config/bdpan.yaml"',
        shell=True, capture_output=True, text=True
    )
    if result.returncode != 0:
        print("  [WARN] 百度网盘未登录，将跳过网盘步骤")
        ok = False
    else:
        print(f"  [OK] 百度网盘: {result.stdout.strip()}")

    # 夸克网盘
    result = subprocess.run(
        f'QUARK_CONFIG_DIR=E:/workbuk/.quark_config {sys.executable} {SCRIPTS_DIR}/drives.py quark status',
        shell=True, capture_output=True, text=True, cwd=str(BASE_DIR)
    )
    if result.returncode != 0:
        print("  [WARN] 夸克网盘未登录，将跳过夸克步骤")
    else:
        print(f"  [OK] 夸克网盘已登录")

    return ok


def ensure_output_dir():
    """确保输出目录存在"""
    OUTPUT_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = OUTPUT_DIR / timestamp
    run_dir.mkdir(exist_ok=True)
    return run_dir


# ── 主流程 ──────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Content Pipeline — GitHub Trending → 网盘 → 文章 → 微信 → 网站 → 分发",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python pipeline.py --period weekly --limit 3    # 本周最热3个项目
  python pipeline.py --period daily --limit 1     # 今日最热1个项目
  python pipeline.py --step 1 --period weekly     # 只抓 Trending
  python pipeline.py --step 4 --article ./output/xxx/article.md  # 只发微信
  python pipeline.py --step-by-step               # 逐步确认执行
        """
    )
    parser.add_argument("--period", choices=["daily", "weekly", "monthly"],
                        default="weekly", help="Trending 时间范围 (默认: weekly)")
    parser.add_argument("--limit", type=int, default=1,
                        help="项目数量 (默认: 1)")
    parser.add_argument("--step", type=int, choices=[1, 2, 3, 4, 5, 6],
                        help="只执行指定步骤")
    parser.add_argument("--step-by-step", action="store_true",
                        help="逐步确认模式")
    parser.add_argument("--article", type=str,
                        help="已有文章路径 (用于 step 4/5/6)")
    parser.add_argument("--skip-drives", action="store_true",
                        help="跳过网盘步骤")
    parser.add_argument("--skip-publish", action="store_true",
                        help="跳过微信发布步骤")
    parser.add_argument("--dry-run", action="store_true",
                        help="仅展示计划，不实际执行")

    args = parser.parse_args()
    config = load_config()

    # 创建本次运行的输出目录
    run_dir = ensure_output_dir()
    print(f"[INFO] 输出目录: {run_dir}")

    steps = [
        ("抓取 GitHub Trending", f'python "{SCRIPTS_DIR}/trending.py" --period {args.period} --limit {args.limit} --output "{run_dir}/trending.json"'),
        ("存入双网盘 + 生成分享链接", f'python "{SCRIPTS_DIR}/drives.py" batch-upload --trending "{run_dir}/trending.json" --output "{run_dir}/drives.json"'),
        ("AI 生成深度文章", f'python "{SCRIPTS_DIR}/writer.py" --trending "{run_dir}/trending.json" --drives "{run_dir}/drives.json" --output "{run_dir}/article.md" --template "{BASE_DIR}/templates/article.md"'),
        ("发布到微信公众号", f'python "{SCRIPTS_DIR}/wechat_pub.py" --article "{run_dir}/article.md" --config "{CONFIG_FILE}"'),
        ("同步到网站 (GitHub + Cloudflare)", f'python "{SCRIPTS_DIR}/site_sync.py" --article "{run_dir}/article.md" --repo "{config.get("GITHUB_REPO", "")}"'),
        ("多平台内容分发", f'python "{SCRIPTS_DIR}/distribute.py" --article "{run_dir}/article.md" --output "{run_dir}/distribute"'),
    ]

    step_names = ["GitHub Trending", "网盘存储", "AI 文章", "微信发布", "网站同步", "内容分发"]

    if args.step:
        # 只跑指定步骤
        name, cmd = steps[args.step - 1]
        if not run_step(step_names[args.step - 1], cmd):
            sys.exit(1)
        return

    # 检查网盘状态
    if not args.skip_drives:
        check_drives()

    if args.dry_run:
        print("\n[DRY RUN] 将执行以下步骤:")
        for i, (name, cmd) in enumerate(steps, 1):
            print(f"  {i}. {name}")
            print(f"     命令: {cmd[:100]}...")
        return

    # 逐步确认模式
    if args.step_by_step:
        for i, (name, cmd) in enumerate(steps, 1):
            print(f"\n准备执行 Step {i}: {name}")
            resp = input("按 Enter 继续, 's' 跳过, 'q' 退出: ").strip().lower()
            if resp == 'q':
                print("已取消")
                sys.exit(0)
            if resp == 's':
                print(f"跳过 Step {i}")
                continue
            if not run_step(step_names[i - 1], cmd):
                print("管道中断")
                sys.exit(1)
    else:
        # 自动依次执行
        for i, (name, cmd) in enumerate(steps, 1):
            if args.skip_drives and i == 2:
                print(f"\n[SKIP] {step_names[i-1]} (--skip-drives)")
                continue
            if args.skip_publish and i == 4:
                print(f"\n[SKIP] {step_names[i-1]} (--skip-publish)")
                continue

            if not run_step(step_names[i - 1], cmd):
                print(f"\n管道在 Step {i} 中断，已完成的内容保存在: {run_dir}")
                sys.exit(1)

    print(f"\n{'='*60}")
    print(f"  管道执行完毕！")
    print(f"  所有输出文件: {run_dir}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
