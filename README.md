# China 12306 Train Tickets MCP

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![MCP](https://img.shields.io/badge/MCP-Server-blue)](https://modelcontextprotocol.io)
[![Remote](https://img.shields.io/badge/Streamable%20HTTP-hosted%20free-success)](https://mcp.pianam.cn/train-mcp/mcp)

Query **China Railway 12306 ticket availability** from any MCP client — train schedules and remaining seats by Chinese station name and date. Read-only, no booking, no account.

- **Try it in 30 seconds**: a free public MCP endpoint is already running — just paste the URL into your MCP client (no install, no API key).
- **Or self-host**: a single Python file, stdlib HTTP + FastMCP, zero paid dependencies.

## ⚡ Use the hosted endpoint (no setup)

```
https://mcp.pianam.cn/train-mcp/mcp
```

Transport: **Streamable HTTP** (MCP 2025-03-26 compatible). No authentication required.

## 🔌 Client configuration

Add this to your MCP client's `mcpServers` configuration (Claude Desktop `claude_desktop_config.json`, Cursor `mcp.json`, Cline, Cherry Studio, etc.):

```json
{
  "mcpServers": {
    "12306-train": {
      "type": "http",
      "url": "https://mcp.pianam.cn/train-mcp/mcp"
    }
  }
}
```

> Clients that do not accept `"type": "http"` (some Cherry Studio / older
> Cline versions) accept the same entry with just `"url"`.

## 🧰 Tools

| Tool | Parameters | Returns |
|---|---|---|
| `query_train_tickets(from_city, to_city, date="")` | `from_city` / `to_city`: Chinese city or station names, e.g. `"青岛"`, `"北京南"`.<br>`date`: `YYYY-MM-DD`; empty defaults to **tomorrow**. 12306's booking window is usually 15 days. | Train list with train number, departure/arrival stations & times, duration, and remaining seats per class (business/first/second class, soft/hard sleeper, hard seat, no-seat). |
| `search_station(keyword)` | `keyword`: e.g. `"北京"`. | Fuzzy-matches station names (returns up to 30: 北京, 北京南, 北京西, 北京北 …) when you are not sure which station to use. |

## 📡 Data sources, caching & limits

- Data comes from **12306's own public query endpoints** (`kyfw.12306.cn/otn/leftTicket/...`) — read-only queries only; **this server cannot book tickets**, please buy via the official 12306 app/website.
- Station code table cached locally for 7 days; ticket queries cached for **300 seconds**.
- No API key, no login required.
- The hosted endpoint is rate-limited to **200 requests / minute / IP**.

## 🐢 Self-hosting

```bash
git clone https://github.com/boy-373/12306-train-mcp.git
cd 12306-train-mcp
pip install -r requirements.txt
python train_mcp_server.py
# the server listens on 127.0.0.1:8003 by default; override with:
#   MCP_HOST=0.0.0.0 MCP_PORT=9000 python train_mcp_server.py
#   MCP_ALLOWED_HOSTS="your-domain.com,127.0.0.1:*"
#   MCP_ALLOWED_ORIGINS="https://your-domain.com"
```

Then point your MCP client at `http://127.0.0.1:8003/mcp`.
No API keys or accounts are ever required.


- `train_stations.json` — bundled 12306 station name → telegraph-code table (auto-refreshed from 12306 every 7 days).

## 🗂️ Files

- `train_mcp_server.py` — the MCP server (FastMCP, Streamable HTTP transport).
- `rate_limit.py` — lightweight per-IP sliding-window rate-limit middleware (200 req/min default).
- `requirements.txt` — `mcp`, `uvicorn`, `starlette`.
- `server.json` — official MCP Registry manifest (remote server entry, ready to publish with `mcp-publisher`).
- `smithery.yaml` / `glama.json` — directory listing metadata.

---

## 🧯 Parameter guide & common errors (read this if a call fails)

**`query_train_tickets(from_city, to_city, date="")`**

| Parameter | What to pass | Notes |
|---|---|---|
| `from_city` / `to_city` | **Chinese station or city names**, e.g. `"青岛"`, `"北京"`, `"上海虹桥"` | A city name works when the city has one main station; for multi-station cities use the exact station name. Not sure? Call `search_station("北京")` first — it returns 北京/北京南/北京西/北京北… |
| `date` | `YYYY-MM-DD`, e.g. `"2026-09-20"` | Optional — **defaults to tomorrow** when empty. 12306's pre-sale window is **15 days** (dates further out return an error or empty results). |

**Why you may get an HTTP 400 / error result:**

1. **Bad date format** — must be exactly `YYYY-MM-DD` (`2026/09/20`, `2026年9月20日`, `Sep 20` all fail).
2. **Station name not found** — typo, pinyin (`"qingdao"`), or a vague nickname the code table doesn't contain. Fix: call `search_station` with a keyword and copy the exact name.
3. **City-level name for a multi-station city** — e.g. `"北京"` usually resolves to 北京 station, but if you want a specific station pass `"北京南"` / `"北京西"` explicitly.
4. **Date outside the 15-day pre-sale window** — 12306 has not released those tickets yet.

**Correct call examples:**

```
query_train_tickets(from_city="青岛", to_city="北京", date="2026-09-20")
query_train_tickets(from_city="北京南", to_city="上海虹桥")        # date omitted -> tomorrow
search_station(keyword="上海")                                   # -> 上海/上海南/上海虹桥/上海西…
```

A successful response returns `车次总数` plus a `车次` list (train number, departure/arrival station & time, duration, and remaining seats per class). An unrecognized station returns `{"error": "出发站「…」无法识别，可用 search_station 工具查车站名"}` — simply re-call with the exact name.

---

## 🧯 参数说明与常见错误（调用失败先看这里）

**`query_train_tickets(from_city, to_city, date="")` 参数说明**

| 参数 | 填什么 | 注意 |
|---|---|---|
| `from_city` / `to_city` | **中文车站名或城市名**，如 `"青岛"`、`"北京"`、`"上海虹桥"` | 城市只有一个主车站时填城市名即可；多车站城市建议填具体车站名。不确定时先调 `search_station("北京")`，会返回 北京/北京南/北京西/北京北 等准确站名 |
| `date` | `YYYY-MM-DD` 格式，如 `"2026-09-20"` | 可留空，**留空默认查明天**；12306 预售期通常为 **15 天**，超出预售期的日期会查询失败或无结果 |

**返回 400 / 错误结果的常见原因：**

1. **日期格式错误**：必须严格为 `YYYY-MM-DD`，`2026/09/20`、`2026年9月20日`、`Sep 20` 等写法都会失败；
2. **站名不存在**：错别字、拼音（如 `"qingdao"`）、或码表中没有的俗称都会无法识别。解决方法：先用 `search_station` 关键词搜索，复制返回的准确站名；
3. **多车站城市用了城市通称**：如 `"北京"` 一般能匹配到「北京」站，但要去特定车站请明确传 `"北京南"`、`"北京西"` 等；
4. **日期超出 15 天预售期**：12306 尚未放票，查询会返回失败提示。

**正确调用示例：**

```
query_train_tickets(from_city="青岛", to_city="北京", date="2026-09-20")
query_train_tickets(from_city="北京南", to_city="上海虹桥")        # date 留空 -> 默认明天
search_station(keyword="上海")                                   # 返回 上海/上海南/上海虹桥/上海西…
```

调用成功会返回 `车次总数` 和 `车次` 列表（车次号、出发/到达站与时间、历时、各席别余票）；站名无法识别时返回 `{"error": "出发站「…」无法识别，可用 search_station 工具查车站名"}`，换成准确站名重试即可。

## 🇨🇳 中文使用说明

**一句话**：直接用中文站名查 12306 余票，数据来自 12306 官方公开查询接口，纯只读。

**在线直连地址（免费、无需 Key、开箱即用）**：`https://mcp.pianam.cn/train-mcp/mcp`

在 MCP 客户端（Claude Desktop / Cursor / Cherry Studio / Cline 等）的配置里加入：

```json
{
  "mcpServers": {
    "12306-train": {
      "type": "http",
      "url": "https://mcp.pianam.cn/train-mcp/mcp"
    }
  }
}
```

**工具**：

- `query_train_tickets(from_city, to_city, date)`：查余票。出发/到达站直接给中文城市或车站名（如「青岛」「北京南」），日期格式 `YYYY-MM-DD`，留空默认明天；返回车次、出发到达时间、历时及商务座/一等座/二等座/软卧/硬卧/硬座/无座等余票。
- `search_station(keyword)`：不确定城市有哪些车站时模糊搜索站名（如「北京」返回 北京/北京南/北京西/北京北 等）。
- 仅查票，不能购票；12306 预售期通常 15 天。

**服务特性**：数据源全部为公开接口、无需注册/付费；服务端内存缓存、失败自动降级/切换备用通道；单 IP 限流 200 次/分钟。

**本地部署**：

```bash
git clone https://github.com/boy-373/12306-train-mcp.git
cd 12306-train-mcp
pip install -r requirements.txt
python train_mcp_server.py
# 默认监听 127.0.0.1:8003，可用环境变量 MCP_HOST / MCP_PORT / MCP_ALLOWED_HOSTS / MCP_ALLOWED_ORIGINS 覆盖
```

## 📄 License

[MIT](LICENSE) © 2026 boy-373

## Install via Smithery

One-click install for [Smithery](https://smithery.ai)-supported clients (Claude Desktop, Cursor, etc.):

[![Smithery](https://smithery.ai/badge/1561852680/12306-train-mcp)](https://smithery.ai/servers/1561852680/12306-train-mcp)

Or run:

```bash
npx -y @smithery/cli install 1561852680/12306-train-mcp --client claude
```

---

## 🔌 Use with Any AI Client — One-Click MCP Gateway

We host a free **MCP aggregation gateway**: your AI assistant (Cherry Studio, Claude Desktop, Cursor, Cline — any MCP client) discovers and uses MCP tools through a single URL:

```
https://mcp.pianam.cn/ai/mcp
```

Add it once, then talk in plain language — the AI automatically **searches → inspects → calls** the right MCP for you.

- 🔍 Search across **22,000+** indexed MCP servers (Chinese & English)
- ⚡ **50+ live hosted MCPs** callable directly out of the box (weather, exchange rates, hot trends, IP geo, train tickets…)
- 📦 GitHub-based MCPs: search finds them with links to install locally
- ✅ Servers health-checked weekly — alive ones ranked first
- 🆓 Free to use, no key required

**📖 3-step setup guide / 中文接入教程**: https://mcp.pianam.cn/ai-gateway
