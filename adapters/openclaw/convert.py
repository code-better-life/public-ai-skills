"""
将标准 SKILL.md 转换为 OpenClaw 的指令格式。
根据 OpenClaw 的实际格式需求来实现。

用法: python convert.py <skill-directory>
"""
import yaml
import sys
from pathlib import Path


def convert(skill_path: Path):
    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        print(f"❌ 未找到: {skill_md}")
        sys.exit(1)

    content = skill_md.read_text()

    # 拆分 frontmatter 和正文
    parts = content.split("---", 2)
    if len(parts) < 3:
        print("❌ SKILL.md 缺少 YAML frontmatter")
        sys.exit(1)

    meta = yaml.safe_load(parts[1])
    body = parts[2].strip()

    # TODO: 根据 OpenClaw 的具体格式需求进行转换
    # 目前输出通用格式
    result = {
        "name": meta.get("name", "unknown"),
        "description": meta.get("description", ""),
        "instructions": body,
    }

    return result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python convert.py <skill-directory>")
        sys.exit(1)

    result = convert(Path(sys.argv[1]))
    print(yaml.dump(result, allow_unicode=True, default_flow_style=False))
