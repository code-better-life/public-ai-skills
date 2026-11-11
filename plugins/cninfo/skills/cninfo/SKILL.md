---
name: cninfo
description: >
  检索巨潮资讯网（cninfo.com.cn）上市公司公告：按标题关键词全市场搜索、按公司列出公告、
  按公告类别和板块筛选、搜索公告正文，并下载 PDF、转成文本阅读。当用户要找 A 股公告、
  查某公司披露过什么、找同类案例（如变更募投、关注函回复、股东会决议）、下载年报季报，
  或者说"巨潮查一下""找找有没有类似公告"时使用。不需要 key。
platforms:
  - claude-code
tags:
  - cninfo
  - announcement
  - a-share
  - disclosure
version: 1.0.0
---

# 巨潮资讯网公告检索

脚本 `scripts/cninfo.py` 只用 Python 标准库，Python 3.8 以上即可运行，不需要 key。
它调用的是巨潮网页自己用的查询接口，不是官方数据服务，接口可能变化；结果以巨潮网站为准。

## 网络

需要能访问 `www.cninfo.com.cn` 和 `static.cninfo.com.cn`。中国大陆网络可以直接用；
云端沙箱若有出站白名单，要放行这两个域名。偶发连接被重置时脚本会自动重试。

## 常用命令

```bash
# 全市场按标题关键词（默认近一年，按时间倒序，默认 30 条）
python3 scripts/cninfo.py search 变更募集资金用途 --since 2026-01-01

# 某家公司的全部公告（代码或简称都行，简称有歧义时会列出候选让你改用代码）
python3 scripts/cninfo.py search --stock 000001 --since 2026-10-01 --limit 100

# 公司 + 关键词
python3 scripts/cninfo.py search 业绩说明会 --stock 600519 --since 2026-01-01

# 按类别、板块筛选（类别可逗号分隔多个）
python3 scripts/cninfo.py search --category 董事会 --plate szmb --since 2026-11-10
python3 scripts/cninfo.py search --stock 000001 --category 年报,半年报 --since 2024-01-01

# 搜正文（匹配很宽，结果多，标题搜不到时再用）
python3 scripts/cninfo.py search 募集资金 --body --since 2026-11-01

# 下载 PDF，--text 同时用 pdftotext 转成 .txt 方便阅读
python3 scripts/cninfo.py download https://static.cninfo.com.cn/finalpage/2026-11-07/1225661488.PDF --out ./cninfo --text

python3 scripts/cninfo.py stock 平安银行      # 代码/简称 → orgId
python3 scripts/cninfo.py categories          # 列出全部类别和板块
```

`search` 加 `--json` 输出结构化结果，字段：`date`、`code`、`name`、`title`、`id`、`pdf`、`detail`
（巨潮公告详情页）。文本输出每条两行：日期、代码、简称、标题，下一行是 PDF 链接。

## 选项

| 选项 | 说明 |
|---|---|
| `keyword` | 标题关键词，可省略（只按公司或类别列） |
| `--stock` | 证券代码或简称 |
| `--category` | 年报、半年报、一季报、三季报、业绩预告、权益分派、董事会、监事会、股东会、日常经营、公司治理、中介报告、首发、增发、股权激励、配股、解禁、公司债、可转债、其他融资、股权变动、补充更正、澄清致歉、风险提示、特别处理和退市、退市整理期 |
| `--plate` | `sz` 深市、`szmb` 深主板、`szcy` 创业板、`sh` 沪市、`shmb` 沪主板、`shkcp` 科创板、`bj` 北交所 |
| `--since` / `--until` | 日期 `YYYY-MM-DD`，默认今天往前一年 |
| `--limit` | 最多返回条数，默认 30，自动翻页 |
| `--body` | 改搜正文；不能和 `--stock`/`--category`/`--plate` 同用，可把公司简称写进关键词 |

## 检索技巧

- 标题检索按巨潮分词匹配，关键词写短而核心的词，例如"变更募集资金用途""关注函""延期"。
  搜不到时换同义词或拆短（"股东大会"和"股东会"都试），再不行用 `--body`。
- 找同类案例：先全市场标题检索圈定公司和公告，再下载 PDF 读原文；交易所问询类可同时搜"关注函""问询函"。
- 查一家公司某类事项：`--stock` 加关键词，或 `--stock` 加 `--category`。
- 全市场宽泛关键词结果可能上千条，先看第一行的总数，再收窄日期、板块或关键词，不要一次拉几千条。
- 巨潮对高频请求会限流甚至短暂封 IP。脚本是串行的，翻页间隔 1 秒；不要并行跑多个脚本实例，
  批量下载控制在几十份以内。
- 阅读 PDF 用 `download --text` 转文本后再读，比直接读 PDF 快、不易失真。`--text` 需要 poppler 的
  `pdftotext`（macOS `brew install poppler`，Debian/Ubuntu `apt install poppler-utils`）。

## 输出给用户

整理成表格或要点：披露日期、证券代码和简称、公告标题、PDF 链接。引用公告内容时写明出自哪份公告及披露日期，
并注明来源巨潮资讯网。原始 JSON 太长时不要整段贴出。
