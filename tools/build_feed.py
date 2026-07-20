"""从 posts.json 生成 Atom feed (feed.xml)

用法：
  python tools/build_feed.py              # 生成 feed.xml 到项目根目录
  python tools/build_feed.py --dry-run    # 只打印到 stdout，不写文件

生成物部署到 GitHub Pages 后可通过 https://www.owlman.cn/feed.xml 访问。
"""

from __future__ import annotations

import argparse
import io
import json
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path


# ---------------------------------------------------------------------------
# 路径与常量
# ---------------------------------------------------------------------------
TOOLS_DIR = Path(__file__).resolve().parent
PROJECT_DIR = TOOLS_DIR.parent
POSTS_FILE = PROJECT_DIR / "posts.json"
FEED_FILE = PROJECT_DIR / "feed.xml"

SITE_URL = "https://www.owlman.cn"
SITE_TITLE = "凌杰的个人网站"
SITE_AUTHOR = "凌杰 (owlman)"
SITE_DESC = "计算机专业领域的技术作家、翻译与自由软件开发者"


# ---------------------------------------------------------------------------
# Atom feed 生成
# ---------------------------------------------------------------------------
def _text(text: str) -> str:
    """转义 XML 文本内容"""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def build_feed(posts: list[dict]) -> str:
    """从 posts 列表构建 Atom XML 字符串"""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    feed_id = f"{SITE_URL}/"
    updated = _latest_date(posts) or now

    lines = [
        '<?xml version="1.0" encoding="utf-8"?>',
        '<feed xmlns="http://www.w3.org/2005/Atom">',
        f"  <title>{_text(SITE_TITLE)}</title>",
        f"  <subtitle>{_text(SITE_DESC)}</subtitle>",
        f'  <link href="{SITE_URL}/" rel="alternate" type="text/html" />',
        f'  <link href="{SITE_URL}/feed.xml" rel="self" />',
        f"  <id>{feed_id}</id>",
        f"  <updated>{updated}</updated>",
        f"  <author><name>{_text(SITE_AUTHOR)}</name></author>",
    ]

    for p in posts:
        title = _text(p["title"])
        url = p["url"]
        date = p["date"]
        # Atom 要求 ISO 8601 时间戳；只传日期则补上 T00:00:00Z
        entry_updated = f"{date}T00:00:00Z"
        entry_id = url

        summary = ""
        if p.get("summary"):
            summary = _text(p["summary"])

        lines.append("  <entry>")
        lines.append(f"    <title>{title}</title>")
        lines.append(f'    <link href="{url}" rel="alternate" type="text/html" />')
        lines.append(f"    <id>{entry_id}</id>")
        lines.append(f"    <updated>{entry_updated}</updated>")
        if summary:
            lines.append(f"    <summary>{summary}</summary>")
        lines.append("  </entry>")

    lines.append("</feed>")
    return "\n".join(lines) + "\n"


def _latest_date(posts: list[dict]) -> str | None:
    """返回文章列表中最新的一条日期（ISO 8601）"""
    if not posts:
        return None
    latest = max(p["date"] for p in posts if p.get("date"))
    return f"{latest}T00:00:00Z"


# ---------------------------------------------------------------------------
# 入口
# ---------------------------------------------------------------------------
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="从 posts.json 生成 Atom feed")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="只打印 XML 到 stdout，不写文件",
    )
    args = parser.parse_args(argv)

    if not POSTS_FILE.exists():
        print(f"[FAIL] {POSTS_FILE} 不存在，请先抓取文章列表", file=sys.stderr)
        return 1

    try:
        posts = json.loads(POSTS_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"[FAIL] JSON 解析失败: {exc}", file=sys.stderr)
        return 1

    if not isinstance(posts, list):
        print(f"[FAIL] posts.json 内容应为数组", file=sys.stderr)
        return 1

    feed_xml = build_feed(posts)

    if args.dry_run:
        print(feed_xml)
        return 0

    FEED_FILE.write_text(feed_xml, encoding="utf-8")
    print(f"写入 {FEED_FILE}：{len(posts)} 条文章")
    return 0


if __name__ == "__main__":
    sys.exit(main())
