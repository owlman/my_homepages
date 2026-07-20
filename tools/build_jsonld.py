"""从 books.json 生成 JSON-LD Books 片段

Person 节点（含 knowsAbout / sameAs）保留在 index.htm 手写（一年改不了几次，
不适合做数据驱动）；Books 列表从 books.json 自动生成，避免双源 drift。

用法：
  python tools/build_jsonld.py --stdout   # 打印 Books 数组到 stdout
  python tools/build_jsonld.py --update   # 直接改写 index.htm 替换 Books 列表
"""

from __future__ import annotations

import argparse
import io
import json
import re
import sys
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower().replace("-", "") != "utf8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)
if sys.stderr.encoding and sys.stderr.encoding.lower().replace("-", "") != "utf8":
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", line_buffering=True)

TOOLS_DIR = Path(__file__).resolve().parent
PROJECT_DIR = TOOLS_DIR.parent
BOOKS_FILE = PROJECT_DIR / "books.json"
INDEX_FILE = PROJECT_DIR / "index.htm"
PERSON_ID = "https://www.owlman.cn/#owlman"

# 匹配 JSON-LD 内整个 Books 数组：{ "@type": "Book", ... }, ... } 的逐行形式
BOOKS_LINE_PATTERN = re.compile(
    r'^\s*\{\s*"@type":\s*"Book",\s*.*?\}\s*,?\s*$',
    re.M,
)


def build_books_entries(books: list[dict]) -> list[str]:
    """根据 type 字段决定 author/translator，每本书一行 JSON"""
    lines: list[str] = []
    for b in books:
        role_key = "author" if b.get("type") == "original" else "translator"
        entry = {
            "@type": "Book",
            "name": b["title"],
            role_key: {"@id": PERSON_ID},
            "url": b["url"],
            "inLanguage": "zh-CN",
        }
        # 末尾不加逗号（JSON 严格不允许尾逗号），先全部加，最后一个去逗号
        lines.append("\t\t\t\t" + json.dumps(entry, ensure_ascii=False) + ",")
    if lines:
        lines[-1] = lines[-1].rstrip(",")
    return lines


def render_books_block(books: list[dict]) -> str:
    """生成 index.htm 中 79-93 行那个 Books 列表的整块文本"""
    return "\n".join(build_books_entries(books))


def update_index(books: list[dict]) -> tuple[bool, str]:
    """替换 index.htm 中的 Books 列表，返回 (是否修改, 改后内容)"""
    if not INDEX_FILE.exists():
        return False, f"index.htm 缺失: {INDEX_FILE}"

    html = INDEX_FILE.read_text(encoding="utf-8")
    matches = list(BOOKS_LINE_PATTERN.finditer(html))
    if len(matches) != 15:
        # 容错：JSON-LD 应该有 15 本书
        return False, f"找到 {len(matches)} 个 Book 行（期望 15），文件结构可能已变，请手动检查"

    start = matches[0].start()
    end = matches[-1].end()
    new_block = render_books_block(books)

    new_html = html[:start] + new_block + html[end:]
    INDEX_FILE.write_text(new_html, encoding="utf-8")
    return True, f"替换 {len(matches)} 行 Books"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="生成 JSON-LD Books 片段")
    parser.add_argument("--stdout", action="store_true", help="打印到 stdout，不写文件")
    parser.add_argument("--update", action="store_true", help="直接改写 index.htm")
    args = parser.parse_args(argv)

    books = json.loads(BOOKS_FILE.read_text(encoding="utf-8"))

    if args.stdout:
        print(render_books_block(books))
        return 0

    if args.update:
        ok, msg = update_index(books)
        if not ok:
            print(f"[FAIL] {msg}", file=sys.stderr)
            return 1
        print(f"[OK] index.htm: {msg}")
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())