# Claude.ai 适配器

将 skill 打包为 `.skill`（ZIP）文件，用于上传到 Claude.ai。

## 使用方式

```bash
# 直接运行
bash adapters/claude-ai/package.sh skills/code-review

# 或通过 Makefile
make deploy-claude-ai
```

## 输出

打包后的文件保存在 `/tmp/<skill-name>.skill`，需手动上传到 Claude.ai > Customize > Skills。
