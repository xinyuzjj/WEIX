#!/usr/bin/env python3
"""
云盘操作模块 — 百度网盘 + 夸克网盘
====================================
统一接口操作双网盘：上传文件、生成分享链接、查询状态。

用法:
  python drives.py status                    # 检查双盘状态
  python drives.py upload --file <file> --project <name>  # 上传文件到双盘
  python drives.py batch-upload --trending trending.json  # 批量处理 Trending 项目
  python drives.py quark status              # 仅夸克
  python drives.py quark share --file-id <id>  # 夸克分享
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlencode


# ── 配置 ──────────────────────────────────────────────────
BAIDU_CONFIG = "E:/workbuk/.bdpan_config/bdpan.yaml"
QUARK_CONFIG = "E:/workbuk/.quark_config"
BAIDU_BIN = os.path.expandvars("$HOME/AppData/Local/bdpan/bdpan")


def _bdpan(cmd):
    """执行百度网盘命令"""
    full_cmd = f'{BAIDU_BIN} {cmd} --config-path "{BAIDU_CONFIG}"'
    result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True, timeout=120)
    return result


def _quark(cmd):
    """执行夸克网盘命令"""
    env = os.environ.copy()
    env["QUARK_CONFIG_DIR"] = QUARK_CONFIG
    scripts_dir = Path(__file__).resolve().parent
    quark_cli = scripts_dir.parent.parent / "quark-drive" / "scripts" / "quark_cli.py"
    
    # 查找夸克 CLI 脚本
    candidates = [
        Path.home() / ".workbuddy" / "skills" / "quark-drive" / "scripts" / "quark_cli.py",
        scripts_dir.parent.parent / "quark-drive" / "scripts" / "quark_cli.py",
    ]
    cli_path = None
    for c in candidates:
        if c.exists():
            cli_path = c
            break
    
    if not cli_path:
        return subprocess.CompletedProcess(args=[], returncode=1, stdout="", 
                                           stderr="夸克 CLI 脚本未找到，请确认 skill 已安装")
    
    full_cmd = f'python "{cli_path}" {cmd}'
    result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True, 
                          timeout=120, env=env)
    return result


# ── 命令实现 ──────────────────────────────────────────────

def cmd_status():
    """检查双盘登录状态"""
    results = {"baidu": False, "quark": False, "baidu_user": "", "quark_user": ""}
    
    # 百度
    r = _bdpan("whoami")
    results["baidu"] = (r.returncode == 0)
    if results["baidu"]:
        results["baidu_user"] = r.stdout.strip().split("\n")[0] if r.stdout else "unknown"
    
    # 夸克
    r = _quark("user")
    results["quark"] = (r.returncode == 0)
    if results["quark"]:
        for line in r.stdout.split("\n"):
            if "昵称" in line or "nickname" in line.lower():
                results["quark_user"] = line.split(":")[-1].strip()
    
    print(json.dumps(results, ensure_ascii=False, indent=2))
    return results


def cmd_upload(file_path, project_name):
    """上传文件到双盘"""
    results = {"baidu": None, "quark": None}
    
    file_path = Path(file_path)
    if not file_path.exists():
        print(f"[ERROR] 文件不存在: {file_path}")
        sys.exit(1)
    
    # 百度网盘上传
    print(f"[BAIDU] 上传 {file_path.name} ...")
    r = _bdpan(f'upload --local-path "{file_path}" --remote-dir "/{project_name}"')
    if r.returncode == 0:
        # 获取分享链接
        print(f"[BAIDU] 生成分享链接 ...")
        r2 = _bdpan(f'share set --remote-path "/{project_name}/{file_path.name}"')
        if r2.returncode == 0:
            results["baidu"] = _extract_baidu_share(r2.stdout)
    
    # 夸克网盘上传
    print(f"[QUARK] 上传 {file_path.name} ...")
    r = _quark(f'upload "{file_path}" --dir "/{project_name}"')
    if r.returncode == 0:
        # 获取文件 ID 并生成分享链接
        file_id = _extract_quark_file_id(r.stdout)
        if file_id:
            r2 = _quark(f'share "{file_id}"')
            results["quark"] = _extract_quark_share(r2.stdout)
    
    return results


def cmd_batch_upload(trending_file, output_file=None):
    """批量处理 Trending 项目：克隆 → 打包 → 上传 → 分享"""
    if not Path(trending_file).exists():
        print(f"[ERROR] Trending 文件不存在: {trending_file}")
        sys.exit(1)
    
    with open(trending_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    results = []
    for repo in data.get("repositories", []):
        name = repo["name"]
        print(f"\n[PROCESS] {name}")
        
        # 克隆仓库
        tmp_dir = Path(f"/tmp/pipeline_{name}")
        if tmp_dir.exists():
            import shutil
            shutil.rmtree(tmp_dir)
        
        r = subprocess.run(
            f'git clone --depth 1 "{repo["clone_url"]}" "{tmp_dir}"',
            shell=True, capture_output=True, text=True, timeout=60
        )
        
        if r.returncode != 0:
            print(f"  [WARN] 克隆失败: {r.stderr[:200]}")
            continue
        
        # 打包
        zip_path = Path(f"/tmp/{name}.zip")
        import shutil
        shutil.make_archive(str(zip_path.with_suffix("")), "zip", tmp_dir)
        
        # 上传
        drive_result = cmd_upload(str(zip_path) + ".zip", name)
        
        results.append({
            "name": name,
            "full_name": repo["full_name"],
            "stars": repo["stars"],
            "baidu_link": drive_result.get("baidu"),
            "quark_link": drive_result.get("quark"),
        })
        
        # 清理
        import shutil
        shutil.rmtree(tmp_dir, ignore_errors=True)
        Path(str(zip_path) + ".zip").unlink(missing_ok=True)
    
    output = {"processed_at": __import__("datetime").datetime.now().isoformat(), "results": results}
    
    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        print(f"\n[OK] 保存到: {output_file}")
    
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return output


def _extract_baidu_share(output):
    """从 bdpan share 输出中提取分享链接"""
    for line in output.split("\n"):
        if "pan.baidu.com" in line or "链接" in line:
            return line.strip()
    return None


def _extract_quark_file_id(output):
    """从夸克上传输出中提取文件 ID"""
    for line in output.split("\n"):
        if "fid" in line.lower() or "file_id" in line.lower():
            return line.split(":")[-1].strip().strip('"')
    return None


def _extract_quark_share(output):
    """从夸克分享输出中提取链接"""
    for line in output.split("\n"):
        if "pan.quark.cn" in line or "share" in line.lower():
            return line.strip()
    return None


# ── CLI ────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="百度网盘 + 夸克网盘 操作模块")
    subparsers = parser.add_subparsers(dest="command", help="操作命令")
    
    # status
    subparsers.add_parser("status", help="检查双盘登录状态")
    
    # upload
    p_upload = subparsers.add_parser("upload", help="上传文件到双盘")
    p_upload.add_argument("--file", required=True)
    p_upload.add_argument("--project", default="default")
    
    # batch-upload
    p_batch = subparsers.add_parser("batch-upload", help="批量处理 Trending 项目")
    p_batch.add_argument("--trending", required=True, help="trending JSON 文件路径")
    p_batch.add_argument("--output", help="输出 JSON 文件路径")
    
    # quark 子命令
    p_quark = subparsers.add_parser("quark", help="夸克网盘专用操作")
    p_quark.add_argument("action", choices=["status", "login", "upload", "share", "list"])
    p_quark.add_argument("--file", help="文件路径")
    p_quark.add_argument("--file-id", help="文件 ID")
    p_quark.add_argument("--dir", default="/", help="目标目录")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    if args.command == "status":
        cmd_status()
    elif args.command == "upload":
        cmd_upload(args.file, args.project)
    elif args.command == "batch-upload":
        cmd_batch_upload(args.trending, args.output)
    elif args.command == "quark":
        _quark(f'{args.action} {args.file or ""} --dir {args.dir}')


if __name__ == "__main__":
    main()
