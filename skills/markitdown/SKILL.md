---
name: markitdown
description: >
  把几乎任何文件转换为 Markdown：PDF、Word、PowerPoint、Excel、图片、音频、HTML、
  CSV/JSON/XML、EPub、Outlook .msg、ZIP 压缩包、Jupyter Notebook，以及网页与 YouTube URL。
  基于微软开源的 markitdown，输出结构清晰、token 友好、面向 LLM 的 Markdown。
  当用户需要"把 PDF/PPT/Excel 转成 markdown"、"提取这个文件里的文字"、"读一下这份资料"、
  "批量转换这个目录里的文档"，或者需要把网页、视频字幕转成文本再做分析时，请使用此 skill。
  如果只处理 .docx 且希望用 mammoth 做语义提取，可改用 docx-to-markdown。
platforms:
  - claude-code
  - antigravity
  - opencode
tags:
  - document
  - pdf
  - office
  - markdown
  - conversion
  - markitdown
version: 1.0.0
---

# MarkItDown — 任意文件转 Markdown

基于 [microsoft/markitdown](https://github.com/microsoft/markitdown)，把 PDF、Office 文档、图片、音频、网页、压缩包等转换为 Markdown。输出目标是"喂给 LLM 的文本"，保留标题、列表、表格、链接等结构，而不是追求人工阅读的高保真排版。

## 依赖安装

```bash
python3 -m pip install -r requirements.txt
```

或按需只装用得到的格式（体积小很多）：

```bash
python3 -m pip install 'markitdown[pdf,docx,pptx,xlsx]'
```

需要 Python 3.10+。完整的可选依赖（extras）与格式对应关系见 [references/formats.md](references/formats.md)。

**国内网络加镜像源**（实测比官方源快 2～4 倍，中科大最快，见 [references/formats.md](references/formats.md) 的实测数据）：

```bash
python3 -m pip install -i https://mirrors.ustc.edu.cn/pypi/simple -r requirements.txt
```

**用 uv 装 `[all]` 必须加 `--prerelease=allow`**：`[all]` 里的 `az-content-understanding` 依赖 `azure-ai-contentunderstanding>=1.2.0b1`（预发布版），不加这个参数 uv 会长时间回溯依赖后报错。pip 不受影响。

```bash
uv venv --python=3.12 .venv && source .venv/bin/activate
uv pip install --prerelease=allow 'markitdown[all]'
```

只装部分 extras（如 `[pdf,docx,pptx,xlsx]`）时不涉及预发布依赖，uv 直接装即可。

## 使用方式

### 方式一：官方 CLI（单文件，最省事）

```bash
markitdown report.pdf -o report.md      # 写入文件
markitdown report.pdf > report.md       # 重定向
cat report.pdf | markitdown -x .pdf     # 管道输入，用 -x 提示扩展名
```

常用参数：`-o` 输出文件、`-x` 扩展名提示、`-m` MIME 提示、`-c` 字符集提示、`--keep-data-uris` 保留 base64 图片、`-p` 启用插件、`--list-plugins` 列出插件。

### 方式二：批量脚本（多文件 / 整个目录 / URL）

官方 CLI 一次只处理一个输入，批量转换用本 skill 的脚本：`scripts/convert_to_markdown.py`

```bash
# 转换指定文件（可混合多种格式）
python3 <SKILL_DIR>/scripts/convert_to_markdown.py a.pdf b.pptx c.xlsx

# 转换当前目录下所有受支持文件（非递归）
python3 <SKILL_DIR>/scripts/convert_to_markdown.py

# 递归转换某个目录，输出集中到 out/
python3 <SKILL_DIR>/scripts/convert_to_markdown.py docs/ --recursive -o out/

# 转换网页 / YouTube 链接，直接打印
python3 <SKILL_DIR>/scripts/convert_to_markdown.py https://example.com/page.html --stdout
```

参数：`-r/--recursive` 递归、`-o/--output-dir` 输出目录（默认与源文件同目录）、`--stdout` 打印不写文件、`-p/--use-plugins` 启用插件、`--keep-data-uris` 保留 data URI。

> `<SKILL_DIR>` 替换为本 skill 目录的实际路径；已经 `cd` 到 skill 目录时可直接写 `scripts/convert_to_markdown.py`。

### 方式三：Python API（需要定制时）

```python
from markitdown import MarkItDown

md = MarkItDown(enable_plugins=False)
result = md.convert("test.xlsx")
print(result.text_content)
```

用多模态模型给图片和 PPT 配图生成描述：

```python
from markitdown import MarkItDown
from openai import OpenAI

md = MarkItDown(llm_client=OpenAI(), llm_model="gpt-4o")
print(md.convert("slide.pptx").text_content)
```

扫描件、复杂版面 PDF 可走 Azure Document Intelligence：

```bash
markitdown scanned.pdf -o out.md -d -e "<document_intelligence_endpoint>"
```

## 支持格式

PDF · Word(.docx) · PowerPoint(.pptx) · Excel(.xlsx/.xls) · CSV · JSON/JSONL · XML/RSS/Atom · HTML · TXT/Markdown · EPub · Outlook(.msg) · Jupyter(.ipynb) · 图片(.jpg/.jpeg/.png) · 音频(.wav/.mp3/.m4a/.mp4) · ZIP（递归转换内部文件） · 网页与 YouTube URL。

逐格式的依赖要求和输出特点见 [references/formats.md](references/formats.md)。

## 注意事项

- **输出定位**：面向文本分析，不保证与原文排版一致；需要精确公文排版请用 `markdown-to-docx` 反向生成。
- **PDF**：纯文本层提取，扫描件（图片型 PDF）默认拿不到文字，需要 Azure Document Intelligence 或 OCR 插件。
- **图片/音频**：默认只提取 EXIF 元数据；图片描述需要配置 `llm_client`，语音转写需要 `[audio-transcription]` 依赖且依赖外部识别服务。
- **输出命名**：脚本默认在源文件旁生成同名 `.md`，不想污染源目录就加 `-o`。同一次运行内重名（`a.csv` 与 `a.xlsx` 都想写 `a.md`）会自动加 `_1`、`_2` 后缀；输出路径正好等于输入时跳过，不会自毁。
- **扫描目录时跳过 `.md`/`.markdown`**（已经是 Markdown，转了等于复制）；显式把 `.md` 当参数传入仍会转换。
- **stdout 干净**：脚本的进度日志走 stderr，`--stdout` 输出的是纯 Markdown，可直接管道给其他命令。
- **安全**：markitdown 以当前进程权限做 I/O，且 `convert()` 会访问本地文件和远程 URL。处理不可信输入前先做校验，或改用更窄的 `convert_local()` / `convert_stream()`。

## 与其他 skill 的关系

| 场景 | 用哪个 |
|------|--------|
| 混合格式 / PDF / PPT / Excel / 网页 → Markdown | `markitdown`（本 skill） |
| 纯 .docx 批量转换，想要 mammoth 的语义提取 | `docx-to-markdown` |
| Markdown → Word（含中国公文格式） | `markdown-to-docx` |
