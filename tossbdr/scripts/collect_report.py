#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
토스 Ads BDR — 아웃리치 발굴 리포트 자동 수집기
실제 공개 소스에서 비즈니스 시그널을 수집·스코어링 → tossbdr/data/*.json 생성.

수집 소스 (전부 clean HTTP, 키·로그인 불필요):
  - 뉴스        : Google News RSS   → 투자 유치 / 신제품 출시 / 광고·캠페인 집행
  - 계절성      : 업종별 성수기 캘린더 규칙
  - 마케팅 채용 : 원티드 API + 사람인 HTML + 잡코리아 HTML → '마케팅 직무' 공고 감지
  - 타깃 핏     : 업종 기반 (상수)

GitHub Actions 일일 크론으로 실행 → data/latest.json + data/report-YYYY-MM-DD.json 커밋.
각 시그널에는 '근거(실제 기사/공고 링크)'가 함께 저장되어 추정이 아닌 팩트로 검증 가능.
"""
import os, re, sys, json, html, urllib.parse, urllib.request
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

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.normpath(os.path.join(HERE, "..", "data"))

# ───────── 발굴 후보 (실제 기업) ─────────
COMPANY = {
    "에이블리":        {"i": "패션 커머스", "hp": "https://ably.team",              "t": "2030 여성"},
    "지그재그":        {"i": "패션 커머스", "hp": "https://kakaostyle.com",          "t": "2030 여성"},
    "꾸까":            {"i": "플라워 구독", "hp": "https://kukka.kr",                "t": "2030 여성"},
    "마이리얼트립":    {"i": "여행",        "hp": "https://www.myrealtrip.com",      "t": "2040 액티브"},
    "트래블월렛":      {"i": "여행·핀테크", "hp": "https://www.travel-wallet.com",   "t": "2040 경제활동"},
    "밀리의서재":      {"i": "독서 구독",   "hp": "https://corp.millie.co.kr",       "t": "2030 생활"},
    "리디":            {"i": "웹툰·콘텐츠", "hp": "https://ridicorp.com",            "t": "1030"},
    "번개장터":        {"i": "중고 커머스", "hp": "https://bgzt.co.kr",              "t": "2030 가성비"},
    "스파르타코딩클럽": {"i": "성인 교육",   "hp": "https://spartaclub.kr",           "t": "2030 직장인"},
    "프레시코드":      {"i": "샐러드 구독", "hp": "https://www.freshcode.me",        "t": "2030 건강"},
    "클래스101":       {"i": "교육",        "hp": "https://101.inc",                 "t": "2030 직장인·학습자"},
    "야나두":          {"i": "교육",        "hp": "https://www.yanadoo.co.kr",       "t": "2030 직장인·학습자"},
}

# ───────── 시그널 카탈로그 (프론트가 이 정의를 그대로 사용) ─────────
CATALOG = {
    "invest":   {"w": 22, "l": "투자 유치",       "src": "벤처투자 뉴스",            "hook": "최근 투자 유치 축하 + 성장 단계 마케팅 확장 각도"},
    "season":   {"w": 22, "l": "성수기 진입",      "src": "시즌 캘린더",              "hook": "업종 성수기 타이밍에 맞춘 집행 확대 제안"},
    "admarket": {"w": 16, "l": "광고·캠페인 집행",  "src": "보도자료",                 "hook": "광고·캠페인 확대 시점 — 신규 매체(토스) 테스트 제안"},
    "launch":   {"w": 14, "l": "신제품 출시",      "src": "보도자료",                 "hook": "신제품 출시 타이밍에 맞춘 토스 노출 제안"},
    "hiring":   {"w": 12, "l": "마케팅 채용중",    "src": "원티드·사람인·잡코리아",    "hook": "마케팅 조직 확대 시점 — 신규 매체 테스트 제안"},
    "fit":      {"w": 8,  "l": "타깃 핏",          "src": "업종 분석",                "hook": "토스 2030·대중 유저 도달 강점을 업종 핏으로 어필"},
}

# 뉴스 제목 분류 키워드
NEWS_KW = {
    "invest":   ["투자", "유치", "시리즈", "펀딩", "라운드", "증자", "조달", "인수", "지분"],
    "launch":   ["출시", "신제품", "론칭", "런칭", "오픈", "선보", "신규 서비스", "리뉴얼", "공개"],
    "admarket": ["캠페인", "광고", "앰버서더", "모델 발탁", "프로모션", "콜라보", "협찬", "브랜드 필름", "마케팅"],
}

# 마케팅 직무 필터 키워드 (채용 공고 제목) — 비마케팅 직무 오탐 방지로 타이트하게
MKW = ["마케팅", "마케터", "퍼포먼스", "그로스", "growth", "crm", "광고",
       "브랜딩", "브랜드 마케", "바이럴", "그로스해킹", "ad sales", "애드세일",
       "캠페인", "media buy", "미디어 플래"]

# 업종별 성수기(월) 규칙 — 업종 문자열 부분매칭, 첫 매칭 우선
SEASON_RULE = [
    ("패션",  {3, 4, 5, 9, 10, 11}),
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


# ───────── 뉴스 (Google News RSS) ─────────
def fetch_news(name):
    """최근 기사 목록 — 제목/링크/발행일/매체. 제목 끝의 ' - 매체명'은 분리."""
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
        while src and title.endswith(" - " + src):   # 끝의 ' - 매체명'(중복 포함) 제거
            title = title[: -(len(src) + 3)].rstrip()
        if not title or name not in title:
            continue
        out.append({"t": title, "u": link, "d": date, "s": src})
        if len(out) >= 30:
            break
    return out


def classify_news(items):
    """뉴스 제목을 시그널별로 분류 → {sig: [ {t,u}, ... ]}"""
    hit = {"invest": [], "launch": [], "admarket": []}
    for it in items:
        t = it["t"]
        for sig, kws in NEWS_KW.items():
            if any(k in t for k in kws):
                if len(hit[sig]) < 4:
                    hit[sig].append(it)
    return {k: v for k, v in hit.items() if v}


# ───────── 마케팅 채용 (원티드 / 사람인 / 잡코리아) ─────────
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
        jid = j.get("id")
        out.append({"t": f"{pos} · {comp}", "u": f"https://www.wanted.co.kr/wd/{jid}"})
        if len(out) >= 3:
            break
    return out


def fetch_saramin(name):
    url = f"https://www.saramin.co.kr/zf_user/search?searchword={enc(name + ' 마케팅')}"
    h = http_get(url)
    out = []
    if not h:
        return out
    # 공고 제목 앵커: <a href="/zf_user/jobs/relay/view?...idx=...">제목</a> (title 속성 포함)
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
    # 중복 제목 제거
    seen, uniq = set(), []
    for j in jobs:
        key = j["t"][:40]
        if key not in seen:
            seen.add(key)
            uniq.append(j)
    return uniq[:5]


def season_on(industry, month):
    for key, months in SEASON_RULE:
        if key in industry:
            return month in months
    return False


# ───────── 메인 ─────────
def build():
    now = datetime.now(KST)
    month = now.month
    date_s = now.strftime("%Y-%m-%d")
    companies = []

    for name, meta in COMPANY.items():
        ind = meta["i"]
        print(f"→ {name} ({ind})")
        signals = {}

        news = fetch_news(name)
        for sig, srcs in classify_news(news).items():
            signals[sig] = srcs
        print(f"    뉴스 {len(news)}건 → {[k for k in signals]}")

        if season_on(ind, month):
            signals["season"] = [{"t": f"{ind} 성수기 구간 (월 {month})", "u": "", "d": "", "s": "시즌 캘린더"}]

        jobs = fetch_hiring(name)
        if jobs:
            signals["hiring"] = jobs
            print(f"    마케팅 채용 {len(jobs)}건")

        signals["fit"] = [{"t": f"{ind} · 토스 {meta.get('t','2040 대중')} 타깃 핏", "u": "", "d": "", "s": "업종 분석"}]

        keys = list(signals.keys())
        score = min(100, sum(CATALOG[k]["w"] for k in keys if k in CATALOG))
        companies.append({
            "n": name, "i": ind,
            "hp": meta.get("hp", ""),
            "target": meta.get("t", "2040 대중"),
            "sigs": keys,
            "score": score,
            "sources": signals,
            "news": news[:8],   # 기업조회 탭 '최신 뉴스'용 (발행일·링크 포함)
            "jobs": jobs,
        })

    companies.sort(key=lambda c: (c["score"], len(c["sources"])), reverse=True)

    return {
        "generated": now.strftime("%Y-%m-%d %H:%M KST"),
        "date": date_s,
        "mode": "live",
        "sources_used": ["Google News RSS", "시즌 캘린더", "원티드", "사람인", "잡코리아"],
        "catalog": CATALOG,
        "companies": companies,
    }


def prune_old(keep_days=30):
    cutoff = datetime.now(KST) - timedelta(days=keep_days)
    for fn in os.listdir(DATA_DIR):
        m = re.match(r"report-(\d{4}-\d{2}-\d{2})\.json$", fn)
        if not m:
            continue
        try:
            d = datetime.strptime(m.group(1), "%Y-%m-%d").replace(tzinfo=KST)
            if d < cutoff:
                os.remove(os.path.join(DATA_DIR, fn))
        except Exception:
            pass


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    report = build()
    for fn in ("latest.json", f"report-{report['date']}.json"):
        with open(os.path.join(DATA_DIR, fn), "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
    prune_old()
    live = sum(1 for c in report["companies"] if any(k not in ("fit",) for k in c["sigs"]))
    print(f"\n✓ 완료 — {len(report['companies'])}개 기업 / 시그널 감지 {live}개 / {report['date']}")


if __name__ == "__main__":
    main()
