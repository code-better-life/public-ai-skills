#!/usr/bin/env python3
"""巨潮资讯网（cninfo.com.cn）公告检索命令行，只用标准库。

调用的是巨潮网页自己用的查询接口（非官方数据服务），不需要 key。
巨潮会对高并发返回 403 或断开连接，脚本串行请求、自动重试，翻页之间有间隔。

用法：
  cninfo.py search 变更募集资金用途 --since 2026-10-01          # 全市场按标题关键词
  cninfo.py search --stock 000001 --since 2026-10-01           # 某公司全部公告
  cninfo.py search 业绩说明会 --stock 贵州茅台 --since 2026-01-01  # 公司 + 关键词
  cninfo.py search --category 董事会 --plate szmb --since 2026-11-10
  cninfo.py search 募集资金 --body --since 2026-10-01           # 搜正文（宽泛）
  cninfo.py stock 平安银行                                     # 代码/简称 → orgId
  cninfo.py download finalpage/2026-11-07/1225661488.PDF --text  # 下载 PDF，可转文本
  cninfo.py categories                                         # 列出类别和板块
"""
import argparse
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

SITE = "https://www.cninfo.com.cn"
STATIC = "https://static.cninfo.com.cn/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "X-Requested-With": "XMLHttpRequest",
    "Accept": "application/json, text/plain, */*",
    "Origin": SITE,
    "Referer": SITE + "/new/commonUrl/pageOfSearch?url=disclosure/list/search",
}
BJ = dt.timezone(dt.timedelta(hours=8))

# 巨潮“公告类别”，值为接口 category 参数（沪深京通用）
CATEGORIES = {
    "年报": "category_ndbg_szsh",
    "半年报": "category_bndbg_szsh",
    "一季报": "category_yjdbg_szsh",
    "三季报": "category_sjdbg_szsh",
    "业绩预告": "category_yjygjxz_szsh",
    "权益分派": "category_qyfpxzcs_szsh",
    "董事会": "category_dshgg_szsh",
    "监事会": "category_jshgg_szsh",
    "股东会": "category_gddh_szsh",
    "日常经营": "category_rcjy_szsh",
    "公司治理": "category_gszl_szsh",
    "中介报告": "category_zj_szsh",
    "首发": "category_sf_szsh",
    "增发": "category_zf_szsh",
    "股权激励": "category_gqjl_szsh",
    "配股": "category_pg_szsh",
    "解禁": "category_jj_szsh",
    "公司债": "category_gszq_szsh",
    "可转债": "category_kzzq_szsh",
    "其他融资": "category_qtrz_szsh",
    "股权变动": "category_gqbd_szsh",
    "补充更正": "category_bcgz_szsh",
    "澄清致歉": "category_cqdq_szsh",
    "风险提示": "category_fxts_szsh",
    "特别处理和退市": "category_tbclts_szsh",
    "退市整理期": "category_tszlq_szsh",
}
ALIASES = {"股东大会": "股东会", "年度报告": "年报", "半年度报告": "半年报", "中报": "半年报",
           "一季度报告": "一季报", "三季度报告": "三季报", "退市": "特别处理和退市"}
PLATES = {"sz": "深市", "szmb": "深主板", "szcy": "创业板", "sh": "沪市", "shmb": "沪主板",
          "shkcp": "科创板", "bj": "北交所"}


def request(url, data=None, raw=False, tries=5):
    """GET/POST，失败按 2/4/8/16 秒退避重试。"""
    body = urllib.parse.urlencode(data).encode() if data is not None else None
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, data=body, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=40) as resp:
                content = resp.read()
            return content if raw else json.loads(content.decode("utf-8"))
        except (urllib.error.URLError, OSError, ValueError) as e:
            last = e
            if isinstance(e, urllib.error.HTTPError) and e.code == 404:
                break
            if i < tries - 1:
                time.sleep(2 ** (i + 1))
    sys.exit("请求失败：%s（%s）" % (url, last))


def clean(s):
    return re.sub(r"</?em>", "", s or "").strip()


def to_date(ms):
    return dt.datetime.fromtimestamp(ms / 1000, BJ).strftime("%Y-%m-%d")


def resolve_stock(word):
    """代码或简称 → 候选列表 [{code, name, orgId, category}]。"""
    res = request(SITE + "/new/information/topSearch/query", {"keyWord": word, "maxNum": 10})
    return [{"code": r["code"], "name": r["zwjc"], "orgId": r["orgId"], "category": r.get("category", "")}
            for r in res or []]


def pick_stock(word):
    cands = resolve_stock(word)
    a_share = [c for c in cands if c["category"] == "A股"] or cands
    exact = [c for c in a_share if word in (c["code"], c["name"])]
    if exact:
        return exact[0]
    if len(a_share) == 1:
        return a_share[0]
    if not a_share:
        sys.exit("找不到证券：%s" % word)
    sys.exit("“%s”匹配到多只证券，请改用代码：\n%s" % (
        word, "\n".join("%s %s %s" % (c["code"], c["name"], c["category"]) for c in a_share)))


def row(a):
    date = to_date(a["announcementTime"])
    name = a.get("secName") or ""
    title = clean(a.get("announcementTitle"))
    if name and title.startswith(clean(name) + "："):
        title = title[len(clean(name)) + 1:]  # 正文检索接口会在标题前加“简称：”
    return {
        "date": date,
        "code": a.get("secCode"),
        "name": clean(name),
        "title": title,
        "id": a.get("announcementId"),
        "pdf": STATIC + a["adjunctUrl"] if a.get("adjunctUrl") else "",
        "detail": "%s/new/disclosure/detail?stockCode=%s&announcementId=%s&orgId=%s&announcementTime=%s"
                  % (SITE, a.get("secCode"), a.get("announcementId"), a.get("orgId"), date),
    }


def cmd_search(args):
    until = args.until or dt.datetime.now(BJ).strftime("%Y-%m-%d")
    since = args.since or (dt.date.fromisoformat(until) - dt.timedelta(days=365)).isoformat()
    key = " ".join(args.keyword)
    rows, total, page = [], 0, 1
    if args.body:
        if args.stock or args.category or args.plate:
            sys.exit("--body 不支持 --stock/--category/--plate，可把公司简称写进关键词")
        if not key:
            sys.exit("--body 需要关键词")
        while len(rows) < args.limit:
            d = request(SITE + "/new/fulltextSearch/full?" + urllib.parse.urlencode({
                "searchkey": key, "sdate": since, "edate": until, "isfulltext": "true",
                "sortName": "pubdate", "sortType": "desc", "pageNum": page, "pageSize": 30, "type": ""}))
            total = d.get("totalAnnouncement") or 0
            batch = d.get("announcements") or []
            rows += [row(a) for a in batch]
            if not batch or not d.get("hasMore") or page * 30 >= total:
                break
            page += 1
            time.sleep(1)
    else:
        stock = ""
        if args.stock:
            s = pick_stock(args.stock)
            stock = "%s,%s" % (s["code"], s["orgId"])
        cat = ""
        if args.category:
            cats = []
            for c in args.category.split(","):
                c = ALIASES.get(c.strip(), c.strip())
                if c not in CATEGORIES:
                    sys.exit("未知类别：%s（运行 categories 查看）" % c)
                cats.append(CATEGORIES[c])
            cat = ";".join(cats)
        if args.plate and args.plate not in PLATES:
            sys.exit("未知板块：%s（可选 %s）" % (args.plate, "/".join(PLATES)))
        if not (key or stock or cat):
            sys.exit("至少给出关键词、--stock 或 --category 之一")
        while len(rows) < args.limit:
            d = request(SITE + "/new/hisAnnouncement/query", {
                "pageNum": page, "pageSize": 30, "column": "szse", "tabName": "fulltext",
                "plate": args.plate or "", "stock": stock, "searchkey": key, "secid": "",
                "category": cat, "trade": "", "seDate": "%s~%s" % (since, until),
                "sortName": "time", "sortType": "desc", "isHLtitle": "true"})
            total = d.get("totalAnnouncement") or 0
            batch = d.get("announcements") or []
            rows += [row(a) for a in batch]
            if not batch or not d.get("hasMore"):
                break
            page += 1
            time.sleep(1)
    seen = set()  # 翻页期间有新公告进来时，相邻页会有重复
    rows = [r for r in rows if not (r["id"] in seen or seen.add(r["id"]))][:args.limit]
    if args.json:
        print(json.dumps({"total": total, "since": since, "until": until, "rows": rows},
                         ensure_ascii=False, indent=1))
        return
    print("共 %d 条（%s ~ %s），显示 %d 条" % (total, since, until, len(rows)))
    for r in rows:
        print("%s  %s %s  %s\n    %s" % (r["date"], r["code"], r["name"], r["title"], r["pdf"]))


def cmd_stock(args):
    for c in resolve_stock(args.word):
        print("%s\t%s\t%s\t%s" % (c["code"], c["name"], c["orgId"], c["category"]))


def cmd_download(args):
    os.makedirs(args.out, exist_ok=True)
    for ref in args.refs:
        url = ref if ref.startswith("http") else STATIC + ref.lstrip("/")
        name = args.name if (args.name and len(args.refs) == 1) else url.rsplit("/", 1)[-1]
        path = os.path.join(args.out, name)
        if not (os.path.exists(path) and os.path.getsize(path) > 0):
            content = request(url, raw=True)
            if not content.startswith(b"%PDF") and url.lower().endswith(".pdf"):
                sys.exit("下载内容不是 PDF：%s" % url)
            with open(path, "wb") as f:
                f.write(content)
        print(path)
        if args.text:
            if not shutil.which("pdftotext"):
                sys.exit("未找到 pdftotext（poppler），可用 brew install poppler 或 apt install poppler-utils 安装")
            txt = os.path.splitext(path)[0] + ".txt"
            subprocess.run(["pdftotext", "-layout", path, txt], check=True)
            print(txt)
        time.sleep(0.5)


def cmd_categories(_):
    print("类别（--category，可逗号分隔多个）：")
    print("  " + "、".join(CATEGORIES))
    print("别名：" + "、".join("%s→%s" % kv for kv in ALIASES.items()))
    print("板块（--plate）：")
    print("  " + "、".join("%s=%s" % kv for kv in PLATES.items()))


def main():
    p = argparse.ArgumentParser(description="巨潮资讯网公告检索")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("search", help="检索公告")
    s.add_argument("keyword", nargs="*", help="标题关键词，多个词用空格分开")
    s.add_argument("--stock", help="证券代码或简称")
    s.add_argument("--category", help="公告类别，如 年报、董事会，可逗号分隔")
    s.add_argument("--plate", help="板块：sz szmb szcy sh shmb shkcp bj")
    s.add_argument("--since", help="起始日 YYYY-MM-DD，默认结束日前一年")
    s.add_argument("--until", help="结束日 YYYY-MM-DD，默认今天")
    s.add_argument("--limit", type=int, default=30, help="最多返回条数，默认 30")
    s.add_argument("--body", action="store_true", help="改搜公告正文（宽泛匹配，结果多）")
    s.add_argument("--json", action="store_true", help="输出 JSON")
    s.set_defaults(func=cmd_search)

    k = sub.add_parser("stock", help="代码/简称 → orgId")
    k.add_argument("word")
    k.set_defaults(func=cmd_stock)

    d = sub.add_parser("download", help="下载公告 PDF")
    d.add_argument("refs", nargs="+", help="PDF 链接或 adjunctUrl（如 finalpage/2026-10-27/xxx.PDF）")
    d.add_argument("--out", default="cninfo_downloads", help="保存目录，默认 ./cninfo_downloads")
    d.add_argument("--name", help="文件名（只下载一个时可用）")
    d.add_argument("--text", action="store_true", help="同时用 pdftotext -layout 转成 .txt")
    d.set_defaults(func=cmd_download)

    c = sub.add_parser("categories", help="列出类别和板块")
    c.set_defaults(func=cmd_categories)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
