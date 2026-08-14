# 支持格式与依赖对照

对应 markitdown 0.1.7。

## 格式 → 扩展名 → 依赖 extras

| 格式 | 扩展名 | 需要的 extras | 输出特点 |
|------|--------|---------------|----------|
| PDF | `.pdf` | `[pdf]` | 提取文本层与表格；扫描件无文本层则输出为空 |
| Word | `.docx` | `[docx]` | 保留标题、列表、表格；`.doc` 不支持 |
| PowerPoint | `.pptx` | `[pptx]` | 按幻灯片切分，含表格、图片 alt 文本、演讲者备注 |
| Excel | `.xlsx` | `[xlsx]` | 每个 sheet 一张 Markdown 表 |
| 旧版 Excel | `.xls` | `[xls]` | 同上 |
| Outlook 邮件 | `.msg` | `[outlook]` | 提取 From/To/Subject 与正文 |
| 音频 | `.wav` `.mp3` `.m4a` `.mp4` | `[audio-transcription]` | EXIF 元数据 + 语音转写（依赖外部识别服务） |
| YouTube | URL | `[youtube-transcription]` | 标题、描述、字幕 |
| 图片 | `.jpg` `.jpeg` `.png` | 无 | 默认只有 EXIF 元数据；配 `llm_client` 后生成图片描述 |
| HTML | `.html` `.htm` | 无 | Wikipedia、Bing 结果页有专门的清洗逻辑 |
| CSV | `.csv` | 无 | 转为 Markdown 表 |
| JSON | `.json` `.jsonl` | 无 | 按纯文本输出 |
| XML / RSS / Atom | `.xml` `.rss` `.atom` | 无 | RSS/Atom 走订阅源专用解析 |
| 纯文本 | `.txt` `.text` `.md` `.markdown` | 无 | 原样输出（含编码探测） |
| EPub | `.epub` | 无 | 按章节转换 |
| Jupyter | `.ipynb` | 无 | 保留 Markdown/代码单元 |
| ZIP | `.zip` | 取决于内部文件 | 解压后逐个转换并拼成一个文档 |

`[all]` 一次装全所有可选依赖（体积较大，包含 pandas、pdfplumber、azure SDK 等）。

## 云端增强

| 能力 | 安装 | 用法 |
|------|------|------|
| Azure Document Intelligence | `[az-doc-intel]` | `markitdown f.pdf -d -e "<endpoint>"`；Python：`MarkItDown(docintel_endpoint=...)` |
| Azure Content Understanding | `[az-content-understanding]` | `markitdown f.pdf --use-cu --cu-endpoint "<endpoint>"`，支持 `--cu-analyzer`、`--cu-file-types`；可做结构化字段抽取与视频分析 |

两者都是按调用计费的云服务，且互斥（CLI 上不能同时用）。

## 插件

```bash
markitdown --list-plugins          # 列出已安装插件
markitdown -p file.pdf             # 启用插件转换
```

第三方插件在 GitHub 用 `#markitdown-plugin` 标签检索。例如 `markitdown-ocr` 可用 LLM Vision 给 PDF/DOCX/PPTX/XLSX 中的内嵌图片做 OCR（需要同时提供 `llm_client` / `llm_model`）。

## Python API 要点

```python
from markitdown import MarkItDown

md = MarkItDown(
    enable_plugins=False,        # 是否加载第三方插件
    llm_client=None,             # 多模态模型客户端（图片描述）
    llm_model=None,              # 例如 "gpt-4o"
    llm_prompt=None,             # 可选的自定义提示词
    docintel_endpoint=None,      # Azure Document Intelligence
)

result = md.convert("input.pdf", keep_data_uris=False)
result.text_content   # Markdown 字符串
```

处理不可信输入时，优先用更窄的入口：`convert_local()`（只读本地文件）、`convert_stream()`（自己控制流）、`convert_response()`（自己发请求）。
