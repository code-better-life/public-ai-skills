---
name: tianyancha
description: >
  通过天眼查开放平台 API 查询企业工商信息：企业搜索、基本信息、股东、对外投资、主要人员、
  变更记录、实际控制人、法律诉讼、经营异常等。当用户要查某家公司的工商登记、统一社会信用代码、
  法定代表人、注册资本、股东结构、实际控制人、涉诉或风险信息，或者说"天眼查一下""查查这家公司"时使用。
  不需要的接口不要调，用最少的调用拿到答案。
platforms:
  - claude-code
tags:
  - company
  - tianyancha
  - api
version: 1.0.0
---

# 天眼查开放平台查询

脚本 `scripts/tyc.py` 只用 Python 标准库，Python 3.8 以上即可运行，无需安装依赖。
使用前需要在 [天眼查开放平台](https://open.tianyancha.com) 申请 token，并开通要用的接口。

## 配置 token

天眼查用请求头 `Authorization: <token>` 认证，不加 Bearer 前缀，域名 `open.api.tianyancha.com`。
脚本按以下顺序找 token：

1. 环境变量 `TIANYANCHA_TOKEN`
2. 文件 `~/.config/tianyancha/token`

推荐用文件，避免 token 进入 shell 历史。在 zsh 里可以这样写入（输入不回显）：

```bash
mkdir -p ~/.config/tianyancha && read -rs "t?token: " && printf '%s' "$t" > ~/.config/tianyancha/token && chmod 600 ~/.config/tianyancha/token && unset t
```

bash 用户把 `read -rs "t?token: "` 换成 `read -rsp "token: " t`。

两处都没有 token 时，脚本不带认证头发请求，适用于由网关或代理在出站时注入认证头的环境。

`python3 scripts/tyc.py check` 只显示 token 来源和长度，不发请求。任何时候都不要打印、回显或写出 token 本身。

## 网络限制

天眼查开放平台拒绝境外 IP，会返回 HTTP 418 和"您当前所在地区暂不支持访问"。
海外云主机、境外出口的云端沙箱无法直接调用，需要在中国大陆网络环境下运行，或经大陆出口的代理转发。

## 调用方式

```bash
python3 scripts/tyc.py search 腾讯                          # 搜索企业，返回候选列表（含 id、全称、信用代码）
python3 scripts/tyc.py base 北京百度网讯科技有限公司           # 企业基本信息（ic/baseinfo/normal）
python3 scripts/tyc.py get ic/holder/2.0 keyword=小米科技有限责任公司 pageNum=1 pageSize=20
```

`get` 可调开放平台任意接口，路径写 `/services/open/` 之后的部分，参数用 `key=value`。
`keyword` 一般可以是公司全称、统一社会信用代码、注册号或天眼查公司 id。

## 常用接口

以下路径均已实测可用。接口能否调用取决于你的账号开通了哪些服务。

| 用途 | 路径 | 主要参数 |
|---|---|---|
| 搜索企业（返回 id、全称、信用代码、状态） | `search/2.0` | `word`, `pageNum`, `pageSize` |
| 企业基本信息，含联系方式（接口 818） | `ic/baseinfoV2/2.0` | `keyword` |
| 企业基本信息，含主要人员（接口 819） | `ic/baseinfoV3/2.0` | `keyword` |
| 企业基本信息 | `ic/baseinfo/normal` | `keyword` |
| 股东信息 | `ic/holder/2.0` | `keyword`, `pageNum`, `pageSize` |
| 对外投资 | `ic/inverst/2.0` | `keyword`, `pageNum`, `pageSize` |
| 主要人员（接口 820） | `ic/staff/2.0` | `keyword`, `pageNum`, `pageSize` |
| 变更记录 | `ic/changeinfo/2.0` | `keyword`, `pageNum`, `pageSize` |
| 实际控制人 | `ic/actualControl/3.0` | `keyword` |
| 法律诉讼 | `jr/lawSuit/3.0` | `keyword`, `pageNum`, `pageSize` |
| 经营异常 | `mr/abnormal/2.0` | `keyword`, `pageNum`, `pageSize` |

表里没有的接口，先到 https://open.tianyancha.com/api_list 查路径和参数再用 `get`。
路径写错时天眼查返回的是 300005（无权限），不是"URL 不存在"，遇到 300005 先核对路径。
核对路径可以用一个不存在的公司名去调：路径对就返回 300000（查无结果）。

## 少调用的用法

天眼查按接口计费或计次，照下面的原则来：

- 用户给的是简称或不确定全称时，先 `search` 一次，从结果里确认全称或 id，再查明细，别拿简称反复试。
- 一个问题只调需要的接口。用户问"注册资本多少"，`base` 一次就够，不要顺手把股东、诉讼都查一遍。
- 同一会话里已经查过的结果直接复用，不重复调用。
- 分页接口先看第一页的 `total`，确有需要再翻页。

## 返回与错误

成功时 `error_code` 为 0，数据在 `result`。脚本在出错时把错误码和含义写到 stderr，退出码为 1。

| error_code | 含义 |
|---|---|
| 300000 | 查询无结果（检查公司名是否为全称） |
| 300002 / 300003 | 账号失效或过期 |
| 300004 | 访问频率过快，稍后再试 |
| 300005 | 账号未开通此接口，或接口路径写错 |
| 300006 / 300007 | 余额或次数不足，提醒用户去开放平台处理 |
| 300008 | 缺少必要参数（没带 token 时也是这个） |
| 300009 | 账号信息有误，多半是 token 填错 |
| 300011 | IP 不在白名单 |

## 输出给用户

把关键字段整理成简短表格或要点（全称、信用代码、法定代表人、成立日期、注册资本、经营状态、
注册地址等），注明数据来自天眼查及查询日期。原始 JSON 太长时不要整段贴出。
