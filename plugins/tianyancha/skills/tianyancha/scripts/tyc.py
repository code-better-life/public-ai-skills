#!/usr/bin/env python3
"""天眼查开放平台命令行客户端，只用标准库。

token 来源（按顺序）：环境变量 TIANYANCHA_TOKEN、文件 ~/.config/tianyancha/token。
都没有时不带 Authorization 头发请求，适用于由网关或代理
在出站时注入 Authorization 头的环境。

用法：
  tyc.py search 腾讯                        # 搜索企业（search/2.0）
  tyc.py base 北京百度网讯科技有限公司        # 企业基本信息（ic/baseinfo/normal）
  tyc.py get ic/holder/2.0 keyword=小米科技有限责任公司 pageNum=1
  tyc.py check                              # 只看 token 从哪来，不发请求
"""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

BASE = "https://open.api.tianyancha.com/services/open/"
TOKEN_FILE = os.path.expanduser("~/.config/tianyancha/token")

# 常见错误码，见开放平台文档
ERRORS = {
    300000: "查询无结果",
    300001: "请求失败",
    300002: "账号失效",
    300003: "账号过期",
    300004: "访问频率过快",
    300005: "无权限访问此 API",
    300006: "余额不足",
    300007: "剩余次数不足",
    300008: "缺少必要参数",
    300009: "账号信息有误",
    300010: "URL 不存在",
    300011: "此 IP 无权限访问此 API",
    300012: "报告生成中",
}


def load_token():
    tok = os.environ.get("TIANYANCHA_TOKEN", "").strip()
    if tok:
        return tok, "env TIANYANCHA_TOKEN"
    if os.path.isfile(TOKEN_FILE):
        with open(TOKEN_FILE, encoding="utf-8") as f:
            tok = f.read().strip()
        if tok:
            return tok, TOKEN_FILE
    return None, "none (no Authorization header will be sent)"


def call(path, params):
    path = path.strip("/")
    if path.startswith("services/open/"):
        path = path[len("services/open/"):]
    url = BASE + path + "?" + urllib.parse.urlencode(params)
    headers = {"Accept": "application/json", "User-Agent": "tyc-cli/1.0"}
    tok, _ = load_token()
    if tok:
        headers["Authorization"] = tok
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        sys.stderr.write("HTTP %s\n" % e.code)
        if e.code == 418:
            sys.stderr.write("天眼查拒绝了境外 IP，请在中国大陆网络环境下运行\n")
    try:
        data = json.loads(body)
    except ValueError:
        sys.stderr.write("非 JSON 响应：%s\n" % body[:500])
        sys.exit(2)
    code = data.get("error_code")
    if code not in (0, None):
        sys.stderr.write("error_code=%s %s reason=%s\n"
                         % (code, ERRORS.get(code, ""), data.get("reason")))
    return data


def parse_kv(items):
    out = {}
    for it in items:
        if "=" not in it:
            sys.exit("参数要写成 key=value：%s" % it)
        k, v = it.split("=", 1)
        out[k] = v
    return out


def main(argv):
    if len(argv) < 2 or argv[1] in ("-h", "--help"):
        print(__doc__)
        return 0
    cmd, rest = argv[1], argv[2:]
    if cmd == "check":
        tok, src = load_token()
        print("token source:", src, "(length %d)" % len(tok) if tok else "")
        return 0
    if cmd == "search":
        if not rest:
            sys.exit("用法：tyc.py search <关键词> [pageNum=1 pageSize=20]")
        params = {"word": rest[0], "pageNum": "1", "pageSize": "20"}
        params.update(parse_kv(rest[1:]))
        data = call("search/2.0", params)
    elif cmd == "base":
        if not rest:
            sys.exit("用法：tyc.py base <公司全称/统一社会信用代码/天眼查 id>")
        data = call("ic/baseinfo/normal", {"keyword": rest[0]})
    elif cmd == "get":
        if not rest:
            sys.exit("用法：tyc.py get <接口路径> key=value ...")
        data = call(rest[0], parse_kv(rest[1:]))
    else:
        sys.exit("未知命令：%s" % cmd)
    json.dump(data, sys.stdout, ensure_ascii=False, indent=2)
    print()
    return 0 if data.get("error_code") in (0, None) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
