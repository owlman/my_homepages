#!/usr/bin/env bash
# 一次性安装 pre-push 钩子：
#   bash tools/install-hook.sh
# 会把 tools/pre-push 复制到 .git/hooks/pre-push 并 chmod +x。
#
# 注意：.git/hooks/ 不入 git，是单台机器的本地钩子；新机器需要重新运行。
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || (echo "[FAIL] 当前目录不是 Git 仓库" >&2; exit 1))"

cp "$SCRIPT_DIR/pre-push" "$REPO_ROOT/.git/hooks/pre-push"
chmod +x "$REPO_ROOT/.git/hooks/pre-push"

echo "[OK] pre-push 钩子已安装到 $REPO_ROOT/.git/hooks/pre-push"
echo "     下次 git push 会自动跑 tools/check.sh"
echo "     临时跳过：git push --no-verify"
