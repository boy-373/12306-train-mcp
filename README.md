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
- The hosted endpoint is rate-limited to **60 requests / minute / IP**.

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
- `rate_limit.py` — lightweight per-IP sliding-window rate-limit middleware (60 req/min default).
- `requirements.txt` — `mcp`, `uvicorn`, `starlette`.
- `server.json` — official MCP Registry manifest (remote server entry, ready to publish with `mcp-publisher`).
- `smithery.yaml` / `glama.json` — directory listing metadata.

---

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

**服务特性**：数据源全部为公开接口、无需注册/付费；服务端内存缓存、失败自动降级/切换备用通道；单 IP 限流 60 次/分钟。

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
