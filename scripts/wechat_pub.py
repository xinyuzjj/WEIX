#!/usr/bin/env python3
"""
微信公众号草稿箱发布模块
=========================
将 Markdown 文章转换为微信格式并推送到公众号草稿箱。
需要配置 WECHAT_APPID 和 WECHAT_SECRET。

用法:
  python wechat_pub.py --article article.md --config config.json
  python wechat_pub.py --article article.md --appid xxx --secret xxx
"""

import argparse
import json
import sys
from pathlib import Path


def markdown_to_wechat_html(md_content):
    """
    将 Markdown 转换为微信公众号兼容的 HTML。
    
    微信公众号只支持有限的 HTML 标签:
    - 标题: h1-h6
    - 段落: p
    - 加粗: strong
    - 斜体: em
    - 链接: a
    - 代码: pre > code
    - 图片: img
    - 列表: ul/ol > li
    - 引用: blockquote
    """
    # 简单 Markdown → HTML 转换（生产环境建议用 markdown 库）
    lines = md_content.split("\n")
    html_parts = []
    in_code_block = False
    code_content = []
    in_list = False
    list_type = None
    list_items = []
    
    for line in lines:
        # 代码块
        if line.strip().startswith("```"):
            if in_code_block:
                code = "\n".join(code_content)
                html_parts.append(f'<pre><code>{_escape_html(code)}</code></pre>')
                code_content = []
                in_code_block = False
            else:
                in_code_block = True
            continue
        
        if in_code_block:
            code_content.append(line)
            continue
        
        # 空行 — 结束列表
        if not line.strip():
            if in_list and list_items:
                html_parts.append(_render_list(list_type, list_items))
                list_items = []
                in_list = False
            continue
        
        # 标题
        if line.startswith("# "):
            html_parts.append(f'<h1>{_process_inline(line[2:])}</h1>')
        elif line.startswith("## "):
            html_parts.append(f'<h2>{_process_inline(line[3:])}</h2>')
        elif line.startswith("### "):
            html_parts.append(f'<h3>{_process_inline(line[4:])}</h3>')
        # 分隔线
        elif line.strip() in ("---", "***", "___"):
            html_parts.append('<hr/>')
        # 无序列表
        elif line.strip().startswith("- ") or line.strip().startswith("* "):
            if not in_list or list_type != "ul":
                if in_list:
                    html_parts.append(_render_list(list_type, list_items))
                    list_items = []
                in_list = True
                list_type = "ul"
            list_items.append(line.strip()[2:])
        # 有序列表
        elif line.strip() and line.strip()[0].isdigit() and ". " in line.strip()[:4]:
            if not in_list or list_type != "ol":
                if in_list:
                    html_parts.append(_render_list(list_type, list_items))
                    list_items = []
                in_list = True
                list_type = "ol"
            content = line.strip().split(". ", 1)[1]
            list_items.append(content)
        # 引用
        elif line.strip().startswith("> "):
            html_parts.append(f'<blockquote><p>{_process_inline(line.strip()[2:])}</p></blockquote>')
        # 普通段落
        else:
            if in_list:
                html_parts.append(_render_list(list_type, list_items))
                list_items = []
                in_list = False
            html_parts.append(f'<p>{_process_inline(line)}</p>')
    
    # 收尾列表
    if in_list and list_items:
        html_parts.append(_render_list(list_type, list_items))
    
    return "\n".join(html_parts)


def _process_inline(text):
    """处理行内格式：加粗、斜体、链接、行内代码"""
    import re
    
    # 行内代码 `code`
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    # 加粗 **bold**
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    # 斜体 *italic*
    text = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<em>\1</em>', text)
    # 链接 [text](url)
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)
    
    return text


def _render_list(list_type, items):
    """渲染列表"""
    tag = list_type
    items_html = "".join(f"<li>{_process_inline(item)}</li>" for item in items)
    return f"<{tag}>{items_html}</{tag}>"


def _escape_html(text):
    """HTML 转义"""
    return (text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))


def publish_to_wechat(article_path, appid, secret):
    """
    发布文章到微信公众号草稿箱。
    
    调用微信 API:
    1. POST https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={appid}&secret={secret}
    2. POST https://api.weixin.qq.com/cgi-bin/draft/add?access_token={token}
    """
    import httpx
    
    if not Path(article_path).exists():
        print(f"[ERROR] 文章文件不存在: {article_path}")
        sys.exit(1)
    
    with open(article_path, "r", encoding="utf-8") as f:
        md_content = f.read()
    
    # 提取标题（第一个 # 行）
    title = "GitHub Trending 深度分析"
    lines = md_content.split("\n")
    for line in lines:
        if line.startswith("# "):
            title = line[2:].strip()
            break
    
    # 转换为微信 HTML
    html_content = markdown_to_wechat_html(md_content)
    
    # 获取 access_token
    print("[WECHAT] 获取 access_token ...")
    try:
        resp = httpx.get(
            "https://api.weixin.qq.com/cgi-bin/token",
            params={
                "grant_type": "client_credential",
                "appid": appid,
                "secret": secret
            },
            timeout=30
        )
        data = resp.json()
        
        if "errcode" in data and data["errcode"] != 0:
            print(f"[ERROR] 获取 token 失败: {data.get('errmsg', data)}")
            sys.exit(1)
        
        access_token = data["access_token"]
        print(f"[OK] Token 获取成功")
        
    except Exception as e:
        print(f"[ERROR] 网络请求失败: {e}")
        sys.exit(1)
    
    # 添加到草稿箱
    print("[WECHAT] 添加到草稿箱 ...")
    draft_data = {
        "articles": [{
            "title": title,
            "author": "WorkBuddy",
            "digest": lines[2] if len(lines) > 2 else title,
            "content": html_content,
            "content_source_url": "",
            "need_open_comment": 0,
            "only_fans_can_comment": 0,
        }]
    }
    
    try:
        resp = httpx.post(
            f"https://api.weixin.qq.com/cgi-bin/draft/add",
            params={"access_token": access_token},
            json=draft_data,
            timeout=30
        )
        result = resp.json()
        
        if result.get("errcode") == 0:
            media_id = result.get("media_id", "unknown")
            print(f"[OK] 已发布到草稿箱 (media_id: {media_id})")
            return {"status": "success", "media_id": media_id}
        else:
            print(f"[ERROR] 发布失败: {result}")
            sys.exit(1)
            
    except Exception as e:
        print(f"[ERROR] 发布请求失败: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="微信公众号草稿箱发布")
    parser.add_argument("--article", required=True, help="文章 Markdown 文件路径")
    parser.add_argument("--config", help="配置文件路径（包含 WECHAT_APPID/SECRET）")
    parser.add_argument("--appid", help="微信公众号 APPID（或从 config 读取）")
    parser.add_argument("--secret", help="微信公众号 SECRET（或从 config 读取）")
    args = parser.parse_args()
    
    # 读取配置
    appid = args.appid
    secret = args.secret
    
    if args.config and Path(args.config).exists():
        with open(args.config, "r", encoding="utf-8") as f:
            config = json.load(f)
        appid = appid or config.get("WECHAT_APPID", "")
        secret = secret or config.get("WECHAT_SECRET", "")
    
    if not appid or not secret:
        print("[ERROR] 请提供 WECHAT_APPID 和 WECHAT_SECRET")
        print("方式1: --appid xxx --secret xxx")
        print("方式2: 在 config.json 中设置 WECHAT_APPID 和 WECHAT_SECRET")
        sys.exit(1)
    
    publish_to_wechat(args.article, appid, secret)


if __name__ == "__main__":
    main()
