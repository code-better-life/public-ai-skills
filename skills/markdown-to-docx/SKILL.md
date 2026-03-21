---
name: markdown-to-docx
description: >
  将 Markdown 文件转换为符合中国公文排版格式（GB/T 9704）的 Word (.docx) 文档。
  也支持对现有 .docx 文件重新应用公文格式。自动处理标题层级映射、字体设置（方正小标宋简体/黑体/楷体/仿宋）、
  页面布局、页码和标点规范化。当用户需要将 Markdown 转为 Word、生成公文格式文档、
  对已有 Word 文档应用公文排版、或者提到"公文"、"排版"、"Word 格式"等关键词时，
  请使用此 skill。即使用户只是说"把这个 md 转成 docx"，也应使用此 skill。
platforms:
  - claude-code
  - antigravity
  - opencode
tags:
  - document
  - docx
  - markdown
  - conversion
  - 公文
version: 1.0.0
---

# Markdown to Word（公文格式）Conversion

将 Markdown 文件转换为符合中国公文排版标准的 Word 文档，或对现有 `.docx` 文件重新应用公文格式。

## 依赖安装

```bash
python3 -m pip install -r requirements.txt
```

或仅安装最小依赖：

```bash
python3 -m pip install python-docx
```

## 使用方式

脚本路径：`scripts/convert_to_docx.py`（相对于本 skill 目录）

### 将 Markdown 转为 Word

```bash
python3 <SKILL_DIR>/scripts/convert_to_docx.py path/to/file.md
```

### 批量转换

```bash
python3 <SKILL_DIR>/scripts/convert_to_docx.py file1.md file2.md
```

### 对已有 Word 文档应用公文格式

```bash
python3 <SKILL_DIR>/scripts/convert_to_docx.py path/to/file.docx
```

生成 `file_formatted.docx`。加 `--overwrite` 覆盖原文件。

### 指定输出路径

```bash
python3 <SKILL_DIR>/scripts/convert_to_docx.py -o output.docx input.md
```

> `<SKILL_DIR>` 需替换为本 skill 目录的实际路径；如果已经 `cd` 到 skill 目录，也可以直接运行 `python3 scripts/convert_to_docx.py`。

## 公文排版规范

### 标题与正文格式

| 元素 | 字体 | 字号 | 说明 |
|------|------|------|------|
| 文档标题 (`#`) | 方正小标宋简体 | 二号 (22pt) | 居中，行距 35pt，无边框 |
| 一级标题 (`##`) | 黑体 | 三号 (16pt) | 行距 30pt，末尾无句号，不加粗 |
| 二级标题 (`###`) | 楷体_GB2312 | 三号 (16pt) | 行距 30pt，末尾补句号（。），不加粗 |
| 三级标题 (`####`+) | 仿宋_GB2312 | 三号 (16pt) | 行距 30pt，末尾补句号（。），**加粗** |
| 正文 | 仿宋_GB2312 | 三号 (16pt) | 首行缩进2字符，行距 30pt |

### 页面设置

| 项目 | 设置 |
|------|------|
| 纸张 | A4 |
| 上边距 | 3.7cm |
| 下边距 | 3.5cm |
| 左边距 | 2.8cm |
| 右边距 | 2.6cm |
| 页码格式 | `- 1 -`，宋体四号，奇数页右/偶数页左 |

### Word 样式映射

| Markdown | Word 样式 | 大纲级别 |
|----------|-----------|----------|
| `#` | Title | Level 0 |
| `##` | Heading 1 | Level 1 |
| `###` | Heading 2 | Level 2 |
| `####`+ | Heading 3 | Level 3 |
| 正文 | Normal | — |

### 文本规范化

- **标题标点**：一级标题去除末尾句号；二/三级标题确保末尾有且仅有一个句号（。）
- **标题格式**：剥除 Markdown 粗体/斜体标记；三级标题由脚本强制加粗
- **编号空格**：去除编号后多余空格（`1. 文本` → `1.文本`）
- **引号转换**：英文引号自动转换为中文引号（""、''）

### 字体回退

当特定字体未安装时，脚本自动使用备选字体：

| 首选字体 | 回退字体 |
|----------|----------|
| 方正小标宋简体 | SimSun (宋体) |
| 楷体_GB2312 | KaiTi (楷体) |
| 仿宋_GB2312 | FangSong (仿宋) |
| 黑体 | SimHei (黑体) |

## 功能特性

- **双模式**：支持 Markdown → Word 转换，也支持对已有 .docx 重新排版
- **标题导航**：生成的文档在 Word 导航窗格中可直接跳转
- **内联格式**：支持 `**粗体**`、`*斜体*`、`<span style="color:red">彩色文字</span>`
- **表格支持**：Markdown 表格转为 Word 表格（Table Grid 样式）
