"""抓取博客园 cnblogs.com/owlman/ 文章列表，生成 posts.json

用法：
  python tools/fetch_posts.py                 # 抓首页 10 篇，直接写 MyHome/posts.json
  python tools/fetch_posts.py --dry-run       # 只打印 JSON 到 stdout，不写文件
  python tools/fetch_posts.py --pages 2       # 抓首页 + 第 2 页（按发布时间并集去重）
  python tools/fetch_posts.py --url <URL>     # 自定义博客首页

依赖：requests（pyproject/requirements 视项目情况安装）
"""

from __future__ import annotations

import argparse
import io
import json
import re
import sys
from pathlib import Path

import requests

# ---------------------------------------------------------------------------
# Windows 下 Python 子进程 stdout 默认 GBK，会让中文打印乱码。
# 与 tools/play_owlman.py 保持一致的兜底。
# ---------------------------------------------------------------------------
if sys.stdout.encoding and sys.stdout.encoding.lower().replace("-", "") != "utf8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)
if sys.stderr.encoding and sys.stderr.encoding.lower().replace("-", "") != "utf8":
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", line_buffering=True)

# ---------------------------------------------------------------------------
# 路径与常量
# ---------------------------------------------------------------------------
TOOLS_DIR = Path(__file__).resolve().parent
PROJECT_DIR = TOOLS_DIR.parent
POSTS_FILE = PROJECT_DIR / "posts.json"
POSTS_SCHEMA = PROJECT_DIR / "posts.schema.json"
DEFAULT_BLOG_URL = "https://www.cnblogs.com/owlman/"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0.0.0 Safari/537.36"
)
REQUEST_TIMEOUT = 20  # seconds


# ---------------------------------------------------------------------------
# 抓取与解析
# ---------------------------------------------------------------------------
def fetch_page(blog_url: str, page: int) -> str:
    """请求博客园第 N 页 HTML 文本。首页 page=1"""
    resp = requests.get(
        blog_url,
        params={"page": page},
        headers={"User-Agent": USER_AGENT},
        timeout=REQUEST_TIMEOUT,
    )
    resp.raise_for_status()
    # 显式按 UTF-8 解码：cnblogs meta charset=utf-8，requests r.encoding 默认按 ISO-8859-1，
    # 不显式指定会把中文显示成乱码。
    resp.encoding = "utf-8"
    return resp.text


def _normalize_title(raw: str) -> str:
    """去 HTML 标签、折叠空白"""
    text = re.sub(r"<[^>]+>", "", raw)
    return re.sub(r"\s+", " ", text).strip()


def parse_posts(html: str) -> list[dict]:
    """从一篇列表页 HTML 中解析出 {title, url, date} 三元组列表。

    解析策略：
      - 标题 + URL：匹配 <a class="postTitle2 ..." href="...">...</a>
      - 日期：匹配 posted @ YYYY-MM-DD HH:MM，取日期部分
      - 两者在 HTML 中顺序一致，按位置 zip 配对
    """
    title_pattern = re.compile(
        r'<a[^>]*class="[^"]*\bpostTitle2\b[^"]*"[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
        re.S,
    )
    posted_pattern = re.compile(r"posted\s*@\s*(\d{4}-\d{2}-\d{2})\s+\d{2}:\d{2}")

    hrefs_titles = [
        (m.group(1), _normalize_title(m.group(2)))
        for m in title_pattern.finditer(html)
    ]
    dates = posted_pattern.findall(html)

    if not hrefs_titles:
        raise RuntimeError(
            "博客园页面未匹配到任何 postTitle2，可能页面结构已变，请检查选择器"
        )
    if len(hrefs_titles) != len(dates):
        raise RuntimeError(
            f"标题数 {len(hrefs_titles)} 与日期数 {len(dates)} 不一致，"
            f"页面结构可能已变，请检查"
        )

    return [
        {"title": title, "url": url, "date": date}
        for (url, title), date in zip(hrefs_titles, dates)
    ]


def fetch_all(blog_url: str, pages: int) -> list[dict]:
    """抓前 N 页，按 url 去重合并后按 date 降序排序"""
    seen: dict[str, dict] = {}
    for page in range(1, pages + 1):
        html = fetch_page(blog_url, page)
        for entry in parse_posts(html):
            seen[entry["url"]] = entry  # 去重，保留首次出现的（更靠前）
    posts = sorted(seen.values(), key=lambda x: x["date"], reverse=True)
    return posts


# ---------------------------------------------------------------------------
# 校验
# ---------------------------------------------------------------------------
def validate(posts: list[dict]) -> None:
    """用 posts.schema.json 校验列表。失败抛 jsonschema.ValidationError"""
    import jsonschema
    schema = json.loads(POSTS_SCHEMA.read_text(encoding="utf-8"))
    jsonschema.validate(posts, schema)


# ---------------------------------------------------------------------------
# 入口
# ---------------------------------------------------------------------------
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="抓取博客园文章列表，更新 posts.json")
    parser.add_argument(
        "--url",
        default=DEFAULT_BLOG_URL,
        help=f"博客首页 URL（默认: {DEFAULT_BLOG_URL}）",
    )
    parser.add_argument(
        "--pages",
        type=int,
        default=1,
        help="抓取前 N 页（默认 1，约 10 篇）",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="只打印 JSON 到 stdout，不写文件",
    )
    args = parser.parse_args(argv)

    print(f"目标: {args.url}")
    print(f"抓取前 {args.pages} 页")

    try:
        posts = fetch_all(args.url, args.pages)
    except requests.RequestException as exc:
        print(f"[FAIL] 网络请求失败: {exc}", file=sys.stderr)
        return 1
    except RuntimeError as exc:
        print(f"[FAIL] {exc}", file=sys.stderr)
        return 1

    if not posts:
        print("[FAIL] 抓取结果为空", file=sys.stderr)
        return 1

    # schema 校验只在要写文件时跑，dry-run 不必
    if not args.dry_run:
        try:
            validate(posts)
        except Exception as exc:
            print(f"[FAIL] schema 校验失败: {exc}", file=sys.stderr)
            return 1

    rendered = json.dumps(posts, ensure_ascii=False, indent=2)

    if args.dry_run:
        print(rendered)
        return 0

    POSTS_FILE.write_text(rendered + "\n", encoding="utf-8")
    print(f"写入 {POSTS_FILE}：{len(posts)} 条")
    if posts:
        print(f"日期范围: {posts[-1]['date']} ~ {posts[0]['date']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
