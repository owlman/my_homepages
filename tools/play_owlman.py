"""owlman.cn 专用评估工具

四步校验：
  1. JSON Schema 校验 —— books.json / posts.json / social-links.json
  2. 文件存在性校验 —— 封面图片是否全部就位
  3. sitemap 一致性 —— 已存在的 sitemap.xml 是否与 books/posts 同步
  4. Playwright 线上渲染 —— 抓取 owlman.cn 并输出 Markdown 摘要 + 全页截图

用法：
  python tools/play_owlman.py [--output-dir out] [--url https://owlman.cn]
  python tools/play_owlman.py --fetch            # 先用 fetch_posts.py 同步博客园，再校验
  python tools/play_owlman.py --skip-live        # 仅做本地校验（不开浏览器）
"""

from __future__ import annotations

import argparse
import io
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import jsonschema
from playwright.sync_api import sync_playwright

# ---------------------------------------------------------------------------
# Windows 下 Python 子进程 stdout 默认 GBK，Claude Code 任务文件按 GBK 落盘
# 会让 print 出来的中文变成 "����" 乱码。这里把 stdout/stderr 强制改回 UTF-8，
# 输出 JSON 文件、Markdown 摘要也一律 UTF-8，下游渲染就不会再串码。
# ---------------------------------------------------------------------------
if sys.stdout.encoding and sys.stdout.encoding.lower().replace("-", "") != "utf8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)
if sys.stderr.encoding and sys.stderr.encoding.lower().replace("-", "") != "utf8":
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", line_buffering=True)

# ---------------------------------------------------------------------------
# 路径常量 —— 脚本自动推断项目根（tools/ ..）
# ---------------------------------------------------------------------------
TOOLS_DIR = Path(__file__).resolve().parent
PROJECT_DIR = TOOLS_DIR.parent
DEFAULT_OUT = PROJECT_DIR / "out"

SCHEMAS = {
    "books": PROJECT_DIR / "books.schema.json",
    "posts": PROJECT_DIR / "posts.schema.json",
    "social-links": PROJECT_DIR / "data" / "social-links.schema.json",
}
DATA_FILES = {
    "books": PROJECT_DIR / "books.json",
    "posts": PROJECT_DIR / "posts.json",
    "social-links": PROJECT_DIR / "data" / "social-links.json",
}

URL_DEFAULT = "https://owlman.cn"


# ===================================================================
# 阶段 1：JSON Schema 校验
# ===================================================================
def validate_schemas() -> dict[str, list[str]]:
    """对每份数据文件跑 schema；返回 {data_name: [error_msg, ...]}"""
    failures: dict[str, list[str]] = {}
    for name in ("books", "posts", "social-links"):
        data_path = DATA_FILES[name]
        schema_path = SCHEMAS[name]
        if not data_path.exists():
            failures[name] = [f"数据文件缺失: {data_path}"]
            continue
        if not schema_path.exists():
            failures[name] = [f"Schema 文件缺失: {schema_path}"]
            continue
        try:
            data = json.loads(data_path.read_text("utf-8"))
            schema = json.loads(schema_path.read_text("utf-8"))
            jsonschema.validate(data, schema)
        except json.JSONDecodeError as exc:
            failures[name] = [f"JSON 解析失败: {exc}"]
        except jsonschema.ValidationError as exc:
            failures[name] = [f"Schema 校验失败: {exc.message}"]
    return failures


# ===================================================================
# 阶段 2：封面文件存在性校验
# ===================================================================
def check_covers() -> list[str]:
    """遍历 books.json 的 cover 字段，返回缺失路径列表"""
    missing: list[str] = []
    try:
        books = json.loads(DATA_FILES["books"].read_text("utf-8"))
    except Exception as exc:
        return [f"无法读取 books.json: {exc}"]
    for entry in books:
        cover = entry.get("cover", "")
        if not (PROJECT_DIR / cover).exists():
            missing.append(cover)
    return missing


# ===================================================================
# 阶段 3：sitemap 与 books/posts 一致性校验
# ===================================================================
def check_sitemap() -> list[str]:
    """检查 sitemap.xml 是否包含 books.json + posts.json 的所有 URL"""
    sitemap_path = PROJECT_DIR / "sitemap.xml"
    if not sitemap_path.exists():
        return [f"sitemap.xml 缺失: {sitemap_path}"]
    try:
        books = json.loads(DATA_FILES["books"].read_text("utf-8"))
        posts = json.loads(DATA_FILES["posts"].read_text("utf-8"))
    except Exception as exc:
        return [f"无法读取数据文件: {exc}"]

    xml = sitemap_path.read_text("utf-8")
    missing: list[str] = []
    for p in posts:
        if p["url"] not in xml:
            missing.append(f"博客未在 sitemap: {p['url']}")
    for b in books:
        if b["url"] not in xml:
            missing.append(f"书籍未在 sitemap: {b['url']}")
    return missing


# ===================================================================
# 阶段 3：Playwright 线上渲染
# ===================================================================
def render_live(
    url: str,
    out_dir: Path,
) -> dict:
    """抓取线上页面，输出 Markdown 摘要 + 全页截图；返回统计字典"""
    out_dir.mkdir(parents=True, exist_ok=True)
    md_path = out_dir / "render.md"
    shot_path = out_dir / "full.png"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            viewport={"width": 1440, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/126.0.0.0 Safari/537.36"
            ),
        )
        page = ctx.new_page()
        try:
            page.goto(url, wait_until="networkidle", timeout=45000)
        except Exception as exc:
            print(f"[warn] networkidle timeout: {exc}", file=sys.stderr)
            page.goto(url, wait_until="domcontentloaded", timeout=45000)

        page.wait_for_timeout(2500)

        # 基础统计
        title = page.title()
        h1 = page.locator("h1").all_inner_texts()
        h2 = page.locator("h2").all_inner_texts()
        h3 = page.locator("h3").all_inner_texts()
        links = page.locator("a").count()
        imgs = page.locator("img").count()
        articles = page.locator("article").count()

        page.screenshot(path=str(shot_path), full_page=True)

        # DOM → Markdown 摘要
        body_text = page.evaluate(
            """() => {
                const skip = new Set(['SCRIPT','STYLE','NOSCRIPT','SVG','PATH']);
                const walk = (el) => {
                    if (!el) return '';
                    const tag = el.tagName;
                    if (skip.has(tag)) return '';
                    let out = '';
                    if (/^H[1-6]$/.test(tag)) {
                        out += '\\n' + '#'.repeat(parseInt(tag[1])) + ' ' + el.innerText.trim() + '\\n';
                    } else if (tag === 'P') {
                        out += '\\n' + el.innerText.trim() + '\\n';
                    } else if (tag === 'LI') {
                        out += '\\n- ' + el.innerText.trim();
                    } else if (tag === 'A') {
                        const href = el.getAttribute('href') || '';
                        out += '\\n[' + el.innerText.trim() + '](' + href + ')';
                    } else if (tag === 'IMG') {
                        out += '\\n![' + (el.getAttribute('alt') || '') + '](' + (el.getAttribute('src') || '') + ')';
                    } else if (tag === 'HR') {
                        out += '\\n---\\n';
                    }
                    for (const child of el.children) out += walk(child);
                    return out;
                };
                return walk(document.body).replace(/\\n{3,}/g, '\\n\\n').trim();
            }"""
        )

        header = (
            f"# owlman.cn 渲染捕获\n\n"
            f"- URL: {url}\n"
            f"- 抓取时间: {datetime.now(timezone.utc).isoformat()}\n"
            f"- title: {title}\n"
            f"- h1: {h1}\n"
            f"- h2 ({len(h2)}): {h2}\n"
            f"- h3 ({len(h3)}): {h3[:12]}\n"
            f"- 链接数: {links}, 图片数: {imgs}, article 数: {articles}\n"
            f"- 截图: {shot_path}\n\n"
            "---\n\n"
        )
        md_path.write_text(header + body_text, encoding="utf-8")
        browser.close()

    return {
        "url": url,
        "title": title,
        "h1": h1,
        "h2": h2,
        "h3_count": len(h3),
        "links": links,
        "imgs": imgs,
        "articles": articles,
        "md": str(md_path),
        "screenshot": str(shot_path),
    }


# ===================================================================
# 阶段 4：汇总报告
# ===================================================================
def print_report(
    schema_failures: dict[str, list[str]],
    missing_covers: list[str],
    sitemap_issues: list[str],
    live: dict | None,
    elapsed_s: float,
) -> int:
    """打印结构化报告，返回退出码（0 = 全部通过）"""
    issues = sum(len(v) for v in schema_failures.values()) + len(missing_covers) + len(sitemap_issues)
    lines: list[str] = []
    lines.append("=" * 62)
    lines.append("  owlman.cn 评估报告")
    lines.append(f"  {datetime.now(timezone.utc).isoformat()}")
    lines.append("=" * 62)

    # Schema
    lines.append("\n[1] JSON Schema 校验")
    for name in ("books", "posts", "social-links"):
        errs = schema_failures.get(name, [])
        status = "PASS" if not errs else f"FAIL ({len(errs)} 项)"
        lines.append(f"    {name}: {status}")
        for e in errs:
            lines.append(f"      -> {e}")

    # 封面
    lines.append("\n[2] 书籍封面文件")
    if not missing_covers:
        lines.append("    PASS  全部封面就位")
    else:
        for c in missing_covers:
            lines.append(f"    FAIL  缺失: {c}")

    # sitemap
    lines.append("\n[3] sitemap.xml 与数据一致性")
    if not sitemap_issues:
        lines.append("    PASS  sitemap 与 books/posts 完全同步")
    else:
        for s in sitemap_issues:
            lines.append(f"    FAIL  {s}")

    # 线上渲染
    lines.append("\n[4] Playwright 线上渲染")
    if live is None:
        lines.append("    SKIP  未执行（Playwright 不可用）")
    else:
        lines.append(f"    URL:       {live['url']}")
        lines.append(f"    title:     {live['title']}")
        lines.append(f"    h1:        {live['h1']}")
        lines.append(f"    h2 ({len(live['h2'])}):   {live['h2']}")
        lines.append(f"    h3 数量:   {live['h3_count']}")
        lines.append(f"    链接数:    {live['links']}")
        lines.append(f"    图片数:    {live['imgs']}")
        lines.append(f"    摘要文件:  {live['md']}")
        lines.append(f"    截图文件:  {live['screenshot']}")

    lines.append(f"\n耗时: {elapsed_s:.1f}s")
    lines.append(f"问题总数: {issues}")
    lines.append("=" * 62)

    print("\n".join(lines))
    return 0 if issues == 0 else 1


# ===================================================================
# 入口
# ===================================================================
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="owlman.cn 评估工具")
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUT),
        help=f"输出目录（默认: {DEFAULT_OUT}）",
    )
    parser.add_argument(
        "--url",
        default=URL_DEFAULT,
        help=f"线上地址（默认: {URL_DEFAULT}）",
    )
    parser.add_argument(
        "--skip-live",
        action="store_true",
        help="跳过 Playwright 线上渲染（仅做本地校验）",
    )
    parser.add_argument(
        "--fetch",
        action="store_true",
        help="先调用 tools/fetch_posts.py 同步博客园文章列表，再做后续校验",
    )
    parser.add_argument(
        "--fetch-pages",
        type=int,
        default=1,
        help="配合 --fetch：抓取前 N 页（默认 1，转交 fetch_posts.py）",
    )
    args = parser.parse_args(argv)

    import time
    start = time.monotonic()

    print(f"项目根: {PROJECT_DIR}")
    print(f"输出目录: {args.output_dir}")

    # ---- 抓取博客园（如指定） ----
    if args.fetch:
        fetch_cmd = [
            sys.executable,
            str(TOOLS_DIR / "fetch_posts.py"),
            "--pages",
            str(args.fetch_pages),
        ]
        print(f"[fetch] 运行: {' '.join(fetch_cmd)}")
        try:
            subprocess.run(fetch_cmd, check=True, cwd=str(PROJECT_DIR))
        except subprocess.CalledProcessError as exc:
            print(f"[FAIL] fetch_posts.py 退出码 {exc.returncode}", file=sys.stderr)
            return exc.returncode or 1

    # ---- Schema ----
    schema_failures = validate_schemas()

    # ---- 封面 ----
    missing_covers = check_covers()

    # ---- sitemap ----
    sitemap_issues = check_sitemap()

    # ---- 线上渲染 ----
    live: dict | None = None
    if not args.skip_live:
        try:
            live = render_live(args.url, Path(args.output_dir))
        except Exception as exc:
            print(f"[warn] Playwright 失败: {exc}", file=sys.stderr)

    elapsed = time.monotonic() - start
    return print_report(schema_failures, missing_covers, sitemap_issues, live, elapsed)


if __name__ == "__main__":
    sys.exit(main())
