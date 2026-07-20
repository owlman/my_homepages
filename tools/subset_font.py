"""下载并子集化 Noto Serif SC 字体（400 + 700）

利用 Google Fonts API v1 的 text= 参数做服务端子集化，
下载预子集 TTF → 本地转 woff2 → 输出到 vendor/fonts/。

依赖：fontTools（pip install fonttools brotli）

用法：
  python tools/subset_font.py                 # 下载 + 子集化 + 输出到 vendor/fonts/
  python tools/subset_font.py --dry-run       # 只统计字符，不下载
"""

from __future__ import annotations

import argparse
import io
import re
import sys
import urllib.parse
from pathlib import Path

import requests
from fontTools.ttLib import TTFont

if sys.stdout.encoding and sys.stdout.encoding.lower().replace("-", "") != "utf8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)
if sys.stderr.encoding and sys.stderr.encoding.lower().replace("-", "") != "utf8":
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", line_buffering=True)

TOOLS_DIR = Path(__file__).resolve().parent
PROJECT_DIR = TOOLS_DIR.parent
FONTS_DIR = PROJECT_DIR / "vendor" / "fonts"

GF_V1_URL = "https://fonts.googleapis.com/css?family=Noto+Serif+SC:400,700&text={text}"

SOURCE_FILES = [
    "index.htm", "css/style.css", "js/main.js",
    "books.json", "posts.json", "MAINTENANCE.md", "README.md",
    "data/social-links.json", "sitemap.xml",
]

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36"
TIMEOUT = 120


def collect_characters() -> str:
    """收集所有源文件用到的唯一字符"""
    chars: set[str] = set()
    for rel in SOURCE_FILES:
        path = PROJECT_DIR / rel
        if not path.exists():
            print(f"[warn] 跳过缺失: {rel}", file=sys.stderr)
            continue
        text = path.read_text(encoding="utf-8")
        for ch in text:
            cp = ord(ch)
            if cp < 0x20 or 0xD800 <= cp <= 0xDFFF or 0xE000 <= cp <= 0xF8FF:
                continue
            chars.add(ch)
    return "".join(sorted(chars, key=ord))


def _fetch_ttf_urls(text: str) -> list[tuple[int, str]]:
    """用 text= 请求 Google Fonts，返回 [(weight, ttf_url), ...]"""
    url = GF_V1_URL.format(text=urllib.parse.quote(text))
    print(f"请求 Google Fonts API（{len(text)} 字符）……")
    resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT)
    resp.raise_for_status()
    css = resp.text
    results: list[tuple[int, str]] = []
    for block in css.split("@font-face")[1:]:
        w = re.search(r"font-weight:\s*(\d+)", block)
        u = re.search(r"url\(([^)]+)\)", block)
        if w and u:
            results.append((int(w.group(1)), u.group(1)))
    return results


def _download_and_convert(url: str, weight: int, chars: str) -> Path:
    """下载 TTF → 子集化校验 → 另存为 woff2"""
    print(f"下载 weight {weight} …")
    resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT)
    resp.raise_for_status()
    orig_kb = len(resp.content) // 1024

    ttf_path = PROJECT_DIR / f"._notoserif_{weight}.ttf"
    ttf_path.write_bytes(resp.content)

    font = TTFont(str(ttf_path))
    font.flavor = "woff2"
    out = FONTS_DIR / f"noto-serif-sc-{weight}.woff2"
    font.save(str(out))

    woff_kb = out.stat().st_size // 1024
    # 校验覆盖度
    cmap = font.getBestCmap() or {}
    missing = [c for c in chars if ord(c) not in cmap]
    if missing:
        print(f"  [warn] {len(missing)} 个字符缺失: {''.join(missing[:20])}", file=sys.stderr)

    ttf_path.unlink()
    print(f"  → TTF {orig_kb} KB → woff2 {woff_kb} KB")
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="子集化 Noto Serif SC 字体")
    parser.add_argument("--dry-run", action="store_true", help="只统计字符，不下载")
    args = parser.parse_args(argv)

    chars = collect_characters()
    cjk = [c for c in chars if 0x4E00 <= ord(c) <= 0x9FFF]
    latin = [c for c in chars if c.isascii() and c.isalpha()]
    print(f"字符集: {len(chars)} 唯一（CJK {len(cjk)} + Latin {len(latin)} + 其他 {len(chars) - len(cjk) - len(latin)}）")

    if args.dry_run:
        return 0

    FONTS_DIR.mkdir(parents=True, exist_ok=True)

    try:
        urls = _fetch_ttf_urls(chars)
    except requests.RequestException as exc:
        print(f"[FAIL] Google Fonts API 失败: {exc}", file=sys.stderr)
        return 1

    if not urls:
        print("[FAIL] 未找到字体 URL", file=sys.stderr)
        return 1

    for weight, url in sorted(urls):
        _download_and_convert(url, weight, chars)

    total_kb = sum(f.stat().st_size for f in FONTS_DIR.glob("*.woff2")) // 1024
    print(f"\n完成: {len(urls)} 个字体 → {FONTS_DIR}（合计 {total_kb} KB）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
