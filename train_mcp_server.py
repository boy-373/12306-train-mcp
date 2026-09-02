# -*- coding: utf-8 -*-
"""
12306 火车票查询 · 远程 MCP Server
----------------------------------
部署在 mcp.pianam.cn，任何支持 MCP 协议的 AI 客户端
(Claude Desktop / Cursor / Cline 等) 填入 URL 即可查火车票余票。
数据源：12306 官方公开查询接口（只读，仅查票，不涉及购票）。

Author: liufuyang  2026-08-30
"""
import json
import os
import re
import ssl
import time
import gzip
import datetime
import urllib.request
from pathlib import Path

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings



BASE_DIR = Path(__file__).parent
STATION_FILE = BASE_DIR / "train_stations.json"

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
_SSL_CTX = ssl.create_default_context()
_SSL_CTX.check_hostname = False
_SSL_CTX.verify_mode = ssl.CERT_NONE

# 12306 余票字段索引（公开接口固定位置）
SEAT_FIELDS = [
    (32, "商务/特等座"),
    (31, "一等座"),
    (30, "二等座"),
    (23, "软卧"),
    (24, "软座"),
    (28, "硬卧"),
    (29, "硬座"),
    (26, "无座"),
]

_stations = None
_stations_ts = 0.0
_query_cache = {}


def _http_get(url, cookies=None, timeout=15):
    req = urllib.request.Request(url)
    req.add_header("User-Agent", UA)
    req.add_header("Accept", "*/*")
    req.add_header("Accept-Language", "zh-CN,zh;q=0.9")
    req.add_header("Referer", "https://kyfw.12306.cn/otn/leftTicket/init")
    if cookies:
        req.add_header("Cookie", cookies)
    resp = urllib.request.urlopen(req, timeout=timeout, context=_SSL_CTX)
    data = resp.read()
    if resp.headers.get("Content-Encoding") == "gzip":
        data = gzip.decompress(data)
    return data.decode("utf-8", errors="ignore"), resp.headers.get("Set-Cookie", "")


def load_stations(force=False):
    """加载车站码表：本地缓存7天，失效后从12306拉取。"""
    global _stations, _stations_ts
    now = time.time()
    if not force and _stations and now - _stations_ts < 86400 * 7:
        return _stations
    if not force and STATION_FILE.exists() and now - STATION_FILE.stat().st_mtime < 86400 * 7:
        _stations = json.loads(STATION_FILE.read_text(encoding="utf-8"))
        _stations_ts = now
        return _stations
    js, _ = _http_get(
        "https://kyfw.12306.cn/otn/resources/js/framework/station_name.js"
    )
    names = {}
    for seg in js.split("@")[1:]:
        p = seg.split("|")
        if len(p) >= 3:
            names[p[1]] = p[2]  # 中文名 -> 电报码
    STATION_FILE.write_text(
        json.dumps(names, ensure_ascii=False), encoding="utf-8"
    )
    _stations, _stations_ts = names, now
    return names


def resolve_station(name):
    """中文城市/车站名 -> (电报码, 规范车站名)。"""
    stations = load_stations()
    name = name.strip()
    if name in stations:
        return stations[name], name
    exact = [k for k in stations if k == name]
    if exact:
        return stations[exact[0]], exact[0]
    cands = [k for k in stations if k.startswith(name)]
    if cands:
        return stations[cands[0]], cands[0]
    return None, name


def _seat_value(fields, idx):
    """解析余票字段：'有'->有票, 数字->N张, 空/加密候补串->None。"""
    v = fields[idx] if idx < len(fields) else ""
    if v in ("", "*", "--"):
        return None
    if v == "有":
        return "有票"
    if v.isdigit():
        return f"{v}张"
    return None


def query_tickets_raw(from_city, to_city, date):
    cache_key = (from_city, to_city, date)
    cached = _query_cache.get(cache_key)
    if cached and time.time() - cached[0] < 300:
        return cached[1]

    fcode, fname = resolve_station(from_city)
    tcode, tname = resolve_station(to_city)
    if not fcode:
        return {"error": f"出发站「{from_city}」无法识别，可用 search_station 工具查车站名"}
    if not tcode:
        return {"error": f"到达站「{to_city}」无法识别，可用 search_station 工具查车站名"}

    # 初始化会话拿 cookie
    _, set_cookie = _http_get("https://kyfw.12306.cn/otn/leftTicket/init")
    cookies = []
    for part in set_cookie.split(","):
        m = re.match(r"\s*([^=;]+=[^;]+)", part)
        if m and "JSESSIONID" in m.group(1):
            cookies.append(m.group(1).strip())
    cookie_str = "; ".join(cookies)

    stations = load_stations()
    code2name = {v: k for k, v in stations.items()}

    data = None
    for ep in ("queryG", "queryZ", "queryA"):
        url = (
            f"https://kyfw.12306.cn/otn/leftTicket/{ep}"
            f"?leftTicketDTO.train_date={date}"
            f"&leftTicketDTO.from_station={fcode}"
            f"&leftTicketDTO.to_station={tcode}"
            f"&purpose_codes=ADULT"
        )
        try:
            txt, _ = _http_get(url, cookies=cookie_str)
            d = json.loads(txt)
            if d.get("status") and d.get("data", {}).get("result") is not None:
                data = d
                break
        except Exception:
            continue

    if data is None:
        return {"error": "12306查询失败，可能是网络波动或查询日期超出预售期（通常为15天内）"}

    trains = []
    for r in data["data"]["result"]:
        f = r.split("|")
        seats = {label: _seat_value(f, idx) for idx, label in SEAT_FIELDS}
        trains.append({
            "车次": f[3],
            "出发站": code2name.get(f[6], f[6]),
            "到达站": code2name.get(f[7], f[7]),
            "出发时间": f[8],
            "到达时间": f[9],
            "历时": f[10],
            "余票": {k: v for k, v in seats.items() if v is not None},
        })

    out = {
        "日期": date,
        "出发": fname,
        "到达": tname,
        "车次总数": len(trains),
        "说明": "余票信息来自12306实时查询；空席别表示该车次无此座位类型；购票请前往12306官方App",
        "车次": trains,
    }
    _query_cache[cache_key] = (time.time(), out)
    return out


mcp = FastMCP(
    "12306-train-query",
    host=os.environ.get("MCP_HOST", "127.0.0.1"),
    port=int(os.environ.get("MCP_PORT", "8003")),
    transport_security=TransportSecuritySettings(
        allowed_hosts=(os.environ.get("MCP_ALLOWED_HOSTS") or "127.0.0.1:*,localhost:*,[::1]:*,mcp.pianam.cn,mcp.pianam.cn:*").split(","),
        allowed_origins=(os.environ.get("MCP_ALLOWED_ORIGINS") or "https://mcp.pianam.cn,https://mcp.pianam.cn:*,http://127.0.0.1:*,http://localhost:*").split(","),
    ),
)


@mcp.tool()
def query_train_tickets(from_city: str, to_city: str, date: str = "") -> dict:
    """查询中国大陆12306火车票余票信息。

    参数:
        from_city: 出发城市或车站中文名，例如 "青岛"、"北京南"
        to_city: 到达城市或车站中文名，例如 "北京"、"上海虹桥"
        date: 出发日期，格式 YYYY-MM-DD，例如 "2026-09-01"；留空默认明天
    返回:
        车次列表，含车次号、出发/到达站、出发/到达时间、历时、各席别余票。
    注意: 仅支持查票，不能购票；12306预售期通常为15天。
    """
    if not date:
        date = (datetime.date.today() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    try:
        datetime.datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        return {"error": "日期格式应为 YYYY-MM-DD，例如 2026-09-01"}
    try:
        return query_tickets_raw(from_city, to_city, date)
    except Exception as e:
        return {"error": f"查询失败: {type(e).__name__}: {e}"}


@mcp.tool()
def search_station(keyword: str) -> dict:
    """按关键词搜索12306车站名称，返回匹配的车站中文名列表。
    当不确定城市有哪些车站时使用，例如搜 "北京" 返回 北京/北京南/北京西/北京北 等。
    """
    try:
        stations = load_stations()
        matches = [k for k in stations if keyword in k][:30]
        return {"关键词": keyword, "匹配车站": matches}
    except Exception as e:
        return {"error": f"搜索失败: {e}"}


if __name__ == "__main__":
    # 挂限流中间件：必须用 uvicorn 直接跑自定义 app——mcp.run() 内部会另建 app 实例，外挂中间件会被丢弃
    import sys
    import uvicorn
    sys.path.insert(0, str(BASE_DIR))
    from rate_limit import RateLimitMiddleware
    _app = mcp.streamable_http_app()
    _app.add_middleware(RateLimitMiddleware, limit_per_minute=60)
    uvicorn.run(_app, host=mcp.settings.host, port=mcp.settings.port, log_level=mcp.settings.log_level.lower())
