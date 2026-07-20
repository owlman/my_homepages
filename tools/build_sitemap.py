"""从 books.json + posts.json 合成 sitemap.xml

输出 schema 0.9，包含：
  - 首页（priority 1.0, monthly）
  - 每本书的豆瓣 URL（priority 0.7, monthly）
  - 每篇博客的 cnblogs URL（priority 0.8, weekly）

用法：
  python tools/build_sitemap.py                 # 默认写 D:/MyHome/sitemap.xml
  python tools/build_sitemap.py --output path   # 自定义输出
  python tools/build_sitemap.py --stdout        # 打印到 stdout
"""

from __future__ import annotations

import argparse
import io
import json
import sys
from pathlib import Path

# UTF-8 兜底（与本项目其他工具保持一致）
if sys.stdout.encoding and sys.stdout.encoding.lower().replace("-", "") != "utf8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)
if sys.stderr.encoding and sys.stderr.encoding.lower().replace("-", "") != "utf8":
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", line_buffering=True)

TOOLS_DIR = Path(__file__).resolve().parent
PROJECT_DIR = TOOLS_DIR.parent
SITE_BASE = "https://www.owlman.cn"
DEFAULT_OUTPUT = PROJECT_DIR / "sitemap.xml"


def _entry(loc: str, changefreq: str, priority: str) -> str:
    return (
        "    <url>\n"
        f"        <loc>{loc}</loc>\n"
        f"        <changefreq>{changefreq}</changefreq>\n"
        f"        <priority>{priority}</priority>\n"
        "    </url>"
    )


def build_xml(books: list[dict], posts: list[dict]) -> str:
    parts: list[str] = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
        _entry(f"{SITE_BASE}/", "monthly", "1.0"),
    ]
    # 博客文章优先级略高（更新更频繁，搜索引擎更重视）
    for p in sorted(posts, key=lambda x: x["date"], reverse=True):
        parts.append(_entry(p["url"], "weekly", "0.8"))
    # 书籍：豆瓣 URL，按 year 倒序
    for b in sorted(books, key=lambda x: x.get("year", 0), reverse=True):
        parts.append(_entry(b["url"], "monthly", "0.7"))
    parts.append("</urlset>")
    return "\n".join(parts) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="合成 sitemap.xml")
    parser.add_argument("--stdout", action="store_true", help="打印到 stdout 而不是写文件")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help=f"输出路径（默认: {DEFAULT_OUTPUT}）")
    args = parser.parse_args(argv)

    try:
        books = json.loads((PROJECT_DIR / "books.json").read_text(encoding="utf-8"))
        posts = json.loads((PROJECT_DIR / "posts.json").read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"[FAIL] 读取数据失败: {exc}", file=sys.stderr)
        return 1

    xml = build_xml(books, posts)
    if args.stdout:
        sys.stdout.write(xml)
        return 0

    Path(args.output).write_text(xml, encoding="utf-8")
    url_count = xml.count("<url>")
    print(f"写入 {args.output}：{url_count} 条 URL（{len(books)} 书 + {len(posts)} 文章 + 1 首页）")
    return 0


if __name__ == "__main__":
    sys.exit(main())