#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
토스 Ads BDR — 아웃리치 발굴 리포트 배치 수집기 (GitHub Actions 일일 크론).
공용 로직은 collector_lib.py. 여기선 발굴 큐(실제 기업)를 돌려 data/*.json 생성.
"""
import os, re, sys, json
from datetime import datetime

from collector_lib import KST, CATALOG, collect_company

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

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
    "무신사":          {"i": "패션 커머스", "hp": "https://corp.musinsa.com",        "t": "2030"},
    "올리브영":        {"i": "뷰티 커머스", "hp": "https://corp.oliveyoung.com",     "t": "2030 여성"},
    "컬리":            {"i": "식품 커머스", "hp": "https://www.kurly.com",           "t": "3040"},
    "오늘의집":        {"i": "리빙 커머스", "hp": "https://www.bucketplace.com",     "t": "2030 주거"},
    "당근마켓":        {"i": "중고·로컬 커머스", "hp": "https://about.daangn.com",    "t": "2040 생활"},
    "왓챠":            {"i": "OTT 콘텐츠",  "hp": "https://watcha.team",             "t": "2030"},
    "29CM":            {"i": "패션·라이프 커머스", "hp": "https://www.29cm.co.kr",   "t": "2030"},
    "야놀자":          {"i": "여행·숙박",   "hp": "https://yanolja.co",              "t": "2040 액티브"},
}


def build():
    now = datetime.now(KST)
    month, date_s = now.month, now.strftime("%Y-%m-%d")
    companies = []
    for name, meta in COMPANY.items():
        print(f"→ {name} ({meta['i']})")
        c = collect_company(name, meta["i"], meta.get("hp", ""), meta.get("t", ""), month)
        print(f"    시그널 {[k for k in c['sigs'] if k not in ('fit',)]}  / 뉴스 {len(c['news'])} / 채용 {len(c['jobs'])}")
        companies.append(c)
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
    from datetime import timedelta
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
    live = sum(1 for c in report["companies"] if any(k != "fit" for k in c["sigs"]))
    print(f"\n✓ 완료 — {len(report['companies'])}개 기업 / 시그널 감지 {live}개 / {report['date']}")


if __name__ == "__main__":
    main()
