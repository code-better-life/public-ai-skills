#!/bin/bash
# 部署 skill 到 Claude Code（通过 symlink）
# 从 registry.yaml 读取兼容 claude-code 的 skill，创建 symlink 到 ~/.claude/skills/

set -euo pipefail

SKILL_DIR="$HOME/.claude/skills"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
REGISTRY="$REPO_ROOT/registry.yaml"

mkdir -p "$SKILL_DIR"

if ! command -v yq &> /dev/null; then
    echo "❌ 需要安装 yq: brew install yq"
    exit 1
fi

echo "📦 正在部署到 $SKILL_DIR ..."

count=0
for skill_path in $(yq '.skills[] | select(.platforms[] == "claude-code") | .path' "$REGISTRY"); do
    name=$(basename "$skill_path")
    src="$REPO_ROOT/$skill_path"
    dest="$SKILL_DIR/$name"

    if [ -d "$src" ]; then
        ln -sf "$src" "$dest"
        echo "  ✅ $name → $dest"
        ((count++))
    else
        echo "  ⚠️  $name: 路径不存在 ($src)"
    fi
done

echo ""
echo "✅ 已部署 $count 个 skill 到 $SKILL_DIR"
