# Claude Code 适配器

通过 symlink 将 skill 部署到 `~/.claude/skills/` 目录。

## 使用方式

```bash
# 直接运行
bash adapters/claude-code/install.sh

# 或通过 Makefile
make deploy-claude-code
```

## 工作原理

1. 读取 `registry.yaml` 中 `platforms` 包含 `claude-code` 的 skill
2. 在 `~/.claude/skills/` 中创建 symlink 指向仓库中的 skill 目录
3. 修改仓库中的 skill 后，改动自动生效（无需重新部署）

## 依赖

- [yq](https://github.com/mikefarah/yq) — YAML 处理工具（`brew install yq`）
