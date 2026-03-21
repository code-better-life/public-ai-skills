#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SKILLS_DIR="$REPO_ROOT/skills"
DIST_DIR="${1:-$REPO_ROOT/dist}"

mkdir -p "$DIST_DIR"
rm -f "$DIST_DIR"/*.zip

found_skill=0

for skill_dir in "$SKILLS_DIR"/*; do
    if [ ! -d "$skill_dir" ]; then
        continue
    fi

    if [ ! -f "$skill_dir/SKILL.md" ]; then
        continue
    fi

    found_skill=1
    skill_name="$(basename "$skill_dir")"
    echo "Packaging $skill_name"

    (
        cd "$SKILLS_DIR"
        zip -r "$DIST_DIR/${skill_name}.zip" "$skill_name" -x "*.DS_Store"
    )
done

if [ "$found_skill" -eq 0 ]; then
    echo "No skills with SKILL.md found in $SKILLS_DIR"
    exit 1
fi

(
    cd "$REPO_ROOT"
    zip -r "$DIST_DIR/all-skills.zip" skills -x "*.DS_Store"
)

echo "Artifacts created in $DIST_DIR"
