#!/usr/bin/env bash
# MyHome 静态站预提交校验：CNAME BOM、JSON Schema、封面文件存在性、字段对齐。
# 用法：bash tools/check.sh   或  作为 pre-push 钩子自动触发。

set -e

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || echo ".")"
cd "$REPO_ROOT"

err() { echo "[FAIL] check.sh: $1" >&2; exit 1; }
ok()  { echo "[PASS] $1"; }

# ---------- 1. CNAME BOM 检查 ----------
if [ -f CNAME ]; then
  if head -c 3 CNAME | od -An -tx1 | tr -d ' \n' | grep -q 'efbbbf'; then
    err "CNAME 含 UTF-8 BOM（GitHub Pages 会失败）"
  fi
  ok "CNAME 干净"
fi

# ---------- 2. JSON Schema 校验 ----------
for pair in "books.json:books.schema.json" "posts.json:posts.schema.json" "data/social-links.json:social-links.schema.json"; do
  file="${pair%%:*}"
  schema="${pair##*:}"
  [ -f "$file" ] || continue
  [ -f "$schema" ] || continue
  python - "$file" "$schema" <<'PY'
import json, sys
file, schema = sys.argv[1], sys.argv[2]
try:
    import jsonschema
except ImportError:
    print(f"   [SKIP] jsonschema 未安装，跳过 {file}")
    sys.exit(0)
with open(file, encoding='utf-8') as f: data = json.load(f)
with open(schema, encoding='utf-8') as f: sch = json.load(f)
jsonschema.validate(data, sch)
PY
  if [ $? -eq 0 ]; then
    ok "$file 通过 $schema"
  else
    err "$file 不符合 $schema"
  fi
done

# ---------- 3. books.json 封面文件存在性 ----------
if [ -f books.json ]; then
  python - <<'PY'
import json, os, sys
data = json.load(open('books.json', encoding='utf-8'))
missing = [b['cover'] for b in data if not os.path.isfile(b['cover'])]
if missing:
    print('缺失封面:', missing, file=sys.stderr)
    sys.exit(1)
PY
  if [ $? -eq 0 ]; then
    ok "所有书籍封面文件存在"
  else
    err "books.json 中存在缺失封面，请补图"
  fi
fi

# ---------- 4. HTML skill-tag 与 JSON-LD knowsAbout 字面对齐 ----------
if [ -f index.htm ]; then
  python - <<'PY'
import re, sys
html = open('index.htm', encoding='utf-8').read()
m = re.search(r'"knowsAbout":\s*\[([^\]]+)\]', html)
if not m:
    sys.exit(0)
html_tags = set(re.findall(r'<span class="skill-tag">([^<]+)</span>', html))
raw = m.group(1)
ld_tags = set(t.strip().strip('"').strip("'") for t in raw.split(','))
only_html = html_tags - ld_tags
only_ld = ld_tags - html_tags
if only_html or only_ld:
    print('HTML skill-tag 与 JSON-LD knowsAbout 不一致：', file=sys.stderr)
    print('  HTML 独有:', sorted(only_html), file=sys.stderr)
    print('  JSON-LD 独有:', sorted(only_ld), file=sys.stderr)
    sys.exit(1)
PY
  if [ $? -eq 0 ]; then
    ok "skill-tag 与 knowsAbout 一致"
  else
    err "HTML 与 JSON-LD 字段不同步"
  fi
fi

echo "[PASS] check.sh 全部通过"
