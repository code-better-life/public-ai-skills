# Antigravity 适配器

Antigravity 原生支持标准 SKILL.md 格式，无需格式转换。Skill 从工作区的 `.agent/skills/` 目录加载。

## 部署到指定工作区

```bash
# 指定工作区路径
bash adapters/antigravity/install.sh /path/to/workspace

# 交互式输入
bash adapters/antigravity/install.sh
```

脚本会从 `registry.yaml` 读取所有 `platforms` 包含 `antigravity` 的 skill，在目标工作区的 `.agent/skills/` 下创建 symlink。

## 前置依赖

- [yq](https://github.com/mikefarah/yq): `brew install yq`

## 注意事项

- 使用 symlink 部署，修改仓库中 skill 后自动生效
- 部分 vendor skill（如 skill-creator）依赖 Claude CLI，在 Antigravity 中功能受限
- `convert.py` 为预留骨架，当前无需使用
