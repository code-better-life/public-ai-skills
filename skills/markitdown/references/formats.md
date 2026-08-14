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

## 安装：镜像源与 uv 的预发布坑

### 镜像源实测

`markitdown[all]==0.1.7` 无缓存全新安装，同一台机器同一时段依次跑（2026-08，macOS arm64 / Python 3.12）：

| 源 | 地址 | 耗时 |
|----|------|------|
| 中科大 USTC | `https://mirrors.ustc.edu.cn/pypi/simple` | 4.8s |
| 阿里云 | `https://mirrors.aliyun.com/pypi/simple` | 9.0s |
| 华为云 | `https://repo.huaweicloud.com/repository/pypi/simple` | 10.4s |
| 清华 TUNA | `https://pypi.tuna.tsinghua.edu.cn/simple` | 12.2s |
| 官方 PyPI | `https://pypi.org/simple` | 19.1s |

五个源都已同步 0.1.7。绝对数字取决于你的网络，但国内源相对官方源的 2～4 倍差距是稳定的。

```bash
pip install -i https://mirrors.ustc.edu.cn/pypi/simple 'markitdown[all]'
# uv 用环境变量或 --index-url
UV_INDEX_URL=https://mirrors.ustc.edu.cn/pypi/simple uv pip install --prerelease=allow 'markitdown[all]'
```

### uv 装 `[all]` 需要 `--prerelease=allow`

`[all]` 包含 `az-content-understanding`，它依赖 `azure-ai-contentunderstanding>=1.2.0b1` —— 这是个预发布版本。uv 默认不接受预发布，会先长时间回溯依赖树，最后报 `... weren't enabled (try: --prerelease=allow)`。这跟镜像源快慢无关，换源不解决。

- `uv pip install 'markitdown[all]'` → 失败
- `uv pip install --prerelease=allow 'markitdown[all]'` → 正常
- `pip install 'markitdown[all]'` → 正常（pip 对含预发布的版本约束会自动放行）
- 只装 `[pdf,docx,pptx,xlsx]` 等子集 → 两者都正常，无需额外参数

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
