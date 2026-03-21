#!/bin/bash
# 打包 skill 为 .skill (ZIP) 文件，用于上传到 Claude.ai
# 用法: bash package.sh <skill-path>

set -euo pipefail

if [ $# -eq 0 ]; then
    echo "用法: bash package.sh <skill-path>"
    echo "示例: bash package.sh skills/code-review"
    exit 1
fi

SKILL_PATH="$1"
SKILL_NAME=$(basename "$SKILL_PATH")
OUTPUT="/tmp/${SKILL_NAME}.skill"

if [ ! -d "$SKILL_PATH" ]; then
    echo "❌ 目录不存在: $SKILL_PATH"
    exit 1
fi

if [ ! -f "$SKILL_PATH/SKILL.md" ]; then
    echo "❌ 未找到 SKILL.md: $SKILL_PATH/SKILL.md"
    exit 1
fi

cd "$SKILL_PATH"
zip -r "$OUTPUT" . -x "*.git*" "*.DS_Store"

echo ""
echo "✅ 已打包: $OUTPUT"
echo "📋 请手动上传到 Claude.ai > Customize > Skills"
