#!/bin/bash
# 部署 skill 到 Antigravity（通过 symlink）
# 从 registry.yaml 读取兼容 antigravity 的 skill，创建 symlink 到目标工作区的 .agent/skills/
#
# 用法:
#   bash adapters/antigravity/install.sh <工作区路径>
#   bash adapters/antigravity/install.sh          # 交互式输入路径

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
REGISTRY="$REPO_ROOT/registry.yaml"

# 获取目标工作区路径
if [ $# -ge 1 ]; then
    WORKSPACE="$1"
else
    read -p "输入目标工作区路径: " WORKSPACE
fi

# 展开 ~ 和相对路径
WORKSPACE="$(cd "$WORKSPACE" 2>/dev/null && pwd)" || {
    echo "❌ 工作区路径不存在: $WORKSPACE"
    exit 1
}

SKILL_DIR="$WORKSPACE/.agent/skills"
mkdir -p "$SKILL_DIR"

if ! command -v yq &> /dev/null; then
    echo "❌ 需要安装 yq: brew install yq"
    exit 1
fi

echo "📦 正在部署到 $SKILL_DIR ..."

count=0
for skill_path in $(yq '.skills[] | select(.platforms[] == "antigravity") | .path' "$REGISTRY"); do
    name=$(basename "$skill_path")
    src="$REPO_ROOT/$skill_path"
    dest="$SKILL_DIR/$name"

    if [ -d "$src" ]; then
        # 移除已有的 symlink 或目录
        [ -L "$dest" ] && rm "$dest"
        ln -sf "$src" "$dest"
        echo "  ✅ $name → $dest"
        ((count++))
    else
        echo "  ⚠️  $name: 路径不存在 ($src)"
    fi
done

echo ""
echo "✅ 已部署 $count 个 skill 到 $SKILL_DIR"
echo "💡 Antigravity 会自动从 .agent/skills/ 发现这些 skill"
