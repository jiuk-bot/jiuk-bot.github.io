#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
토스 Ads BDR 발굴 — 공용 수집 로직.
배치(collect_report.py, 일일 크론)와 실시간 API(api/collect.py, 온디맨드)가 공유.
전부 clean HTTP(키·로그인 불필요): Google News RSS + 원티드/사람인/잡코리아 + 계절성 규칙.
"""
import re, sys, html, json, urllib.parse, urllib.request
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from xml.etree import ElementTree as ET

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")
KST = timezone(timedelta(hours=9))

# ───────── 시그널 카탈로그 (프론트가 이 정의를 그대로 사용) ─────────
CATALOG = {
    "invest":   {"w": 22, "l": "투자 유치",       "src": "벤처투자 뉴스",            "hook": "최근 투자 유치 축하 + 성장 단계 마케팅 확장 각도"},
    "season":   {"w": 22, "l": "성수기 진입",      "src": "시즌 캘린더",              "hook": "업종 성수기 타이밍에 맞춘 집행 확대 제안"},
    "admarket": {"w": 16, "l": "광고·캠페인 집행",  "src": "보도자료",                 "hook": "광고·캠페인 확대 시점 — 신규 매체(토스) 테스트 제안"},
    "launch":   {"w": 14, "l": "신제품 출시",      "src": "보도자료",                 "hook": "신제품 출시 타이밍에 맞춘 토스 노출 제안"},
    "hiring":   {"w": 12, "l": "마케팅 채용중",    "src": "원티드·사람인·잡코리아",    "hook": "마케팅 조직 확대 시점 — 신규 매체 테스트 제안"},
    "fit":      {"w": 8,  "l": "타깃 핏",          "src": "업종 분석",                "hook": "토스 2030·대중 유저 도달 강점을 업종 핏으로 어필"},
}

NEWS_KW = {
    "invest":   ["투자", "유치", "시리즈", "펀딩", "라운드", "증자", "조달", "인수", "지분"],
    "launch":   ["출시", "신제품", "론칭", "런칭", "오픈", "선보", "신규 서비스", "리뉴얼", "공개"],
    "admarket": ["캠페인", "광고", "앰버서더", "모델 발탁", "프로모션", "콜라보", "협찬", "브랜드 필름", "마케팅"],
}

MKW = ["마케팅", "마케터", "퍼포먼스", "그로스", "growth", "crm", "광고",
       "브랜딩", "브랜드 마케", "바이럴", "그로스해킹", "ad sales", "애드세일",
       "캠페인", "media buy", "미디어 플래"]

SEASON_RULE = [
    ("패션",  {3, 4, 5, 9, 10, 11}),
    ("뷰티",  {3, 4, 5, 9, 10, 11}),
    ("리빙",  {3, 4, 9, 10}),
    ("식품",  {1, 5, 6, 11, 12}),
    ("숙박",  {1, 7, 8, 12}),
    ("플라워", {2, 3, 5, 12}),
    ("여행",  {1, 7, 8, 12}),
    ("독서",  {1, 9, 11, 12}),
    ("웹툰",  {1, 2, 7, 8}),
    ("콘텐츠", {1, 2, 7, 8}),
    ("중고",  {2, 3, 12}),
    ("교육",  {1, 2, 3, 9}),
    ("샐러드", {1, 4, 5, 6}),
    ("핀테크", {1, 7, 8, 12}),
]


def http_get(url, timeout=12):
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": UA,
            "Accept-Language": "ko-KR,ko;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml,application/json;q=0.9,*/*;q=0.8",
        })
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read().decode("utf-8", "replace")
    except Exception as e:
        print(f"    ! GET 실패 {url[:70]} — {e}", file=sys.stderr)
        return None


def enc(s):
    return urllib.parse.quote(s)


def clean(t):
    return html.unescape(re.sub(r"\s+", " ", t or "")).strip()


def fmt_date(pub):
    try:
        return parsedate_to_datetime(pub).astimezone(KST).strftime("%Y-%m-%d")
    except Exception:
        return ""


# ───────── 뉴스 ─────────
def fetch_news(name):
    url = f"https://news.google.com/rss/search?q=%22{enc(name)}%22%20when:45d&hl=ko&gl=KR&ceid=KR:ko"
    xml = http_get(url)
    out = []
    if not xml:
        return out
    try:
        root = ET.fromstring(xml)
    except ET.ParseError:
        return out
    for item in root.iter("item"):
        title = clean(item.findtext("title"))
        link = clean(item.findtext("link"))
        date = fmt_date(item.findtext("pubDate"))
        src = clean(item.findtext("source")) or (title.rsplit(" - ", 1)[-1] if " - " in title else "")
        while src and title.endswith(" - " + src):
            title = title[: -(len(src) + 3)].rstrip()
        if not title or name not in title:
            continue
        out.append({"t": title, "u": link, "d": date, "s": src})
        if len(out) >= 30:
            break
    return out


def classify_news(items):
    hit = {"invest": [], "launch": [], "admarket": []}
    for it in items:
        t = it["t"]
        for sig, kws in NEWS_KW.items():
            if any(k in t for k in kws) and len(hit[sig]) < 4:
                hit[sig].append(it)
    return {k: v for k, v in hit.items() if v}


# ───────── 마케팅 채용 ─────────
def is_marketing(title):
    low = title.lower()
    return any(k in low for k in MKW)


def fetch_wanted(name):
    url = (f"https://www.wanted.co.kr/api/v4/jobs?country=kr&query={enc(name)}"
           f"&job_sort=job.latest_order&locations=all&years=-1&limit=20")
    raw = http_get(url)
    out = []
    if not raw:
        return out
    try:
        data = json.loads(raw).get("data", [])
    except Exception:
        return out
    for j in data:
        pos = clean(j.get("position", ""))
        comp = clean((j.get("company") or {}).get("name", ""))
        if name not in comp and name not in pos:
            continue
        if not is_marketing(pos):
            continue
        out.append({"t": f"{pos} · {comp}", "u": f"https://www.wanted.co.kr/wd/{j.get('id')}"})
        if len(out) >= 3:
            break
    return out


def fetch_saramin(name):
    url = f"https://www.saramin.co.kr/zf_user/search?searchword={enc(name + ' 마케팅')}"
    h = http_get(url)
    out = []
    if not h:
        return out
    for m in re.finditer(r'<a[^>]+href="(/zf_user/jobs/relay/view[^"]+)"[^>]*title="([^"]+)"', h):
        href, title = m.group(1), clean(m.group(2))
        if title and is_marketing(title):
            out.append({"t": title, "u": "https://www.saramin.co.kr" + html.unescape(href)})
        if len(out) >= 3:
            break
    return out


def fetch_jobkorea(name):
    url = f"https://www.jobkorea.co.kr/Search/?stext={enc(name)}"
    h = http_get(url)
    out = []
    if not h:
        return out
    for m in re.finditer(r'<a[^>]+href="(/Recruit/GI_Read/[^"]+)"[^>]*title="([^"]+)"', h):
        href, title = m.group(1), clean(m.group(2))
        if title and is_marketing(title):
            out.append({"t": title, "u": "https://www.jobkorea.co.kr" + html.unescape(href)})
        if len(out) >= 3:
            break
    return out


def fetch_hiring(name):
    jobs = []
    for fn in (fetch_wanted, fetch_saramin, fetch_jobkorea):
        try:
            jobs += fn(name)
        except Exception as e:
            print(f"    ! 채용 소스 실패 {fn.__name__} — {e}", file=sys.stderr)
    seen, uniq = set(), []
    for j in jobs:
        key = j["t"][:40]
        if key not in seen:
            seen.add(key)
            uniq.append(j)
    return uniq[:5]


def season_on(industry, month):
    for key, months in SEASON_RULE:
        if key in (industry or ""):
            return month in months
    return False


# ───────── 한 기업 수집 (배치·실시간 공용) ─────────
def collect_company(name, industry=None, hp="", target="", month=None):
    name = (name or "").strip()
    if month is None:
        month = datetime.now(KST).month
    signals = {}

    news = fetch_news(name)
    for sig, srcs in classify_news(news).items():
        signals[sig] = srcs

    if industry and season_on(industry, month):
        signals["season"] = [{"t": f"{industry} 성수기 구간 (월 {month})", "u": "", "d": "", "s": "시즌 캘린더"}]

    jobs = fetch_hiring(name)
    if jobs:
        signals["hiring"] = jobs

    if industry:
        signals["fit"] = [{"t": f"{industry} · 토스 {target or '2040 대중'} 타깃 핏", "u": "", "d": "", "s": "업종 분석"}]

    keys = list(signals.keys())
    score = min(100, sum(CATALOG[k]["w"] for k in keys if k in CATALOG))
    return {
        "n": name,
        "i": industry or "조회 기업 (업종 미등록)",
        "hp": hp,
        "target": target,
        "sigs": keys,
        "score": score,
        "sources": signals,
        "news": news[:8],
        "jobs": jobs,
    }
