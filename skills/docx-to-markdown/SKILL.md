---
name: docx-to-markdown
description: >
  将 Word (.docx) 文件转换为 Markdown (.md) 格式。支持批量转换和递归扫描子目录。
  使用 mammoth 库进行语义提取，支持表格、标题、加粗、斜体、列表等格式。
  当用户需要将 Word 文档转为 Markdown、批量转换 docx 文件、或者需要将 Word 内容转为纯文本/Markdown
  以便进一步处理时，请使用此 skill。即使用户只是说"把这个 Word 文件转一下"或"读取 docx 内容"，
  也应考虑使用此 skill。
platforms:
  - claude-code
  - antigravity
  - opencode
tags:
  - document
  - docx
  - markdown
  - conversion
version: 1.0.0
---

# Docx to Markdown Conversion

将 `.docx` 文件转换为 Markdown 格式，使用 `mammoth` 库进行语义提取，并通过自定义 HTML 解析器生成干净的 Markdown 输出。

## 依赖安装

```bash
python3 -m pip install -r requirements.txt
```

或仅安装最小依赖：

```bash
python3 -m pip install mammoth
```

## 使用方式

脚本路径：`scripts/convert_docs.py`（相对于本 skill 目录）

### 转换指定文件

```bash
python3 <SKILL_DIR>/scripts/convert_docs.py path/to/file1.docx path/to/file2.docx
```

### 转换当前目录下的所有 docx 文件（非递归）

```bash
python3 <SKILL_DIR>/scripts/convert_docs.py
```

### 递归转换工作区内所有 docx 文件

```bash
python3 <SKILL_DIR>/scripts/convert_docs.py --recursive
```

> `<SKILL_DIR>` 需替换为本 skill 目录的实际路径；如果已经 `cd` 到 skill 目录，也可以直接运行 `python3 scripts/convert_docs.py`。

## 功能特性

- **跨平台**：基于 Python mammoth 库，Windows / macOS / Linux 均可运行
- **递归扫描**：使用 `--recursive` 参数递归查找子目录中的 `.docx` 文件
- **表格支持**：将 HTML 表格正确转换为 Markdown 表格格式
- **格式保留**：保留标题层级、加粗、斜体、有序/无序列表、超链接
- **临时文件过滤**：自动跳过以 `~$` 开头的 Word 临时文件

## 输出说明

- 输出文件与源文件同目录，仅扩展名变为 `.md`
- 例：`report.docx` → `report.md`
