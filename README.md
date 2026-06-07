# Public AI Skills

公开 AI Skill 仓库，集中托管可分享、可迁移、可打包发布的 skill。

当前已收录：

- `docx-to-markdown`
- `markdown-to-docx`

这个仓库适合作为：

- 公开 skill 的 GitHub 源仓库
- GitHub Release 下载源
- Claude Code / Antigravity / OpenCode 等工具的安装输入源

## 目录结构

```text
public-ai-skills/
├── README.md
├── registry.yaml
├── skills/
├── adapters/
├── scripts/
├── dist/
└── .github/workflows/
```

## 当前 Skill

| Skill | 说明 | Claude Code | Antigravity | OpenCode |
|------|------|:-----------:|:-----------:|:--------:|
| `docx-to-markdown` | Word 转 Markdown，支持标题、列表、表格等常见结构 | ✅ | ✅ | ✅ |
| `markdown-to-docx` | Markdown 转 Word，支持中国公文格式排版 | ✅ | ✅ | ✅ |

完整元数据见 [registry.yaml](registry.yaml)。

## 作为 Claude Code 插件市场安装

本仓库根目录提供了 [`.claude-plugin/marketplace.json`](.claude-plugin/marketplace.json)，可直接作为 Claude Code 的插件市场（marketplace）添加。

```bash
# 添加市场（GitHub 简写、本地路径或 Git URL 均可）
/plugin marketplace add code-better-life/public-ai-skills

# 安装插件（包含 docx-to-markdown 与 markdown-to-docx 两个 skill）
/plugin install document-conversion@public-ai-skills
```

> 通过 GitHub 简写添加时，Claude Code 会读取仓库默认分支（`main`）上的 `marketplace.json`，因此该文件需位于 `main` 分支。

安装后即可使用插件内置的两个 skill：

- `document-conversion:docx-to-markdown`
- `document-conversion:markdown-to-docx`

## 快速开始

### 1. 克隆仓库

```bash
git clone <your-public-repo-url>
cd public-ai-skills
```

### 2. 安装依赖

按需进入 skill 目录安装：

```bash
cd skills/docx-to-markdown
python3 -m pip install -r requirements.txt
```

或：

```bash
cd skills/markdown-to-docx
python3 -m pip install -r requirements.txt
```

### 3. 直接运行 skill 脚本

```bash
python3 skills/docx-to-markdown/scripts/convert_docs.py path/to/file.docx
python3 skills/markdown-to-docx/scripts/convert_to_docx.py path/to/file.md
```

## 发布与打包

本仓库自带发布打包脚本：

```bash
bash scripts/package-release.sh
```

它会：

- 为每个 skill 生成独立 ZIP
- 生成一个包含整个 `skills/` 目录的汇总 ZIP
- 将产物输出到 `dist/`

GitHub Actions 工作流见 [release.yml](.github/workflows/release.yml)。推送 `v*` tag 时，会自动打包并上传 Release 资产。

## 适配器

`adapters/` 目录中提供了面向不同工具的安装和转换脚本，包括：

- Claude Code
- Claude.ai
- Antigravity
- OpenClaw
- OpenCode

其中 Claude Code、Claude.ai、Antigravity 的脚本已经可以作为基础工作流使用；OpenClaw 和 OpenCode 目前仍是格式转换骨架。

## 可迁移性约束

公开 skill 在放进这个仓库前，建议确保：

- 不包含绝对路径
- 不依赖私有知识库或本地私有文件
- 依赖安装方式通用
- 脚本缺依赖时有清晰报错

## 版本建议

建议用 tag 做发布：

```bash
git tag v0.1.0
git push origin v0.1.0
```
